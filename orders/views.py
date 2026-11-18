import logging

import stripe
from django.conf import settings
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from accounts.models import Address
from cart.services import get_cart, quote_for, sync_count
from core.ratelimit import ratelimit

from .forms import CheckoutForm, TrackOrderForm
from .invoices import InvoiceUnavailable, get_or_build_pdf
from .models import Order, StripeEvent
from .services import CheckoutError, create_checkout_session, create_order, expire_order, fulfil_order

logger = logging.getLogger(__name__)
PENDING_ORDER_KEY = "pending_order_id"


def _initial(request):
    if not request.user.is_authenticated:
        return {}
    user = request.user
    initial = {"email": user.email, "first_name": user.first_name, "last_name": user.last_name, "phone": user.phone}
    chosen = request.GET.get("adresse", "")
    address = (user.addresses.filter(pk=chosen).first() if chosen.isdigit() else None) or user.addresses.first()
    if address:
        initial.update({k: getattr(address, k) for k in ("first_name", "last_name", "line1", "line2",
                                                         "postal_code", "city")})
        initial["phone"] = address.phone or user.phone
    return initial


@require_http_methods(["GET", "POST"])
@ratelimit("checkout", "10/m")
def checkout(request):
    quote = quote_for(request)
    if quote.is_empty:
        messages.info(request, "Votre panier est vide.")
        return redirect("cart:detail")
    addresses = list(request.user.addresses.all()) if request.user.is_authenticated else []
    form = CheckoutForm(request.POST or None, initial=_initial(request))
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        customer = request.user if request.user.is_authenticated else None
        try:
            order = create_order(quote, data, customer=customer)
            if customer and data.get("save_address"):
                Address.objects.get_or_create(
                    customer=customer, line1=data["line1"], postal_code=data["postal_code"],
                    defaults={"first_name": data["first_name"], "last_name": data["last_name"],
                              "line2": data.get("line2", ""), "city": data["city"], "phone": data.get("phone", ""),
                              "is_default": not addresses},
                )
            session = create_checkout_session(order)
        except CheckoutError as exc:
            messages.error(request, str(exc))
        except stripe.StripeError:
            logger.exception("Erreur Stripe à la création de la session")
            messages.error(request, "Le service de paiement est momentanément indisponible. Merci de réessayer.")
        else:
            request.session[PENDING_ORDER_KEY] = order.pk
            response = HttpResponseRedirect(session.url)
            response.status_code = 303  # POST → GET vers la page de paiement Stripe
            return response
    return render(request, "orders/checkout.html", {
        "form": form, "quote": quote, "addresses": addresses,
        "address_api_url": settings.ADDRESS_API_URL,
    })


@require_GET
def success(request):
    session_id = request.GET.get("session_id", "")
    order = Order.objects.filter(stripe_session_id=session_id).first() if session_id else None
    # La page « merci » n'est visible que par le navigateur qui a créé la commande (ou son titulaire).
    if order is None or (request.session.get(PENDING_ORDER_KEY) != order.pk
                         and not (request.user.is_authenticated and order.customer_id == request.user.pk)):
        raise Http404
    cart = get_cart(request)
    if cart is not None:
        cart.delete()
    sync_count(request, 0)
    request.session.pop(PENDING_ORDER_KEY, None)
    return render(request, "orders/success.html", {"order": order})


@csrf_exempt  # appel serveur-à-serveur : authentifié par la signature Stripe, pas par CSRF
@require_POST
def stripe_webhook(request):
    payload = request.body
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET).to_dict()
    except (ValueError, stripe.SignatureVerificationError):
        logger.warning("Webhook Stripe rejeté : signature invalide")
        return HttpResponseBadRequest("Signature invalide")

    try:
        with transaction.atomic():
            # Idempotence : un même événement (rejoué par Stripe) n'est traité qu'une fois.
            # L'enregistrement est annulé si le traitement échoue → Stripe pourra le rejouer (HTTP 500).
            try:
                with transaction.atomic():
                    StripeEvent.objects.create(event_id=event["id"], type=event["type"])
            except IntegrityError:
                return HttpResponse("Déjà traité", status=200)
            _handle_event(event)
    except Order.DoesNotExist:
        logger.error("Webhook %s : commande introuvable", event["id"])
        return HttpResponse("Commande inconnue", status=200)
    return HttpResponse("OK", status=200)


def _handle_event(event):
    obj = event["data"]["object"]
    etype = event["type"]
    if etype not in {"checkout.session.completed", "checkout.session.async_payment_succeeded",
                     "checkout.session.expired", "checkout.session.async_payment_failed"}:
        return
    order_id = (obj.get("metadata") or {}).get("order_id") or obj.get("client_reference_id")
    if not order_id:
        return
    if etype in ("checkout.session.expired", "checkout.session.async_payment_failed"):
        expire_order(int(order_id))
        return
    if obj.get("payment_status") != "paid":  # paiement différé : on attend async_payment_succeeded
        return
    fulfil_order(int(order_id), payment_intent=obj.get("payment_intent") or "",
                 amount_total=obj.get("amount_total"))


def _get_order_for(request, number, token):
    order = get_object_or_404(Order.objects.prefetch_related("items"), number=number)
    if str(order.access_token) != str(token) and not (
        request.user.is_authenticated and (order.customer_id == request.user.pk or request.user.is_staff)
    ):
        raise Http404
    return order


@require_GET
def detail(request, number, token):
    order = _get_order_for(request, number, token)
    return render(request, "orders/detail.html", {"order": order, "items": order.items.all()})


@require_GET
def invoice_pdf(request, number, token):
    order = _get_order_for(request, number, token)
    invoice = getattr(order, "invoice", None)
    if invoice is None or not order.is_paid:
        raise Http404
    try:
        data = get_or_build_pdf(invoice)
    except InvoiceUnavailable:
        return HttpResponse("Génération des factures momentanément indisponible.", status=503)
    response = HttpResponse(data, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="facture-{invoice.number}.pdf"'
    return response


@require_http_methods(["GET", "POST"])
@ratelimit("track", "10/h")
def track(request):
    form = TrackOrderForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        order = Order.objects.filter(number__iexact=form.cleaned_data["number"].strip(),
                                     email__iexact=form.cleaned_data["email"]).first()
        if order:
            return redirect(order.get_absolute_url())
        form.add_error(None, "Aucune commande ne correspond à ce numéro et cet e-mail.")
    return render(request, "orders/track.html", {"form": form})

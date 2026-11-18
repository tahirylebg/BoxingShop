"""Cycle de vie des commandes : création, paiement Stripe, confirmation (stock), annulation."""
import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.urls import reverse
from django.utils import timezone

from cart.models import PromoCode
from catalog.models import Product, Variant
from core.models import ShippingSettings

from . import emails
from .models import Invoice, Order, OrderItem

logger = logging.getLogger(__name__)


class CheckoutError(Exception):
    pass


def cents(amount):
    return int((Decimal(amount) * 100).quantize(Decimal("1")))


def create_order(quote, data, customer=None):
    """Crée une commande « en attente » à partir du devis du panier (aucun stock décrémenté ici)."""
    if quote.is_empty:
        raise CheckoutError("Votre panier est vide.")
    for line in quote.lines:
        variant = line.variant
        if not variant.is_active or line.quantity > variant.stock:
            raise CheckoutError(
                f"« {variant.product.name} ({variant.label}) » n'est plus disponible en quantité suffisante "
                f"({variant.stock} en stock). Merci d'ajuster votre panier."
            )
    with transaction.atomic():
        order = Order.objects.create(
            customer=customer, email=data["email"].lower(), first_name=data["first_name"],
            last_name=data["last_name"], line1=data["line1"], line2=data.get("line2", ""),
            postal_code=data["postal_code"], city=data["city"], phone=data.get("phone", ""),
            subtotal=quote.subtotal, club_discount=quote.club_discount, promo_discount=quote.promo_discount,
            promo_code=quote.promo_code, shipping_cost=quote.shipping, total=quote.total,
        )
        OrderItem.objects.bulk_create([
            OrderItem(order=order, variant=line.variant, product_name=line.variant.product.name,
                      variant_label=line.variant.label, sku=line.variant.sku, unit_price=line.unit_price,
                      quantity=line.quantity, line_total=line.total)
            for line in quote.lines
        ])
    return order


def create_checkout_session(order):
    """Crée la session Stripe Checkout (carte + Apple Pay / Google Pay selon le Dashboard)."""
    if not settings.STRIPE_SECRET_KEY:
        raise CheckoutError("Le paiement en ligne n'est pas configuré (clé Stripe manquante).")
    stripe.api_key = settings.STRIPE_SECRET_KEY
    items = list(order.items.all())
    params = {
        "mode": "payment",
        "locale": "fr",
        "customer_email": order.email,
        "client_reference_id": str(order.pk),
        "metadata": {"order_id": str(order.pk), "order_number": order.number},
        "payment_intent_data": {"metadata": {"order_id": str(order.pk), "order_number": order.number}},
        "line_items": [
            {
                "quantity": item.quantity,
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "unit_amount": cents(item.unit_price),
                    "product_data": {"name": f"{item.product_name} — {item.variant_label}".strip(" —"),
                                     "metadata": {"sku": item.sku}},
                },
            }
            for item in items
        ],
        "shipping_options": [{
            "shipping_rate_data": {
                "type": "fixed_amount",
                "display_name": "Livraison offerte" if not order.shipping_cost else ShippingSettings.load().carrier_label,
                "fixed_amount": {"amount": cents(order.shipping_cost), "currency": settings.STRIPE_CURRENCY},
            }
        }],
        "success_url": f"{settings.SITE_URL}{reverse('orders:success')}?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{settings.SITE_URL}{reverse('cart:detail')}?paiement=annule",
    }
    if order.discount_total > 0:
        coupon = stripe.Coupon.create(
            amount_off=cents(order.discount_total), currency=settings.STRIPE_CURRENCY, duration="once",
            max_redemptions=1, name=f"Remises {order.number}"[:40],
        )
        params["discounts"] = [{"coupon": coupon.id}]
    session = stripe.checkout.Session.create(**params, idempotency_key=f"checkout-{order.number}")
    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id"])
    return session


def fulfil_order(order_id, *, payment_intent="", amount_total=None):
    """Confirme une commande payée. Appelé par le webhook Stripe, dans une transaction.

    Verrouille la commande puis les déclinaisons (ordre de clé stable → pas d'interblocage),
    vérifie le stock, le décrémente, incrémente les ventes et l'usage du code promo.
    Retourne la commande ; ne fait rien si elle n'est plus « en attente » (idempotence).
    """
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status != Order.Status.PENDING:
            return order
        if amount_total is not None and amount_total != cents(order.total):
            logger.error("Montant Stripe %s ≠ commande %s (%s)", amount_total, order.number, order.total)
            transaction.on_commit(lambda: emails.notify_admin_payment_mismatch(order, amount_total))
            return order

        order.stripe_payment_intent = payment_intent or order.stripe_payment_intent
        items = list(order.items.all())
        variant_ids = sorted({i.variant_id for i in items if i.variant_id})
        locked = {v.pk: v for v in Variant.objects.select_for_update().filter(pk__in=variant_ids).order_by("pk")}

        shortages = [i for i in items if i.variant_id not in locked or locked[i.variant_id].stock < i.quantity]
        if shortages:
            order.status = Order.Status.CANCELLED
            order.stock_issue = True
            order.save(update_fields=["status", "stock_issue", "stripe_payment_intent"])
            transaction.on_commit(lambda: refund_and_notify(order))
            return order

        for item in items:
            Variant.objects.filter(pk=item.variant_id).update(stock=F("stock") - item.quantity)
            Product.objects.filter(pk=locked[item.variant_id].product_id).update(
                sales_count=F("sales_count") + item.quantity)
        if order.promo_code:
            PromoCode.objects.filter(code=order.promo_code).update(times_used=F("times_used") + 1)

        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "paid_at", "stripe_payment_intent"])
        Invoice.objects.create(order=order)
        transaction.on_commit(lambda: emails.send_order_confirmation(order))
        transaction.on_commit(lambda: emails.notify_admin_low_stock(variant_ids))
    return order


def refund_and_notify(order):
    if order.stripe_payment_intent and settings.STRIPE_SECRET_KEY:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            stripe.Refund.create(payment_intent=order.stripe_payment_intent,
                                 idempotency_key=f"refund-{order.number}")
        except stripe.StripeError:
            logger.exception("Remboursement impossible pour %s", order.number)
    emails.send_order_cancelled_stock(order)


def expire_order(order_id):
    Order.objects.filter(pk=order_id, status=Order.Status.PENDING).update(status=Order.Status.CANCELLED)

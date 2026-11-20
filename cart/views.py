from urllib.parse import urlencode

from django.contrib import messages
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from catalog.models import Product

from .models import PromoCode
from .services import CartError, add_item, get_cart, quote_for, set_quantity


def _is_fetch(request):
    return request.headers.get("X-Requested-With") == "fetch"


def _suggestions(quote, limit=3):
    """« Complétez votre équipement » : meilleures ventes en stock, d'abord dans les rayons absents du panier."""
    in_cart = {line.variant.product_id for line in quote.lines}
    cart_categories = {line.variant.product.category_id for line in quote.lines}
    candidates = (Product.objects.active().exclude(pk__in=in_cart)
                  .filter(variants__is_active=True, variants__stock__gt=0).distinct()
                  .select_related("category").prefetch_related("images").order_by("-sales_count")[:24])
    ranked = sorted(candidates, key=lambda p: p.category_id in cart_categories)
    out = []
    for product in ranked[:limit]:
        variant = product.variants.filter(is_active=True, stock__gt=0).order_by("price", "pk").first()
        images = list(product.images.all())
        image = next((i for i in images if variant and i.color == variant.color), images[0] if images else None)
        out.append({"product": product, "variant": variant, "image": image})
    return out


def _drawer_context(quote):
    from catalog.models import Category

    tops = list(Category.objects.filter(parent__isnull=True).order_by("position", "pk")) if quote.is_empty else []
    gloves = next((c for c in tops if c.slug == "gants"), None)
    return {
        "quote": quote,
        "suggestions": [] if quote.is_empty else _suggestions(quote),
        "gloves_url": gloves.get_absolute_url() if gloves else "",
        "empty_categories": [c for c in tops if c.slug != "gants"][:3],
    }


def _drawer_html(request, quote):
    return render_to_string("cart/_drawer.html", _drawer_context(quote), request=request)


def _respond(request, *, ok=True, message="", fallback="cart:detail"):
    """Réponse JSON (tiroir JS) ou redirection classique (sans JS)."""
    if _is_fetch(request):
        quote = quote_for(request)
        return JsonResponse({"ok": ok, "message": message, "count": quote.item_count,
                             "html": _drawer_html(request, quote)}, status=200 if ok else 400)
    if ok:
        quote_for(request)  # met à jour le compteur du header en session
    if message:
        (messages.success if ok else messages.error)(request, message)
    nxt = request.POST.get("next", "")
    if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}, require_https=request.is_secure()):
        return redirect(nxt)  # ex. code promo saisi depuis le récapitulatif du checkout
    return redirect(fallback)


@require_GET
def detail(request):
    quote = quote_for(request)
    return render(request, "cart/detail.html", {"quote": quote, "cart": get_cart(request)})


@require_GET
def drawer(request):
    return render(request, "cart/_drawer.html", _drawer_context(quote_for(request)))


def _resolve_variant(product, data):
    variants = list(product.variants.filter(is_active=True))
    color, weight, size = data.get("couleur"), data.get("poids"), data.get("taille")
    if color or weight or size:
        for v in variants:
            if ((not color or v.color == color) and (not weight or str(v.weight_oz) == weight)
                    and (not size or v.size == size)):
                return v
        return None
    variant_id = data.get("variant")
    return next((v for v in variants if str(v.pk) == variant_id), None)


@require_POST
def add(request):
    product = get_object_or_404(Product.objects.active(), pk=request.POST.get("product"))
    variant = _resolve_variant(product, request.POST)

    if request.POST.get("action") == "preview":  # repli sans JS : afficher la déclinaison choisie
        params = {k: request.POST[k] for k in ("couleur", "poids", "taille") if request.POST.get(k)}
        if variant:
            params = {"sku": variant.sku}
        return redirect(f"{product.get_absolute_url()}?{urlencode(params)}")

    if variant is None:
        return _respond(request, ok=False, message="Cette combinaison n'existe pas : choisissez une autre option.",
                        fallback=product.get_absolute_url())
    try:
        quantity = max(1, min(int(request.POST.get("quantity", 1)), 99))
    except ValueError:
        quantity = 1
    try:
        add_item(get_cart(request, create=True), variant, quantity)
    except CartError as exc:
        return _respond(request, ok=False, message=str(exc), fallback=f"{product.get_absolute_url()}?sku={variant.sku}")
    return _respond(request, message=f"{product.name} ({variant.label}) ajouté au panier.")


@require_POST
def update(request, item_id):
    cart = get_cart(request)
    if cart is None:
        return _respond(request, ok=False, message="Votre panier est vide.")
    try:
        quantity = int(request.POST.get("quantity", 0))
    except ValueError:
        return _respond(request, ok=False, message="Quantité invalide.")
    if request.POST.get("action") == "remove":
        quantity = 0
    try:
        set_quantity(cart, item_id, quantity)
    except CartError as exc:
        return _respond(request, ok=False, message=str(exc))
    return _respond(request, message="Panier mis à jour.")


@require_POST
def apply_promo(request):
    cart = get_cart(request)
    if cart is None:
        return _respond(request, ok=False, message="Votre panier est vide.")
    if request.POST.get("action") == "remove":
        cart.promo_code = None
        cart.save(update_fields=["promo_code"])
        return _respond(request, message="Code promo retiré.")
    code = (request.POST.get("code") or "").strip().upper()
    promo = PromoCode.objects.filter(code=code).first()
    if promo is None:
        return _respond(request, ok=False, message="Code promo inconnu.")
    cart.promo_code = promo
    cart.save(update_fields=["promo_code"])
    quote = quote_for(request, cart)
    if quote.promo_error:
        cart.promo_code = None
        cart.save(update_fields=["promo_code"])
        return _respond(request, ok=False, message=quote.promo_error)
    return _respond(request, message=f"Code {promo.code} appliqué.")

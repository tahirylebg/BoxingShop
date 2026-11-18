"""Accès au panier (session ou compte) et opérations de modification."""
from django.db import transaction

from accounts.models import ClubPriceTier
from core.models import ShippingSettings

from .models import Cart, CartItem
from .pricing import Line, compute_quote

SESSION_KEY = "cart_id"
MAX_QTY = 99


class CartError(Exception):
    pass


def get_cart(request, create=False):
    user = request.user if request.user.is_authenticated else None
    cart = None
    if user:
        cart = Cart.objects.filter(customer=user).order_by("-updated_at").first()
    else:
        cart_id = request.session.get(SESSION_KEY)
        if cart_id:
            cart = Cart.objects.filter(pk=cart_id, customer__isnull=True).first()
    if cart is None and create:
        if not request.session.session_key:
            request.session.save()
        cart = Cart.objects.create(customer=user, session_key=request.session.session_key or "")
        if not user:
            request.session[SESSION_KEY] = cart.pk
    return cart


def cart_lines(cart):
    if cart is None:
        return []
    items = cart.items.select_related("variant__product__discipline", "variant__product__category").prefetch_related(
        "variant__product__images"
    )
    return [Line(variant=i.variant, quantity=i.quantity, item_id=i.pk) for i in items]


def quote_for(request, cart=None):
    cart = cart if cart is not None else get_cart(request)
    lines = cart_lines(cart)
    quote = compute_quote(
        lines,
        shipping_settings=ShippingSettings.load(),
        customer=request.user if request.user.is_authenticated else None,
        promo=cart.promo_code if cart else None,
        tiers=list(ClubPriceTier.objects.all()),
    )
    sync_count(request, quote.item_count)
    return quote


def sync_count(request, count):
    request.session["cart_count"] = count


def add_item(cart, variant, quantity):
    if quantity < 1:
        raise CartError("Quantité invalide.")
    if not variant.is_active or not variant.product.is_active:
        raise CartError("Ce produit n'est plus disponible.")
    with transaction.atomic():
        item, created = CartItem.objects.select_for_update().get_or_create(
            cart=cart, variant=variant, defaults={"quantity": 0}
        )
        new_qty = item.quantity + quantity
        if new_qty > variant.stock:
            available = max(0, variant.stock - item.quantity)
            if available == 0:
                raise CartError("Cette déclinaison est épuisée." if variant.stock == 0
                                else "Vous avez déjà tout le stock disponible dans votre panier.")
            raise CartError(f"Stock insuffisant : {available} pièce(s) disponible(s) en plus.")
        item.quantity = min(new_qty, MAX_QTY)
        item.save()
        cart.save(update_fields=["updated_at"])
    return item


def set_quantity(cart, item_id, quantity):
    item = cart.items.select_related("variant").filter(pk=item_id).first()
    if item is None:
        raise CartError("Article introuvable dans le panier.")
    if quantity <= 0:
        item.delete()
        return None
    if quantity > item.variant.stock:
        raise CartError(f"Stock insuffisant : {item.variant.stock} pièce(s) disponible(s).")
    item.quantity = min(quantity, MAX_QTY)
    item.save(update_fields=["quantity"])
    return item


def merge_carts(source, target):
    """Fusionne le panier invité dans le panier du compte à la connexion."""
    for item in source.items.select_related("variant"):
        existing = target.items.filter(variant=item.variant).first()
        if existing:
            existing.quantity = min(existing.quantity + item.quantity, item.variant.stock, MAX_QTY)
            existing.save(update_fields=["quantity"])
        else:
            item.cart = target
            item.save(update_fields=["cart"])
    if source.promo_code_id and not target.promo_code_id:
        target.promo_code_id = source.promo_code_id
        target.save(update_fields=["promo_code"])
    source.delete()

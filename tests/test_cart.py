"""Panier : ajout, limites de stock, code promo, fusion à la connexion."""
from decimal import Decimal

import pytest

from cart.models import Cart
from cart.services import CartError, add_item, set_quantity

pytestmark = pytest.mark.django_db

AJAX = {"HTTP_X_REQUESTED_WITH": "fetch", "HTTP_ACCEPT": "application/json"}


def test_add_item_respects_stock(variant):
    cart = Cart.objects.create()
    add_item(cart, variant, 3)
    with pytest.raises(CartError, match="2 pièce"):
        add_item(cart, variant, 3)
    add_item(cart, variant, 2)
    assert cart.items.get().quantity == 5
    with pytest.raises(CartError):
        add_item(cart, variant, 1)


def test_inactive_variant_cannot_be_added(variant):
    variant.is_active = False
    variant.save()
    with pytest.raises(CartError):
        add_item(Cart.objects.create(), variant, 1)


def test_set_quantity_zero_removes_line(variant):
    cart = Cart.objects.create()
    item = add_item(cart, variant, 2)
    assert set_quantity(cart, item.pk, 0) is None
    assert not cart.items.exists()


def test_add_view_and_cart_page(client, product, variant, shipping):
    r = client.post("/panier/ajouter/", {"product": product.pk, "variant": variant.pk, "quantity": 2})
    assert r.status_code == 302
    assert client.session["cart_count"] == 2
    page = client.get("/panier/")
    assert page.status_code == 200
    assert page.context["quote"].subtotal == Decimal("80.00")
    assert page.context["quote"].shipping == Decimal("6.90")


def test_add_view_selects_variant_by_options(client, product, variant, variant_b):
    client.post("/panier/ajouter/", {"product": product.pk, "couleur": "Noir", "poids": "12"})
    assert Cart.objects.get().items.get().variant == variant_b


def test_add_view_json_reports_stock_error(client, product, variant):
    r = client.post("/panier/ajouter/", {"product": product.pk, "variant": variant.pk, "quantity": 9}, **AJAX)
    assert r.status_code in (200, 400, 409)
    assert r.json()["ok"] is False


def test_promo_code_flow(client, product, variant, promo, shipping):
    client.post("/panier/ajouter/", {"product": product.pk, "variant": variant.pk, "quantity": 1})
    client.post("/panier/code-promo/", {"code": "ring10"})
    assert Cart.objects.get().promo_code is None  # 40 € < minimum 50 €
    client.post("/panier/ajouter/", {"product": product.pk, "variant": variant.pk, "quantity": 1})
    client.post("/panier/code-promo/", {"code": "ring10"})
    quote = client.get("/panier/").context["quote"]
    assert quote.promo_discount == Decimal("8.00")
    client.post("/panier/code-promo/", {"code": "INCONNU"})
    assert Cart.objects.get().promo_code.code == "RING10"


def test_club_discount_applied_in_cart(client, club_customer, tiers, product, variant_b, shipping):
    client.force_login(club_customer)
    client.post("/panier/ajouter/", {"product": product.pk, "variant": variant_b.pk, "quantity": 5})
    quote = client.get("/panier/").context["quote"]
    assert quote.club_percent == 10
    assert quote.club_discount == Decimal("12.50")


def test_guest_cart_merged_on_login(client, customer, product, variant):
    client.post("/panier/ajouter/", {"product": product.pk, "variant": variant.pk, "quantity": 2})
    client.post("/compte/connexion/", {"username": customer.email, "password": "Uppercut-2026!"})
    cart = Cart.objects.get(customer=customer)
    assert cart.items.get().quantity == 2

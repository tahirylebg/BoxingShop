"""Calcul du panier : livraison, code promo, tarifs club (fonction pure, sans base pour l'essentiel)."""
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.utils import timezone

from cart.models import PromoCode
from cart.pricing import Line, compute_quote

D = Decimal
SHIPPING = SimpleNamespace(flat_rate=D("6.90"), free_shipping_threshold=D("90.00"))
CLUB = SimpleNamespace(is_club=True)
TIERS = [SimpleNamespace(min_quantity=5, discount_percent=D("10")),
         SimpleNamespace(min_quantity=10, discount_percent=D("15")),
         SimpleNamespace(min_quantity=20, discount_percent=D("20"))]


def lines(*specs):
    return [Line(variant=SimpleNamespace(price=D(price)), quantity=qty) for price, qty in specs]


def promo(**kw):
    defaults = {"code": "RING10", "value": D("10"), "min_subtotal": D("50"), "discount_type": "percent",
                "valid_from": timezone.now() - timedelta(days=1)}
    return PromoCode(**{**defaults, **kw})


class TestShipping:
    def test_flat_rate_below_threshold(self):
        q = compute_quote(lines(("40.00", 2)), shipping_settings=SHIPPING)
        assert q.subtotal == D("80.00")
        assert q.shipping == D("6.90")
        assert q.total == D("86.90")
        assert q.remaining_for_free_shipping == D("10.00")

    def test_free_at_exact_threshold(self):
        q = compute_quote(lines(("45.00", 2)), shipping_settings=SHIPPING)
        assert q.shipping == D("0.00")
        assert q.total == D("90.00")

    def test_threshold_applies_after_discounts(self):
        # 100 € - 10 % promo = 90 € → toujours offert ; 95 € - 10 % = 85,50 € → payant
        assert compute_quote(lines(("100.00", 1)), shipping_settings=SHIPPING, promo=promo()).shipping == 0
        q = compute_quote(lines(("95.00", 1)), shipping_settings=SHIPPING, promo=promo())
        assert q.merchandise_total == D("85.50")
        assert q.shipping == D("6.90")

    def test_empty_cart_has_no_shipping(self):
        q = compute_quote([], shipping_settings=SHIPPING)
        assert q.is_empty and q.total == 0


class TestPromo:
    def test_percent(self):
        q = compute_quote(lines(("60.00", 1)), shipping_settings=SHIPPING, promo=promo())
        assert q.promo_code == "RING10"
        assert q.promo_discount == D("6.00")

    def test_fixed_amount_never_exceeds_cart(self):
        q = compute_quote(lines(("20.00", 1)), shipping_settings=SHIPPING,
                          promo=promo(discount_type="fixed", value=D("50"), min_subtotal=D("0")))
        assert q.promo_discount == D("20.00")
        assert q.merchandise_total == 0

    def test_minimum_not_reached(self):
        q = compute_quote(lines(("30.00", 1)), shipping_settings=SHIPPING, promo=promo())
        assert q.promo_discount == 0
        assert "au moins 50" in q.promo_error

    @pytest.mark.parametrize("kwargs, message", [
        ({"is_active": False}, "plus actif"),
        ({"valid_until": timezone.now() - timedelta(hours=1)}, "pas valable"),
        ({"valid_from": timezone.now() + timedelta(days=1)}, "pas valable"),
        ({"max_uses": 3, "times_used": 3}, "nombre maximal"),
    ])
    def test_invalid_codes(self, kwargs, message):
        q = compute_quote(lines(("80.00", 1)), shipping_settings=SHIPPING, promo=promo(**kwargs))
        assert q.promo_discount == 0
        assert message in q.promo_error


class TestClubPricing:
    def test_regular_customer_gets_no_tier(self):
        q = compute_quote(lines(("10.00", 12)), shipping_settings=SHIPPING,
                          customer=SimpleNamespace(is_club=False), tiers=TIERS)
        assert q.club_discount == 0

    @pytest.mark.parametrize("qty, percent", [(4, 0), (5, 10), (9, 10), (10, 15), (25, 20)])
    def test_tiers_by_total_quantity(self, qty, percent):
        q = compute_quote(lines(("10.00", qty)), shipping_settings=SHIPPING, customer=CLUB, tiers=TIERS)
        assert q.club_percent == percent
        assert q.club_discount == (D("10.00") * qty * percent / 100).quantize(D("0.01"))

    def test_quantity_counts_across_lines(self):
        q = compute_quote(lines(("10.00", 3), ("20.00", 2)), shipping_settings=SHIPPING, customer=CLUB, tiers=TIERS)
        assert q.item_count == 5 and q.club_percent == 10

    def test_promo_applies_after_club_discount(self):
        q = compute_quote(lines(("20.00", 5)), shipping_settings=SHIPPING, customer=CLUB, tiers=TIERS,
                          promo=promo())
        assert q.subtotal == D("100.00")
        assert q.club_discount == D("10.00")
        assert q.promo_discount == D("9.00")  # 10 % de 90 €
        assert q.merchandise_total == D("81.00")
        assert q.shipping == D("6.90")
        assert q.total == D("87.90")

    def test_unvalidated_club_request_has_no_discount(self, customer, tiers):
        customer.club_status = "pending"
        q = compute_quote(lines(("10.00", 10)), shipping_settings=SHIPPING, customer=customer, tiers=tiers)
        assert q.club_discount == 0

    def test_approved_club_customer_from_db(self, club_customer, tiers):
        q = compute_quote(lines(("10.00", 10)), shipping_settings=SHIPPING, customer=club_customer, tiers=tiers)
        assert q.club_percent == 15

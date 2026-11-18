"""Calcul du panier : sous-total, remise club, code promo, frais de port, total.

Ordre d'application (documenté dans les CGV) :
  1. sous-total articles (prix TTC × quantités)
  2. remise Club/Coach selon la quantité totale (comptes validés uniquement)
  3. code promo, appliqué sur le montant après remise club
  4. livraison offerte si le montant des articles après remises atteint le seuil, sinon forfait
"""
from dataclasses import dataclass, field
from decimal import Decimal

CENT = Decimal("0.01")


def q(amount):
    return Decimal(amount).quantize(CENT)


@dataclass
class Line:
    variant: object
    quantity: int
    item_id: int | None = None

    @property
    def unit_price(self):
        return self.variant.price

    @property
    def total(self):
        return q(self.variant.price * self.quantity)


@dataclass
class Quote:
    lines: list = field(default_factory=list)
    item_count: int = 0
    subtotal: Decimal = Decimal("0.00")
    club_percent: Decimal = Decimal("0")
    club_discount: Decimal = Decimal("0.00")
    promo_code: str = ""
    promo_discount: Decimal = Decimal("0.00")
    promo_error: str = ""
    merchandise_total: Decimal = Decimal("0.00")
    shipping: Decimal = Decimal("0.00")
    free_shipping_threshold: Decimal = Decimal("0.00")
    remaining_for_free_shipping: Decimal = Decimal("0.00")
    total: Decimal = Decimal("0.00")

    @property
    def discount_total(self):
        return self.club_discount + self.promo_discount

    @property
    def free_shipping_progress(self):
        if not self.free_shipping_threshold:
            return 100
        return min(100, int(self.merchandise_total * 100 / self.free_shipping_threshold))

    @property
    def is_empty(self):
        return not self.lines


def club_percent_for(customer, item_count, tiers):
    if not customer or not getattr(customer, "is_club", False):
        return Decimal("0")
    eligible = [t for t in tiers if item_count >= t.min_quantity]
    return max((t.discount_percent for t in eligible), default=Decimal("0"))


def compute_quote(lines, *, shipping_settings, customer=None, promo=None, tiers=(), now=None):
    quote = Quote(lines=list(lines))
    quote.item_count = sum(line.quantity for line in quote.lines)
    quote.subtotal = q(sum((line.total for line in quote.lines), Decimal("0")))
    quote.free_shipping_threshold = shipping_settings.free_shipping_threshold

    quote.club_percent = club_percent_for(customer, quote.item_count, tiers)
    quote.club_discount = q(quote.subtotal * quote.club_percent / 100)
    after_club = quote.subtotal - quote.club_discount

    if promo is not None:
        valid, error = promo.check_validity(after_club, now=now)
        if valid:
            quote.promo_code = promo.code
            quote.promo_discount = promo.discount_for(after_club)
        else:
            quote.promo_error = error

    quote.merchandise_total = q(after_club - quote.promo_discount)
    if quote.is_empty or quote.merchandise_total >= shipping_settings.free_shipping_threshold:
        quote.shipping = Decimal("0.00")
    else:
        quote.shipping = q(shipping_settings.flat_rate)
    quote.remaining_for_free_shipping = max(
        Decimal("0.00"), q(shipping_settings.free_shipping_threshold - quote.merchandise_total)
    )
    quote.total = q(quote.merchandise_total + quote.shipping)
    return quote

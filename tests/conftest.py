import hashlib
import hmac
import json
import time
from decimal import Decimal

import pytest
from django.core.cache import cache

from accounts.models import ClubPriceTier, Customer
from cart.models import PromoCode
from catalog.models import Category, Discipline, Product, Variant
from core.models import ShippingSettings


@pytest.fixture(autouse=True)
def _isolation(settings, tmp_path):
    """Cache (rate-limit, catalogue) et médias propres à chaque test."""
    settings.MEDIA_ROOT = tmp_path / "media"
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def shipping(db):
    s = ShippingSettings.load()
    s.flat_rate = Decimal("6.90")
    s.free_shipping_threshold = Decimal("90.00")
    s.save()
    return s


@pytest.fixture
def product(db):
    discipline = Discipline.objects.create(name="Boxe anglaise", slug="boxe-anglaise")
    category = Category.objects.create(name="Gants", slug="gants")
    return Product.objects.create(
        name="Gant test", slug="gant-test", discipline=discipline, category=category,
        short_description="Gant de test", description="Description.", material="cuir", level="sparring",
    )


@pytest.fixture
def variant(product):
    return Variant.objects.create(product=product, sku="BS-TEST-10", color="Noir", weight_oz=10,
                                  price=Decimal("40.00"), stock=5, low_stock_threshold=2)


@pytest.fixture
def variant_b(product):
    return Variant.objects.create(product=product, sku="BS-TEST-12", color="Noir", weight_oz=12,
                                  price=Decimal("25.00"), stock=10, low_stock_threshold=2)


@pytest.fixture
def promo(db):
    return PromoCode.objects.create(code="ring10", value=Decimal("10"), min_subtotal=Decimal("50"))


@pytest.fixture
def tiers(db):
    return [ClubPriceTier.objects.create(min_quantity=5, discount_percent=Decimal("10")),
            ClubPriceTier.objects.create(min_quantity=10, discount_percent=Decimal("15"))]


@pytest.fixture
def customer(db):
    return Customer.objects.create_user("client@example.com", "Uppercut-2026!", first_name="Sam")


@pytest.fixture
def club_customer(db):
    user = Customer.objects.create_user("club@example.com", "Uppercut-2026!", club_name="Team")
    user.approve_club()
    user.save()
    return user


@pytest.fixture
def staff(db):
    return Customer.objects.create_superuser("admin@example.com", "Admin-2026!")


CHECKOUT_DATA = {"email": "guest@example.com", "first_name": "Alex", "last_name": "Martin",
                 "line1": "1 rue du Ring", "postal_code": "75011", "city": "Paris", "accept_terms": "on"}


def stripe_signature(payload: bytes, secret: str, timestamp=None) -> str:
    """Reproduit l'en-tête Stripe-Signature (HMAC-SHA256 de « t.payload »)."""
    timestamp = timestamp or int(time.time())
    signed = f"{timestamp}.".encode() + payload
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


@pytest.fixture
def post_webhook(client, settings):
    def _post(event: dict, *, secret=None):
        payload = json.dumps(event).encode()
        signature = stripe_signature(payload, secret or settings.STRIPE_WEBHOOK_SECRET)
        return client.post("/commande/webhook/stripe/", data=payload, content_type="application/json",
                           HTTP_STRIPE_SIGNATURE=signature)
    return _post


def checkout_event(order, *, event_id="evt_test_1", etype="checkout.session.completed", amount=None,
                   payment_status="paid"):
    from orders.services import cents
    return {
        "id": event_id, "object": "event", "type": etype, "api_version": "2025-01-27.acacia",
        "data": {"object": {
            "id": order.stripe_session_id or "cs_test_1", "object": "checkout.session",
            "client_reference_id": str(order.pk), "metadata": {"order_id": str(order.pk)},
            "payment_status": payment_status, "payment_intent": "pi_test_1",
            "amount_total": cents(order.total) if amount is None else amount,
        }},
    }

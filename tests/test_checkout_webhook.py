"""Tunnel de commande et webhook Stripe simulé : signature, idempotence, décrément du stock."""
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

import pytest
from django.core import mail

from catalog.models import Variant
from orders.models import Invoice, Order, StripeEvent
from orders.services import fulfil_order

from .conftest import CHECKOUT_DATA, checkout_event

pytestmark = pytest.mark.django_db(transaction=True)  # select_for_update + on_commit réels


@pytest.fixture
def stripe_mock():
    session = SimpleNamespace(id="cs_test_1", url="https://checkout.stripe.com/c/pay/cs_test_1")
    with mock.patch("stripe.checkout.Session.create", return_value=session) as create, \
            mock.patch("stripe.Coupon.create", return_value=SimpleNamespace(id="coupon_1")) as coupon:
        yield SimpleNamespace(create=create, coupon=coupon)


@pytest.fixture
def pending_order(client, product, variant, variant_b, shipping, stripe_mock):
    client.post("/panier/ajouter/", {"product": product.pk, "variant": variant.pk, "quantity": 2})
    client.post("/panier/ajouter/", {"product": product.pk, "variant": variant_b.pk, "quantity": 1})
    r = client.post("/commande/", CHECKOUT_DATA)
    assert r.status_code == 303 and r["Location"].startswith("https://checkout.stripe.com/")
    return Order.objects.get()


def test_checkout_creates_pending_order_without_touching_stock(pending_order, variant, stripe_mock):
    assert pending_order.status == Order.Status.PENDING
    assert pending_order.total == Decimal("105.00")  # 80 + 25, livraison offerte
    variant.refresh_from_db()
    assert variant.stock == 5
    params = stripe_mock.create.call_args.kwargs
    assert params["mode"] == "payment"
    assert params["metadata"]["order_id"] == str(pending_order.pk)
    assert sum(li["price_data"]["unit_amount"] * li["quantity"] for li in params["line_items"]) == 10500
    assert params["idempotency_key"] == f"checkout-{pending_order.number}"


def test_checkout_with_promo_creates_stripe_coupon(client, product, variant, promo, shipping, stripe_mock):
    client.post("/panier/ajouter/", {"product": product.pk, "variant": variant.pk, "quantity": 2})
    client.post("/panier/code-promo/", {"code": "RING10"})
    client.post("/commande/", CHECKOUT_DATA)
    assert stripe_mock.coupon.call_args.kwargs["amount_off"] == 800
    assert stripe_mock.create.call_args.kwargs["discounts"] == [{"coupon": "coupon_1"}]


def test_checkout_requires_terms(client, product, variant, shipping, stripe_mock):
    client.post("/panier/ajouter/", {"product": product.pk, "variant": variant.pk, "quantity": 1})
    r = client.post("/commande/", {**CHECKOUT_DATA, "accept_terms": ""})
    assert r.status_code == 200
    assert not Order.objects.exists()
    stripe_mock.create.assert_not_called()


def test_webhook_marks_paid_and_decrements_stock(pending_order, post_webhook, variant, variant_b, promo):
    r = post_webhook(checkout_event(pending_order))
    assert r.status_code == 200
    pending_order.refresh_from_db()
    variant.refresh_from_db()
    variant_b.refresh_from_db()
    assert pending_order.status == Order.Status.PAID
    assert pending_order.paid_at is not None
    assert pending_order.stripe_payment_intent == "pi_test_1"
    assert (variant.stock, variant_b.stock) == (3, 9)
    assert variant.product.__class__.objects.get(pk=variant.product_id).sales_count == 3
    assert Invoice.objects.filter(order=pending_order).exists()
    assert any(pending_order.number in m.subject for m in mail.outbox)


def test_webhook_is_idempotent(pending_order, post_webhook, variant):
    event = checkout_event(pending_order)
    post_webhook(event)
    r = post_webhook(event)
    assert r.status_code == 200
    variant.refresh_from_db()
    assert variant.stock == 3  # pas de double décrément
    assert StripeEvent.objects.count() == 1
    # Un autre événement pour une commande déjà payée ne change rien non plus
    post_webhook(checkout_event(pending_order, event_id="evt_test_2",
                                etype="checkout.session.async_payment_succeeded"))
    variant.refresh_from_db()
    assert variant.stock == 3
    assert Invoice.objects.count() == 1


def test_webhook_rejects_bad_signature(pending_order, post_webhook, variant):
    r = post_webhook(checkout_event(pending_order), secret="whsec_wrong")
    assert r.status_code == 400
    pending_order.refresh_from_db()
    assert pending_order.status == Order.Status.PENDING
    assert not StripeEvent.objects.exists()


def test_webhook_without_signature_header(client):
    r = client.post("/commande/webhook/stripe/", data=b"{}", content_type="application/json")
    assert r.status_code == 400


def test_webhook_amount_mismatch_is_not_fulfilled(pending_order, post_webhook, variant):
    post_webhook(checkout_event(pending_order, amount=100))
    pending_order.refresh_from_db()
    variant.refresh_from_db()
    assert pending_order.status == Order.Status.PENDING
    assert variant.stock == 5


def test_unpaid_completed_session_waits(pending_order, post_webhook):
    post_webhook(checkout_event(pending_order, payment_status="unpaid"))
    pending_order.refresh_from_db()
    assert pending_order.status == Order.Status.PENDING


def test_expired_session_cancels_order(pending_order, post_webhook, variant):
    post_webhook(checkout_event(pending_order, etype="checkout.session.expired"))
    pending_order.refresh_from_db()
    assert pending_order.status == Order.Status.CANCELLED
    variant.refresh_from_db()
    assert variant.stock == 5


def test_shortage_at_payment_cancels_and_refunds(pending_order, post_webhook, variant, variant_b):
    Variant.objects.filter(pk=variant.pk).update(stock=1)  # vendu ailleurs entre-temps
    with mock.patch("stripe.Refund.create") as refund:
        post_webhook(checkout_event(pending_order))
    pending_order.refresh_from_db()
    variant.refresh_from_db()
    variant_b.refresh_from_db()
    assert pending_order.status == Order.Status.CANCELLED and pending_order.stock_issue
    assert (variant.stock, variant_b.stock) == (1, 10)  # rien n'est décrémenté
    refund.assert_called_once()
    assert refund.call_args.kwargs["payment_intent"] == "pi_test_1"
    assert not Invoice.objects.exists()


def test_fulfil_order_twice_directly(pending_order, variant):
    fulfil_order(pending_order.pk, payment_intent="pi_1")
    fulfil_order(pending_order.pk, payment_intent="pi_1")
    variant.refresh_from_db()
    assert variant.stock == 3


def test_promo_usage_counted_once_paid(client, product, variant, promo, shipping, stripe_mock, post_webhook):
    client.post("/panier/ajouter/", {"product": product.pk, "variant": variant.pk, "quantity": 2})
    client.post("/panier/code-promo/", {"code": "RING10"})
    client.post("/commande/", CHECKOUT_DATA)
    order = Order.objects.get()
    promo.refresh_from_db()
    assert promo.times_used == 0
    post_webhook(checkout_event(order))
    promo.refresh_from_db()
    assert promo.times_used == 1

"""Permissions, contrôle d'accès, CSRF, rate-limit et en-têtes de sécurité."""
import uuid

import pytest
from django.test import Client

from orders.models import Order

pytestmark = pytest.mark.django_db


@pytest.fixture
def order(customer, variant):
    o = Order.objects.create(customer=customer, email=customer.email, first_name="Sam", last_name="D",
                             line1="1 rue", postal_code="75011", city="Paris", subtotal=40, total=40,
                             status=Order.Status.PAID)
    return o


@pytest.mark.parametrize("url", ["/compte/", "/compte/commandes/", "/compte/adresses/", "/compte/profil/",
                                 "/compte/club/", "/compte/donnees/", "/compte/donnees/export.json"])
def test_account_pages_require_login(client, url):
    r = client.get(url)
    assert r.status_code == 302 and "/compte/connexion/" in r["Location"]


def test_order_detail_requires_token_or_owner(client, order, customer):
    assert client.get(f"/commande/{order.number}/{order.access_token}/").status_code == 200
    assert client.get(f"/commande/{order.number}/{uuid.uuid4()}/").status_code == 404
    client.force_login(customer)
    assert client.get(f"/commande/{order.number}/{uuid.uuid4()}/").status_code == 200


def test_other_customer_cannot_see_order(client, order, club_customer):
    client.force_login(club_customer)
    assert client.get(f"/commande/{order.number}/{uuid.uuid4()}/").status_code == 404
    assert client.get(f"/commande/{order.number}/{uuid.uuid4()}/facture.pdf").status_code == 404


def test_address_of_another_customer_is_not_reachable(client, customer, club_customer):
    address = club_customer.addresses.create(first_name="A", last_name="B", line1="1 rue", postal_code="69001",
                                             city="Lyon")
    client.force_login(customer)
    assert client.get(f"/compte/adresses/{address.pk}/").status_code == 404
    assert client.post(f"/compte/adresses/{address.pk}/supprimer/").status_code == 404
    assert club_customer.addresses.exists()


@pytest.mark.parametrize("url", ["/admin/", "/admin/orders/order/", "/admin/orders/order/export/"])
def test_admin_requires_staff(client, customer, staff, url):
    assert client.get(url).status_code == 302
    client.force_login(customer)
    assert client.get(url).status_code == 302
    client.force_login(staff)
    assert client.get(url).status_code == 200


def test_admin_cannot_delete_orders(client, staff, order):
    client.force_login(staff)
    assert client.get(f"/admin/orders/order/{order.pk}/delete/").status_code == 403


def test_csv_export(client, staff, order):
    from django.utils import timezone
    order.paid_at = timezone.now()
    order.save()
    client.force_login(staff)
    today = timezone.localdate().isoformat()
    r = client.get(f"/admin/orders/order/export/?start={today}&end={today}")
    assert r["Content-Type"].startswith("text/csv")
    assert order.number in r.content.decode("utf-8-sig")


def test_club_status_is_not_self_assignable(client, customer):
    client.force_login(customer)
    client.post("/compte/club/", {"club_name": "Team", "club_siret": "12345678900011", "club_message": "x",
                                  "club_status": "approved"})
    customer.refresh_from_db()
    assert customer.club_status == "pending"
    assert not customer.is_club
    client.post("/compte/profil/", {"first_name": "Sam", "last_name": "D", "club_status": "approved",
                                    "is_staff": "on"})
    customer.refresh_from_db()
    assert customer.club_status == "pending" and not customer.is_staff


def test_csrf_enforced_on_forms(product, variant):
    client = Client(enforce_csrf_checks=True)
    assert client.post("/panier/ajouter/", {"product": product.pk, "variant": variant.pk}).status_code == 403
    assert client.post("/compte/connexion/", {"username": "a@b.c", "password": "x"}).status_code == 403


def test_logout_requires_post(client, customer):
    client.force_login(customer)
    assert client.get("/compte/deconnexion/").status_code == 405


def test_login_rate_limited(client, customer):
    codes = [client.post("/compte/connexion/", {"username": customer.email, "password": "mauvais"}).status_code
             for _ in range(6)]
    assert codes[:5] == [200] * 5
    assert codes[5] == 429


def test_checkout_rate_limited(client, product, variant, shipping):
    client.post("/panier/ajouter/", {"product": product.pk, "variant": variant.pk})
    codes = [client.post("/commande/", {}).status_code for _ in range(11)]
    assert codes[-1] == 429


def test_signup_ignores_external_next(client):
    r = client.post("/compte/inscription/?next=https://evil.example/", {
        "email": "new@example.com", "first_name": "N", "last_name": "K", "password1": "Uppercut-2026!",
        "password2": "Uppercut-2026!", "accept_privacy": "on"})
    assert r.status_code == 302 and "evil.example" not in r["Location"]


def test_account_deletion_keeps_orders_anonymous(client, customer, order):
    client.force_login(customer)
    r = client.post("/compte/donnees/supprimer/", {"password": "Uppercut-2026!"})
    assert r.status_code == 302
    order.refresh_from_db()
    assert order.customer is None


def test_security_headers(client, product):
    r = client.get("/")
    csp = r["Content-Security-Policy"]
    assert "script-src 'self'" in csp and "unsafe-inline" not in csp
    assert "frame-ancestors 'none'" in csp
    assert r["X-Content-Type-Options"] == "nosniff"
    assert r["X-Frame-Options"] == "DENY"
    assert r["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_user_content_is_escaped(client, customer, product, variant):
    from catalog.models import Review
    Review.objects.create(product=product, customer=customer, author_name="<script>alert(1)</script>",
                          rating=5, title="<b>x</b>", body="<img src=x onerror=alert(1)>", is_published=True)
    html = client.get(product.get_absolute_url(), follow=True).content.decode()
    assert "<script>alert(1)</script>" not in html
    assert "<img src=x onerror" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html

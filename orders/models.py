import secrets
import uuid

from django.db import models
from django.urls import reverse
from django.utils import timezone


def generate_order_number():
    return f"BS-{timezone.now():%y%m}-{secrets.token_hex(3).upper()}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente de paiement"
        PAID = "paid", "Payée"
        PREPARING = "preparing", "En préparation"
        SHIPPED = "shipped", "Expédiée"
        DELIVERED = "delivered", "Livrée"
        CANCELLED = "cancelled", "Annulée"

    number = models.CharField("n° de commande", max_length=20, unique=True, default=generate_order_number)
    access_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    customer = models.ForeignKey(
        "accounts.Customer", null=True, blank=True, on_delete=models.SET_NULL, related_name="orders"
    )
    email = models.EmailField("e-mail")
    status = models.CharField("statut", max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)

    # Adresse de livraison (instantané au moment de la commande)
    first_name = models.CharField("prénom", max_length=80)
    last_name = models.CharField("nom", max_length=80)
    line1 = models.CharField("adresse", max_length=200)
    line2 = models.CharField("complément", max_length=200, blank=True)
    postal_code = models.CharField("code postal", max_length=10)
    city = models.CharField("ville", max_length=100)
    country = models.CharField("pays", max_length=2, default="FR")
    phone = models.CharField("téléphone", max_length=30, blank=True)

    # Montants TTC
    subtotal = models.DecimalField("sous-total articles", max_digits=10, decimal_places=2)
    club_discount = models.DecimalField("remise club", max_digits=10, decimal_places=2, default=0)
    promo_discount = models.DecimalField("remise code promo", max_digits=10, decimal_places=2, default=0)
    promo_code = models.CharField("code promo", max_length=30, blank=True)
    shipping_cost = models.DecimalField("frais de port", max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField("total TTC", max_digits=10, decimal_places=2)

    stripe_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True)
    stock_issue = models.BooleanField(
        "rupture au paiement", default=False, help_text="Stock insuffisant au moment de la confirmation."
    )

    carrier = models.CharField("transporteur", max_length=60, blank=True)
    tracking_number = models.CharField("n° de suivi", max_length=60, blank=True)
    tracking_url = models.URLField("lien de suivi", blank=True)

    created_at = models.DateTimeField("créée le", auto_now_add=True, db_index=True)
    paid_at = models.DateTimeField("payée le", null=True, blank=True)
    shipped_at = models.DateTimeField("expédiée le", null=True, blank=True)
    delivered_at = models.DateTimeField("livrée le", null=True, blank=True)

    class Meta:
        verbose_name = "commande"
        ordering = ["-created_at"]

    def __str__(self):
        return self.number

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def discount_total(self):
        return self.club_discount + self.promo_discount

    @property
    def is_paid(self):
        return self.status in {self.Status.PAID, self.Status.PREPARING, self.Status.SHIPPED, self.Status.DELIVERED}

    def get_absolute_url(self):
        return reverse("orders:detail", args=[self.number, self.access_token])

    STEPS = [Status.PAID, Status.PREPARING, Status.SHIPPED, Status.DELIVERED]

    def progress_steps(self):
        reached = self.STEPS.index(self.status) if self.status in self.STEPS else -1
        return [{"label": s.label, "done": i <= reached, "current": i == reached} for i, s in enumerate(self.STEPS)]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.Variant", null=True, on_delete=models.SET_NULL, related_name="+")
    product_name = models.CharField(max_length=150)
    variant_label = models.CharField(max_length=120, blank=True)
    sku = models.CharField(max_length=40)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "ligne de commande"

    def __str__(self):
        return f"{self.quantity} × {self.sku}"


class Invoice(models.Model):
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="invoice")
    number = models.CharField("n° de facture", max_length=20, unique=True, blank=True)
    issued_at = models.DateTimeField("émise le", default=timezone.now)
    pdf = models.FileField(upload_to="invoices/", blank=True)

    class Meta:
        verbose_name = "facture"
        ordering = ["-issued_at"]

    def __str__(self):
        return self.number

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.number:
            # Numérotation chronologique continue basée sur la séquence PostgreSQL.
            self.number = f"F{self.issued_at:%Y}-{self.pk:06d}"
            super().save(update_fields=["number"])


class StripeEvent(models.Model):
    """Journal des événements Stripe traités : garantit l'idempotence des webhooks."""

    event_id = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=100)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "événement Stripe"
        verbose_name_plural = "événements Stripe"

    def __str__(self):
        return f"{self.type} ({self.event_id})"

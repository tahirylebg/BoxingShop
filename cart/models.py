from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class PromoCode(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Pourcentage"
        FIXED = "fixed", "Montant fixe (€)"

    code = models.CharField("code", max_length=30, unique=True, help_text="Saisi en majuscules.")
    description = models.CharField("description interne", max_length=150, blank=True)
    discount_type = models.CharField("type", max_length=8, choices=DiscountType.choices, default=DiscountType.PERCENT)
    value = models.DecimalField("valeur", max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    min_subtotal = models.DecimalField(
        "panier minimum (€)", max_digits=8, decimal_places=2, default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    valid_from = models.DateTimeField("valable du", default=timezone.now)
    valid_until = models.DateTimeField("valable jusqu'au", null=True, blank=True)
    max_uses = models.PositiveIntegerField("utilisations max.", null=True, blank=True, help_text="Vide = illimité.")
    times_used = models.PositiveIntegerField("utilisations", default=0, editable=False)
    is_active = models.BooleanField("actif", default=True)

    class Meta:
        verbose_name = "code promo"
        verbose_name_plural = "codes promo"
        ordering = ["-valid_from"]

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def check_validity(self, subtotal, now=None):
        """Retourne (valide, message d'erreur)."""
        now = now or timezone.now()
        if not self.is_active:
            return False, "Ce code n'est plus actif."
        if now < self.valid_from or (self.valid_until and now > self.valid_until):
            return False, "Ce code n'est pas valable à cette date."
        if self.max_uses is not None and self.times_used >= self.max_uses:
            return False, "Ce code a atteint son nombre maximal d'utilisations."
        if subtotal < self.min_subtotal:
            return False, f"Ce code nécessite un panier d'au moins {self.min_subtotal} €."
        return True, ""

    def discount_for(self, amount):
        if self.discount_type == self.DiscountType.PERCENT:
            discount = amount * min(self.value, Decimal("100")) / Decimal("100")
        else:
            discount = self.value
        return min(discount, amount).quantize(Decimal("0.01"))


class Cart(models.Model):
    customer = models.ForeignKey(
        "accounts.Customer", null=True, blank=True, on_delete=models.CASCADE, related_name="carts"
    )
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    promo_code = models.ForeignKey(PromoCode, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "panier"

    def __str__(self):
        return f"Panier #{self.pk}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.Variant", on_delete=models.CASCADE, related_name="+")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["added_at"]
        constraints = [models.UniqueConstraint(fields=["cart", "variant"], name="unique_cart_variant")]

    def __str__(self):
        return f"{self.quantity} × {self.variant}"

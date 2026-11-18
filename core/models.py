from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class SEOFields(models.Model):
    """Balises méta éditables depuis l'admin (repli automatique si vides)."""

    meta_title = models.CharField(
        "balise <title>", max_length=70, blank=True, help_text="70 caractères max. Laisser vide = titre auto."
    )
    meta_description = models.CharField(
        "méta description", max_length=160, blank=True, help_text="160 caractères max., affichée dans Google."
    )

    class Meta:
        abstract = True


class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # un singleton ne se supprime pas
        return 0, {}

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ShippingSettings(SingletonModel):
    carrier_label = models.CharField("transporteur", max_length=80, default="Colissimo suivi 48 h")
    flat_rate = models.DecimalField(
        "frais de port (€ TTC)", max_digits=7, decimal_places=2, default=Decimal("6.90"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    free_shipping_threshold = models.DecimalField(
        "livraison offerte dès (€ TTC)", max_digits=8, decimal_places=2, default=Decimal("90.00"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Montant des articles (après remises) à partir duquel la livraison est offerte.",
    )

    class Meta:
        verbose_name = "réglages de livraison"
        verbose_name_plural = "réglages de livraison"

    def __str__(self):
        return f"{self.carrier_label} — {self.flat_rate} € (offerte dès {self.free_shipping_threshold} €)"


class PageMeta(SEOFields):
    """Méta SEO des pages fixes (accueil, guides, pages légales…)."""

    path = models.CharField("chemin de la page", max_length=200, unique=True, help_text="Ex. / ou /guides/")
    label = models.CharField("page", max_length=100)

    class Meta:
        verbose_name = "méta d'une page fixe"
        verbose_name_plural = "SEO des pages fixes"
        ordering = ["path"]

    def __str__(self):
        return f"{self.label} ({self.path})"

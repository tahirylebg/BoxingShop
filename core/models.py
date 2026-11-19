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


class Photo(models.Model):
    """Photothèque éditoriale (accueil, disciplines, guides) avec crédit et déclinaisons WebP."""

    RENDITION_WIDTHS = (640, 1024, 1600)

    title = models.CharField("titre interne", max_length=120)
    image = models.ImageField("image source", upload_to="photos/originals/")
    alt = models.CharField("texte alternatif", max_length=200, blank=True,
                           help_text="Vide si la photo est purement décorative.")
    credit = models.CharField("auteur", max_length=120, blank=True)
    credit_source = models.CharField("source", max_length=60, blank=True, help_text="Ex. Pexels, Unsplash")
    credit_url = models.URLField("lien vers la photo", blank=True)
    width = models.PositiveIntegerField(default=0, editable=False)
    height = models.PositiveIntegerField(default=0, editable=False)
    renditions = models.JSONField(default=dict, editable=False)

    class Meta:
        verbose_name = "photo"
        verbose_name_plural = "photothèque"
        ordering = ["title"]

    def __str__(self):
        return self.title

    def rendition_folder(self):
        return "photos/webp"

    @property
    def credit_line(self):
        return " · ".join(filter(None, [self.credit, self.credit_source]))

    def save(self, *args, **kwargs):
        from catalog.images import build_renditions

        changed = not self.pk or Photo.objects.filter(pk=self.pk).values_list("image", flat=True).first() != self.image.name
        super().save(*args, **kwargs)
        if changed or not self.renditions:
            build_renditions(self)
            super().save(update_fields=["renditions", "width", "height"])


class HomeSettings(SingletonModel):
    hero_photo = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                                   verbose_name="photo du hero", help_text="Affichée en noir et blanc, plein écran.")
    hero_title = models.CharField("titre du hero", max_length=80, default="Frappe juste.")
    hero_text = models.TextField(
        "manifeste", max_length=400,
        default="Du matériel de combat choisi par des pratiquants, éprouvé au sac, au sparring et sur le ring.",
    )

    guides_photo = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                                     verbose_name="photo de la page Guides")
    campaign_photo = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                                       verbose_name="photo de la bande campagne",
                                       help_text="Bande plein écran affichée avant le pied de page.")
    campaign_title = models.CharField("slogan de campagne", max_length=60, default="Rien n'est donné.")
    campaign_text = models.CharField("texte de campagne", max_length=200,
                                     default="Chaque round se gagne à l'entraînement. Équipez-vous pour durer.")
    campaign_cta = models.CharField("bouton de campagne", max_length=40, default="S'équiper")

    class Meta:
        verbose_name = "page d'accueil"
        verbose_name_plural = "page d'accueil"

    def __str__(self):
        return "Page d'accueil"

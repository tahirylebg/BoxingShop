from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count, Min, Q, Sum
from django.urls import reverse

from core.models import SEOFields


class Discipline(SEOFields):
    name = models.CharField("nom", max_length=80)
    short_name = models.CharField("nom court (menu)", max_length=20, blank=True)
    slug = models.SlugField(unique=True)
    tagline = models.CharField("accroche", max_length=160, blank=True)
    description = models.TextField(blank=True)
    position = models.PositiveSmallIntegerField(default=0)
    photo = models.ForeignKey("core.Photo", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                              verbose_name="photo (mosaïque d'accueil)")

    class Meta:
        ordering = ["position", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:discipline", args=[self.slug])


class Category(SEOFields):
    """Type de produit (Gants, Protections…), éventuellement sous-type (Protège-tibias…)."""

    name = models.CharField("nom", max_length=80)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children", verbose_name="type parent"
    )
    description = models.TextField(blank=True)
    photo = models.ForeignKey("core.Photo", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                              verbose_name="photo du rayon", help_text="Photo carrée centrée sur l'objet (accueil).")
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "type de produit"
        verbose_name_plural = "types de produit"
        ordering = ["position", "name"]

    @property
    def image(self):
        """Image de tuile : la photo de rayon si son fichier existe, sinon la photo principale du produit
        en stock le plus vendu du rayon (sous-rayons compris)."""
        from django.core.files.storage import default_storage

        if self.photo_id and self.photo.renditions and default_storage.exists(self.photo.image.name):
            return self.photo
        product = (Product.objects.filter(category_id__in=self.descendant_ids(), is_active=True,
                                          variants__is_active=True, variants__stock__gt=0)
                   .order_by("-sales_count", "pk").first())
        return product.images.order_by("position", "id").first() if product else None

    def __str__(self):
        return f"{self.parent} › {self.name}" if self.parent_id else self.name

    def get_absolute_url(self):
        return reverse("catalog:category", args=[self.slug])

    @property
    def root(self):
        return self.parent if self.parent_id else self

    def descendant_ids(self):
        return [self.pk, *self.children.values_list("pk", flat=True)]


class SizeChart(models.Model):
    """Tableau de correspondance morphologique (poids/taille du pratiquant → taille ou oz conseillés)."""

    name = models.CharField("nom", max_length=120)
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="size_charts",
        help_text="Tableau par défaut pour ce type de produit.",
    )
    measure_label = models.CharField("conseil exprimé en", max_length=40, default="Poids de gant")
    intro = models.TextField("introduction", blank=True)

    class Meta:
        verbose_name = "tableau de tailles"
        verbose_name_plural = "tableaux de tailles"

    def __str__(self):
        return self.name


class SizeChartRow(models.Model):
    chart = models.ForeignKey(SizeChart, on_delete=models.CASCADE, related_name="rows")
    body_weight_min = models.PositiveSmallIntegerField("poids min (kg)", null=True, blank=True)
    body_weight_max = models.PositiveSmallIntegerField("poids max (kg)", null=True, blank=True)
    height_min = models.PositiveSmallIntegerField("taille min (cm)", null=True, blank=True)
    height_max = models.PositiveSmallIntegerField("taille max (cm)", null=True, blank=True)
    recommended = models.CharField("conseillé", max_length=40)
    note = models.CharField("usage", max_length=120, blank=True)
    position = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["position", "body_weight_min"]
        verbose_name = "ligne"

    def __str__(self):
        return self.recommended

    @staticmethod
    def _range(lo, hi, unit):
        if lo is None and hi is None:
            return "—"
        if lo is None:
            return f"< {hi} {unit}"
        if hi is None:
            return f"> {lo} {unit}"
        return f"{lo}–{hi} {unit}"

    @property
    def weight_range(self):
        return self._range(self.body_weight_min, self.body_weight_max, "kg")

    @property
    def height_range(self):
        return self._range(self.height_min, self.height_max, "cm")


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def with_listing_data(self):
        active_variants = Q(variants__is_active=True)
        return self.select_related("discipline", "category").annotate(
            min_price=Min("variants__price", filter=active_variants),
            total_stock=Sum("variants__stock", filter=active_variants),
        )


class Product(SEOFields):
    class Material(models.TextChoices):
        LEATHER = "cuir", "Cuir véritable"
        MICROFIBER = "microfibre", "Microfibre"
        SYNTHETIC = "synthetique", "Synthétique (PU)"
        COTTON = "coton", "Coton"
        POLYESTER = "polyester", "Polyester / satin"
        SILICONE = "silicone", "Silicone / gel"
        OTHER = "autre", "Autre"

    class Level(models.TextChoices):
        BEGINNER = "debutant", "Débutant"
        SPARRING = "sparring", "Sparring"
        COMBAT = "combat", "Combat"

    class Range(models.TextChoices):
        STANDARD = "standard", "Standard"
        PRO = "pro", "Pro"
        COMPETITION = "competition", "Compétition"

    name = models.CharField("nom", max_length=150)
    slug = models.SlugField(max_length=170, unique=True)
    discipline = models.ForeignKey(
        Discipline, on_delete=models.PROTECT, related_name="primary_products", verbose_name="discipline principale"
    )
    disciplines = models.ManyToManyField(
        Discipline, blank=True, related_name="products", verbose_name="disciplines compatibles",
        help_text="La discipline principale est incluse automatiquement.",
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products", verbose_name="type")
    short_description = models.CharField("accroche", max_length=200)
    description = models.TextField(
        "description", help_text="Paragraphes séparés par une ligne vide. « ## » = intertitre, « - » = puce."
    )
    # Spécifications structurées
    padding = models.CharField("rembourrage", max_length=120, blank=True)
    closure = models.CharField("fermeture", max_length=80, blank=True)
    origin = models.CharField("fabrication / origine", max_length=80, blank=True)
    material = models.CharField("matière", max_length=20, choices=Material.choices, db_index=True)
    level = models.CharField("niveau de pratique", max_length=10, choices=Level.choices, db_index=True)
    range_tier = models.CharField("gamme", max_length=12, choices=Range.choices, default=Range.STANDARD)
    extra_specs = models.JSONField(
        "spécifications complémentaires", default=dict, blank=True,
        help_text='Paires libellé/valeur, ex. {"Poids unitaire": "380 g", "Lavage": "30 °C"}',
    )
    size_chart = models.ForeignKey(
        SizeChart, null=True, blank=True, on_delete=models.SET_NULL, related_name="products",
        verbose_name="tableau de tailles", help_text="Vide = tableau par défaut du type de produit.",
    )
    is_active = models.BooleanField("en ligne", default=True, db_index=True)
    is_featured = models.BooleanField("mis en avant", default=False)
    sales_count = models.PositiveIntegerField("ventes", default=0, editable=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "produit"
        ordering = ["-sales_count", "name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:product", args=[self.discipline.slug, self.category.slug, self.slug])

    @property
    def is_premium(self):
        return self.range_tier in (self.Range.PRO, self.Range.COMPETITION)

    def get_size_chart(self):
        if self.size_chart_id:
            return self.size_chart
        return SizeChart.objects.filter(category__in=[self.category_id, self.category.root.pk]).first()

    def rating_summary(self):
        return self.reviews.filter(is_published=True).aggregate(avg=Avg("rating"), count=Count("id"))

    def spec_list(self):
        rows = [
            ("Matière", self.get_material_display()),
            ("Rembourrage", self.padding),
            ("Fermeture", self.closure),
            ("Niveau", self.get_level_display()),
            ("Gamme", self.get_range_tier_display()),
            ("Origine", self.origin),
        ]
        rows += [(str(k), str(v)) for k, v in (self.extra_specs or {}).items()]
        return [(k, v) for k, v in rows if v]


class ProductImage(models.Model):
    RENDITION_WIDTHS = (360, 640, 960, 1400)

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("image source", upload_to="products/originals/")
    alt = models.CharField("texte alternatif", max_length=200, help_text="Décrit l'image pour les non-voyants.")
    color = models.CharField(
        "couleur associée", max_length=40, blank=True, help_text="Affichée quand cette couleur est sélectionnée."
    )
    position = models.PositiveSmallIntegerField(default=0)
    credit = models.CharField("crédit photo", max_length=160, blank=True, help_text="Ex. Ron Lach · Pexels")
    width = models.PositiveIntegerField(default=0, editable=False)
    height = models.PositiveIntegerField(default=0, editable=False)
    renditions = models.JSONField(default=dict, editable=False, help_text="{largeur: chemin WebP}")

    class Meta:
        verbose_name = "image"
        ordering = ["position", "id"]

    def __str__(self):
        return self.alt

    def rendition_folder(self):
        return f"products/webp/{self.product_id}"

    def save(self, *args, **kwargs):
        from .images import build_renditions

        regenerate = kwargs.pop("regenerate", False)
        image_changed = False
        if self.pk:
            old = ProductImage.objects.filter(pk=self.pk).values_list("image", flat=True).first()
            image_changed = old != self.image.name
        super().save(*args, **kwargs)
        if regenerate or image_changed or not self.renditions:
            build_renditions(self)
            super().save(update_fields=["renditions", "width", "height"])


class VariantQuerySet(models.QuerySet):
    def low_stock(self):
        return self.filter(is_active=True, stock__lte=models.F("low_stock_threshold"))


class Variant(models.Model):
    class Size(models.TextChoices):
        XS = "XS", "XS"
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"
        XXL = "XXL", "XXL"

    SIZE_ORDER = [s.value for s in Size]
    WEIGHT_CHOICES = (8, 10, 12, 14, 16, 18)

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField("SKU", max_length=40, unique=True)
    color = models.CharField("couleur", max_length=40, blank=True)
    color_hex = models.CharField("code couleur", max_length=7, blank=True, help_text="Ex. #0D0D0D")
    weight_oz = models.PositiveSmallIntegerField(
        "poids (oz)", null=True, blank=True, validators=[MinValueValidator(4), MaxValueValidator(20)]
    )
    size = models.CharField("taille", max_length=3, choices=Size.choices, blank=True)
    price = models.DecimalField("prix TTC (€)", max_digits=8, decimal_places=2,
                                validators=[MinValueValidator(Decimal("0"))])
    compare_at_price = models.DecimalField(
        "prix barré (€)", max_digits=8, decimal_places=2, null=True, blank=True,
        help_text="Renseigner pour afficher une promotion.",
    )
    stock = models.PositiveIntegerField("stock", default=0)
    low_stock_threshold = models.PositiveIntegerField("seuil d'alerte", default=3)
    is_active = models.BooleanField("active", default=True)

    objects = VariantQuerySet.as_manager()

    class Meta:
        verbose_name = "déclinaison (SKU)"
        verbose_name_plural = "déclinaisons (SKU)"
        ordering = ["product", "color", "weight_oz", "size"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "color", "weight_oz", "size"], name="unique_variant_options", nulls_distinct=False
            ),
            models.CheckConstraint(condition=Q(price__gte=0), name="variant_price_positive"),
        ]

    def __str__(self):
        return f"{self.product.name} — {self.label}" if self.label else self.product.name

    @property
    def label(self):
        parts = [self.color, f"{self.weight_oz} oz" if self.weight_oz else "", self.size]
        return " / ".join(p for p in parts if p)

    @property
    def in_stock(self):
        return self.is_active and self.stock > 0

    @property
    def is_low_stock(self):
        return self.in_stock and self.stock <= self.low_stock_threshold

    @property
    def on_sale(self):
        return bool(self.compare_at_price and self.compare_at_price > self.price)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    customer = models.ForeignKey(
        "accounts.Customer", null=True, blank=True, on_delete=models.SET_NULL, related_name="reviews"
    )
    author_name = models.CharField("auteur", max_length=80)
    rating = models.PositiveSmallIntegerField("note", validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField("titre", max_length=120)
    body = models.TextField("avis", max_length=2000)
    is_published = models.BooleanField("publié", default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "avis client"
        verbose_name_plural = "avis clients"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=Q(rating__gte=1, rating__lte=5), name="review_rating_range"),
        ]

    def __str__(self):
        return f"{self.product} — {self.rating}/5"

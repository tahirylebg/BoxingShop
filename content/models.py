from django.db import models
from django.urls import reverse

from core.models import SEOFields


class Guide(SEOFields):
    title = models.CharField("titre", max_length=160)
    slug = models.SlugField(max_length=170, unique=True)
    kicker = models.CharField("surtitre", max_length=60, default="Guide technique")
    excerpt = models.CharField("chapô", max_length=300)
    body = models.TextField(
        "contenu", help_text="Paragraphes séparés par une ligne vide. « ## » = intertitre, « - » = puce, **gras**."
    )
    products = models.ManyToManyField(
        "catalog.Product", blank=True, related_name="guides", verbose_name="produits concernés"
    )
    categories = models.ManyToManyField(
        "catalog.Category", blank=True, related_name="guides", verbose_name="types de produit concernés",
        help_text="Le guide sera proposé sur toutes les fiches de ces types.",
    )
    photo = models.ForeignKey("core.Photo", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
                              verbose_name="photo de couverture")
    TOPICS = [("gants", "Gants"), ("protections", "Protections"), ("entretien", "Entretien"), ("debutant", "Débutant")]
    topic = models.CharField("thème", max_length=20, choices=TOPICS, default="gants",
                             help_text="Sert aux filtres de la page Guides.")
    reading_minutes = models.PositiveSmallIntegerField("temps de lecture (min)", default=5)
    is_published = models.BooleanField("publié", default=True)
    published_at = models.DateField("date de publication")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "guide technique"
        verbose_name_plural = "guides techniques"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("content:guide", args=[self.slug])

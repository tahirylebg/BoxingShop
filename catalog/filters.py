"""Filtres multicritères du catalogue.

Les filtres sont lus depuis la query-string (URL partageable, fonctionne en GET classique sans JS).
Les critères portant sur les déclinaisons (poids, taille, disponibilité) s'appliquent à une MÊME
déclinaison via une sous-requête EXISTS : « 14 oz en stock » signifie qu'une déclinaison 14 oz est en stock.
"""
from django.db.models import Count, Exists, OuterRef, Prefetch, Q
from django.http import QueryDict
from django.utils.functional import cached_property

from core.cache import cached

from .models import Category, Discipline, Product, ProductImage, Variant

SORTS = {
    "pertinence": ("Pertinence", ["-is_featured", "-sales_count", "name"]),
    "ventes": ("Meilleures ventes", ["-sales_count", "name"]),
    "prix-asc": ("Prix croissant", ["min_price", "name"]),
    "prix-desc": ("Prix décroissant", ["-min_price", "name"]),
    "nouveautes": ("Nouveautés", ["-created_at"]),
}
LEVEL_ORDER = [c for c, _ in Product.Level.choices]


def listing_queryset():
    return (
        Product.objects.active()
        .with_listing_data()
        .prefetch_related(Prefetch("images", queryset=ProductImage.objects.order_by("position", "id")))
    )


class CatalogFilter:
    MULTI = ("discipline", "type", "poids", "taille", "matiere", "niveau")

    def __init__(self, params: QueryDict, discipline=None, category=None):
        self.params = params
        self.discipline = discipline  # contexte fixé par l'URL
        self.category = category
        self.values = {key: [v for v in params.getlist(key) if v] for key in self.MULTI}
        self.values["poids"] = [v for v in self.values["poids"] if v.isdigit()]
        self.in_stock = params.get("dispo") == "1"
        self.q = (params.get("q") or "").strip()[:80]
        self.sort = params.get("tri") if params.get("tri") in SORTS else "pertinence"

    # --- Requêtes -----------------------------------------------------------------------------
    def base_queryset(self):
        qs = Product.objects.active()
        if self.discipline:
            qs = qs.filter(pk__in=Product.objects.filter(disciplines=self.discipline).values("pk"))
        if self.category:
            qs = qs.filter(category_id__in=self.category.descendant_ids())
        return qs

    def queryset(self):
        qs = listing_queryset().filter(pk__in=self.base_queryset().values("pk"))
        v = self.values
        if v["discipline"]:
            qs = qs.filter(pk__in=Product.objects.filter(disciplines__slug__in=v["discipline"]).values("pk"))
        if v["type"]:
            qs = qs.filter(Q(category__slug__in=v["type"]) | Q(category__parent__slug__in=v["type"]))
        if v["matiere"]:
            qs = qs.filter(material__in=v["matiere"])
        if v["niveau"]:
            qs = qs.filter(level__in=v["niveau"])
        if self.q:
            # sous-requête : une jointure sur les variantes fausserait les agrégats prix/stock
            matches = Product.objects.filter(
                Q(name__icontains=self.q) | Q(short_description__icontains=self.q)
                | Q(category__name__icontains=self.q) | Q(variants__sku__iexact=self.q)
            ).values("pk")
            qs = qs.filter(pk__in=matches)
        variant_q = Q(product=OuterRef("pk"), is_active=True)
        if v["poids"]:
            variant_q &= Q(weight_oz__in=[int(x) for x in v["poids"]])
        if v["taille"]:
            variant_q &= Q(size__in=v["taille"])
        if self.in_stock:
            variant_q &= Q(stock__gt=0)
        if v["poids"] or v["taille"] or self.in_stock:
            qs = qs.filter(Exists(Variant.objects.filter(variant_q)))
        return qs.order_by(*SORTS[self.sort][1])

    # --- Facettes (options disponibles dans le contexte, mises en cache) ---------------------
    @cached_property
    def facets(self):
        key = f"facets:{self.discipline.pk if self.discipline else 0}:{self.category.pk if self.category else 0}"
        return cached(key, self._build_facets)

    def _build_facets(self):
        base_ids = list(self.base_queryset().values_list("pk", flat=True))
        variants = Variant.objects.filter(product_id__in=base_ids, is_active=True)
        weights = sorted(set(variants.exclude(weight_oz=None).values_list("weight_oz", flat=True)))
        sizes = set(variants.exclude(size="").values_list("size", flat=True))
        products = Product.objects.filter(pk__in=base_ids)
        materials = dict(products.values_list("material").annotate(n=Count("id")))
        levels = dict(products.values_list("level").annotate(n=Count("id")))
        disciplines = [] if self.discipline else [
            (d.slug, d.name, d.n) for d in Discipline.objects.annotate(
                n=Count("products", filter=Q(products__in=base_ids), distinct=True)).filter(n__gt=0)
        ]
        categories = [] if (self.category and not self.category.children.exists()) else [
            (c.slug, c.name, c.n) for c in Category.objects.filter(
                parent=self.category if self.category else None).annotate(
                n=Count("products", filter=Q(products__in=base_ids), distinct=True)
                + Count("children__products", filter=Q(children__products__in=base_ids), distinct=True)
            ).filter(n__gt=0)
        ]
        return {
            "discipline": disciplines,
            "type": categories,
            "poids": [(str(w), f"{w} oz", None) for w in weights if 8 <= w <= 18],
            "taille": [(s, s, None) for s in Variant.SIZE_ORDER if s in sizes],
            "matiere": [(c, label, materials[c]) for c, label in Product.Material.choices if c in materials],
            "niveau": [(c, label, levels[c]) for c, label in Product.Level.choices if c in levels],
        }

    def groups(self):
        """Structure prête pour le template : [(clé, légende, style, [(valeur, libellé, n, coché)])]."""
        labels = {"discipline": "Discipline", "type": "Type de produit", "poids": "Poids (oz)", "taille": "Taille",
                  "matiere": "Matière", "niveau": "Niveau de pratique"}
        styles = {"poids": "chips", "taille": "chips"}
        out = []
        for key in ("discipline", "type", "poids", "taille", "matiere", "niveau"):
            options = self.facets[key]
            if options:
                out.append((key, labels[key], styles.get(key, "list"),
                            [(val, label, n, val in self.values[key]) for val, label, n in options]))
        return out

    def active_chips(self):
        """Filtres actifs avec l'URL qui retire chacun d'eux."""
        labels = {}
        for key, _, _, options in self.groups():
            for val, label, _, _ in options:
                labels[(key, val)] = label
        chips = []
        for key in self.MULTI:
            for val in self.values[key]:
                remaining = self.params.copy()
                remaining.setlist(key, [x for x in self.values[key] if x != val])
                remaining.pop("page", None)
                chips.append((labels.get((key, val), val), "?" + remaining.urlencode()))
        if self.in_stock:
            remaining = self.params.copy()
            remaining.pop("dispo", None)
            remaining.pop("page", None)
            chips.append(("En stock", "?" + remaining.urlencode()))
        if self.q:
            remaining = self.params.copy()
            remaining.pop("q", None)
            chips.append((f"« {self.q} »", "?" + remaining.urlencode()))
        return chips

    @property
    def is_filtered(self):
        return any(self.values.values()) or self.in_stock or bool(self.q)

    @staticmethod
    def sort_options():
        return [(k, v[0]) for k, v in SORTS.items()]

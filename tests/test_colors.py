from decimal import Decimal

import pytest
from django.http import QueryDict

from catalog.cards import decorate
from catalog.colors import from_slug, split_query
from catalog.filters import CatalogFilter
from catalog.models import Product, ProductImage, Variant


@pytest.mark.parametrize("query, text, colors", [
    ("gants bleus", "gants", ["Bleu"]),
    ("gant rouge", "gant", ["Rouge"]),
    ("protège-tibias noir", "protège-tibias", ["Noir"]),
    ("Short BLANCHE", "Short", ["Blanc"]),
    ("gants", "gants", []),
])
def test_split_query_reconnait_genre_et_nombre(query, text, colors):
    assert split_query(query) == (text, colors)


def test_from_slug():
    assert from_slug("bleu") == "Bleu"
    assert from_slug("bleues") == "Bleu"
    assert from_slug("violet") is None


@pytest.fixture
def two_colors(product):
    Variant.objects.create(product=product, sku="BS-T-NOI-10", color="Noir", weight_oz=10, price=Decimal("40"), stock=5)
    Variant.objects.create(product=product, sku="BS-T-BLE-10", color="Bleu", weight_oz=10, price=Decimal("40"), stock=5)
    other = Product.objects.create(name="Gant rouge seul", slug="gant-rouge", discipline=product.discipline,
                                   category=product.category, short_description="x", description="x",
                                   material="cuir", level="sparring")
    Variant.objects.create(product=other, sku="BS-R-ROU-10", color="Rouge", weight_oz=10, price=Decimal("40"), stock=5)
    return product, other


@pytest.mark.django_db
def test_recherche_couleur_filtre_les_produits(two_colors):
    product, other = two_colors
    found = list(CatalogFilter(QueryDict("q=gants bleus")).queryset())
    assert found == [product]
    found = list(CatalogFilter(QueryDict("q=gant rouge")).queryset())
    assert found == [other]


@pytest.mark.django_db
def test_filtre_couleur_seul(two_colors):
    product, _ = two_colors
    flt = CatalogFilter(QueryDict("couleur=bleu"))
    assert list(flt.queryset()) == [product]
    group = next(g for g in flt.groups() if g[0] == "couleur")
    assert ("bleu", "Bleu", 1, True) in group[3]


@pytest.mark.django_db
def test_carte_montre_la_couleur_active(two_colors):
    product, _ = two_colors
    ProductImage.objects.bulk_create([  # bulk_create : pas de génération de déclinaisons (fichiers fictifs)
        ProductImage(product=product, color="Noir", position=0, image="x/noir.jpg"),
        ProductImage(product=product, color="Bleu", position=1, image="x/bleu.jpg"),
    ])
    card = decorate(Product.objects.filter(pk=product.pk).prefetch_related("images"), colors=["Bleu"])[0]
    assert card.card_image.color == "Bleu"
    assert card.card_color_slug == "bleu"
    default = decorate(Product.objects.filter(pk=product.pk).prefetch_related("images"))[0]
    assert default.card_image.color in {"Noir", "Bleu"}
    assert default.card_color_slug == ""

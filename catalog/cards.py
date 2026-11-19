"""Données d'affichage des cartes produit : pastilles couleur, badges texte et options d'ajout rapide.

Une seule requête pour toutes les cartes d'une page (pas de N+1).
"""
from datetime import timedelta

from django.utils import timezone

from .models import Variant

NEW_DAYS = 30
MAX_SWATCHES = 4


def decorate(products):
    products = list(products)
    if not products:
        return products
    by_product = {}
    for v in Variant.objects.filter(product__in=products, is_active=True).order_by("product", "color", "weight_oz", "size"):
        by_product.setdefault(v.product_id, []).append(v)
    fresh = timezone.now() - timedelta(days=NEW_DAYS)
    for p in products:
        variants = by_product.get(p.pk, [])
        colors, seen = [], set()
        for v in variants:
            if v.color and v.color not in seen:
                seen.add(v.color)
                colors.append({"name": v.color, "hex": v.color_hex or "#0D0D0D"})
        p.swatches = colors[:MAX_SWATCHES]
        p.swatches_more = max(0, len(colors) - MAX_SWATCHES)
        p.is_low = any(v.is_low_stock for v in variants)
        p.is_new = p.created_at >= fresh
        # Ajout rapide : un bouton par poids (ou par taille) dans le premier coloris en stock.
        default_color = next((v.color for v in variants if v.in_stock), variants[0].color if variants else "")
        same_color = [v for v in variants if v.color == default_color]
        quick = []
        for v in same_color:
            label = f"{v.weight_oz} oz" if v.weight_oz else (v.size or "")
            if label and label not in {q["label"] for q in quick}:
                quick.append({"id": v.pk, "label": label, "in_stock": v.in_stock})
        if not quick and same_color:
            quick = [{"id": same_color[0].pk, "label": "", "in_stock": same_color[0].in_stock}]
        p.quick = quick
        p.quick_color = default_color if len(colors) > 1 else ""
    return products

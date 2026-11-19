"""Données d'affichage des cartes produit : image de la bonne couleur, pastilles, badges et ajout rapide.

Une seule requête pour toutes les variantes d'une page (pas de N+1) ; les images viennent du prefetch.
"""
from datetime import timedelta

from django.utils import timezone

from .colors import color_slug
from .models import Variant

NEW_DAYS = 30
MAX_SWATCHES = 4


def _srcset(image):
    if not image or not image.renditions:
        return "", ""
    from core.templatetags.shop import rendition_srcset

    return rendition_srcset(image)


def decorate(products, colors=None):
    """colors : couleurs actives (filtre ou recherche) ; la carte montre alors la photo de cette couleur."""
    products = list(products)
    if not products:
        return products
    wanted = list(colors or [])
    by_product = {}
    for v in Variant.objects.filter(product__in=products, is_active=True).order_by("product", "color", "weight_oz", "size"):
        by_product.setdefault(v.product_id, []).append(v)
    fresh = timezone.now() - timedelta(days=NEW_DAYS)
    for p in products:
        variants = by_product.get(p.pk, [])
        images = list(p.images.all())
        colors_in_order, seen = [], set()
        for v in variants:
            if v.color and v.color not in seen:
                seen.add(v.color)
                colors_in_order.append(v.color)
        in_stock = [c for c in colors_in_order if any(v.color == c and v.in_stock for v in variants)]
        chosen = next((c for c in wanted if c in colors_in_order), None) or (in_stock or colors_in_order or [""])[0]
        own = [i for i in images if i.color == chosen]
        ambiance = [i for i in images if not i.color]
        p.card_color = chosen
        p.card_color_slug = color_slug(chosen) if (wanted and chosen in wanted) else ""
        p.card_image = own[0] if own else (images[0] if images else None)
        p.card_alt = ambiance[0] if ambiance else (own[1] if len(own) > 1 else None)
        swatches = []
        for c in colors_in_order:
            hex_ = next((v.color_hex for v in variants if v.color == c and v.color_hex), "#0D0D0D")
            first = next((i for i in images if i.color == c), None)
            src, srcset = _srcset(first)
            swatches.append({"name": c, "hex": hex_, "slug": color_slug(c), "src": src, "srcset": srcset,
                             "active": c == chosen})
        p.swatches = swatches[:MAX_SWATCHES]
        p.swatches_more = max(0, len(swatches) - MAX_SWATCHES)
        p.is_low = any(v.is_low_stock for v in variants)
        p.is_new = p.created_at >= fresh
        # Ajout rapide : un bouton par poids (ou taille) dans la couleur affichée sur la carte.
        same_color = [v for v in variants if v.color == chosen] or variants
        quick = []
        for v in same_color:
            label = f"{v.weight_oz} oz" if v.weight_oz else (v.size or "")
            if label and label not in {q["label"] for q in quick}:
                quick.append({"id": v.pk, "label": label, "in_stock": v.in_stock})
        if not quick and same_color:
            quick = [{"id": same_color[0].pk, "label": "", "in_stock": same_color[0].in_stock}]
        p.quick = quick
        p.quick_color = chosen if len(colors_in_order) > 1 else ""
    return products

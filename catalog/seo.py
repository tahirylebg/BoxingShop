"""Données structurées Schema.org (JSON-LD)."""
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone


def _abs(path):
    return path if path.startswith("http") else f"{settings.SITE_URL}{path}"


def breadcrumb_jsonld(request, crumbs):
    items = [{"@type": "ListItem", "position": 1, "name": "Accueil", "item": _abs("/")}]
    for i, (name, url) in enumerate(crumbs, start=2):
        item = {"@type": "ListItem", "position": i, "name": name}
        item["item"] = _abs(url or request.path)
        items.append(item)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}


def product_jsonld(request, product, variants, images, rating, reviews):
    url = _abs(product.get_absolute_url())
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": product.short_description,
        "url": url,
        "brand": {"@type": "Brand", "name": "Boxing Shop"},
        "category": product.category.name,
        "material": product.get_material_display(),
        "image": [_abs(default_storage.url(img.renditions[max(img.renditions, key=int)]))
                  for img in images if img.renditions],
        "sku": variants[0].sku if variants else "",
        "offers": [
            {
                "@type": "Offer",
                "sku": v.sku,
                "name": v.label or product.name,
                "url": f"{url}?sku={v.sku}",
                "price": str(v.price),
                "priceCurrency": "EUR",
                "availability": "https://schema.org/InStock" if v.in_stock else "https://schema.org/OutOfStock",
                "itemCondition": "https://schema.org/NewCondition",
            }
            for v in variants
        ],
    }
    if rating and rating.get("count"):
        data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": f"{rating['avg']:.1f}",
            "reviewCount": rating["count"],
            "bestRating": "5",
            "worstRating": "1",
        }
        data["review"] = [
            {
                "@type": "Review",
                "author": {"@type": "Person", "name": r.author_name},
                "reviewRating": {"@type": "Rating", "ratingValue": r.rating, "bestRating": "5"},
                "name": r.title,
                "reviewBody": r.body,
                "datePublished": timezone.localdate(r.created_at).isoformat(),
            }
            for r in reviews[:5]
        ]
    return data

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.ratelimit import ratelimit

from .cards import decorate
from .colors import color_slug, from_slug

from content.models import Guide

from .filters import CatalogFilter, listing_queryset
from .forms import ReviewForm
from .models import Category, Discipline, Product, ProductImage, Variant
from .seo import breadcrumb_jsonld, product_jsonld

PER_PAGE = 24


def _listing(request, *, title, intro="", kicker="Catalogue", discipline=None, category=None, crumbs=(),
             meta_obj=None):
    flt = CatalogFilter(request.GET, discipline=discipline, category=category)
    page = Paginator(flt.queryset(), PER_PAGE).get_page(request.GET.get("page"))
    context = {
        "title": title, "intro": intro, "kicker": kicker, "filter": flt, "page": page,
        "products": decorate(page.object_list, colors=flt.colors), "fill_guide": _fill_guide(category),
        "discipline": discipline, "category": category, "crumbs": crumbs, "meta_obj": meta_obj,
        "breadcrumb_ld": breadcrumb_jsonld(request, crumbs),
        # pages filtrées : on évite l'indexation de milliers de combinaisons
        "noindex": flt.is_filtered,
    }
    # Requête fetch() du filtrage dynamique : on ne renvoie que la zone de résultats.
    if request.headers.get("X-Requested-With") == "fetch":
        return render(request, "catalog/_results.html", context)
    context["hero"] = _hero(flt, discipline, category)
    return render(request, "catalog/listing.html", context)


def _fill_guide(category):
    """Guide éditorial qui comble la dernière rangée incomplète de la grille."""
    guides = Guide.objects.filter(is_published=True).select_related("photo")
    if category:
        match = guides.filter(categories__in=category.descendant_ids() + [category.root.pk]).first()
        if match:
            return match
    return guides.filter(topic="gants").first() or guides.first()


def _hero(flt, discipline, category):
    """Bandeau d'en-tête : photo, chiffres clés et sous-catégories (discipline, type ou boutique)."""
    from django.db.models import Max, Min

    from core.models import HomeSettings

    base = flt.base_queryset()
    stats = Variant.objects.filter(product__in=base, is_active=True).aggregate(
        wmin=Min("weight_oz"), wmax=Max("weight_oz"), pmin=Min("price"))
    figures = [f"{base.count()} produits"]
    if stats["wmin"]:
        figures.append(f"{stats['wmin']}–{stats['wmax']} oz" if stats["wmax"] != stats["wmin"] else f"{stats['wmin']} oz")
    if stats["pmin"] is not None:
        figures.append("dès " + f"{stats['pmin']:.2f}".replace(".", ",") + " €")
    photo = None
    if discipline:
        photo = discipline.photo
    if photo is None:
        images = ProductImage.objects.filter(product__in=base).exclude(credit="Visuel Boxing Shop")
        photo = images.order_by("position", "id").first()
    if photo is None:
        home = HomeSettings.objects.select_related("hero_photo").first()
        photo = home.hero_photo if home else None
    # Sous-catégories défilables
    cat_ids = set(base.values_list("category_id", flat=True))
    subnav = []
    if discipline:
        for top in Category.objects.filter(parent__isnull=True).prefetch_related("children"):
            for c in [top, *top.children.all()]:
                if c.pk in cat_ids or (c is top and any(ch.pk in cat_ids for ch in top.children.all())):
                    subnav.append((c.name, f"{discipline.get_absolute_url()}{c.slug}/", category and category.pk == c.pk))
    else:
        parent = category.root if category else None
        if parent and not parent.children.exists():
            parent = None  # type sans sous-catégories : on propose les autres types
        pool = parent.children.all() if parent else Category.objects.filter(parent__isnull=True)
        if parent:
            subnav.append((f"Tout {parent.name.lower()}", parent.get_absolute_url(), category.pk == parent.pk))
        for c in pool:
            subnav.append((c.name, c.get_absolute_url(), bool(category and category.pk == c.pk)))
    index = f"{discipline.position + 1:02d} / Discipline" if discipline else ("Équipement" if category else "Boutique")
    return {"photo": photo, "figures": figures, "subnav": subnav, "index": index}


@require_GET
def shop(request):
    return _listing(request, title="Tout l'équipement", kicker="Boutique",
                    intro="Gants, protections, tenues et matériel de club : filtrez par discipline, poids, taille, "
                          "matière et niveau.",
                    crumbs=[("Boutique", None)])


@require_GET
def discipline_view(request, discipline_slug):
    discipline = get_object_or_404(Discipline, slug=discipline_slug)
    return _listing(request, title=discipline.name, intro=discipline.description, kicker="Discipline",
                    discipline=discipline, crumbs=[(discipline.name, None)], meta_obj=discipline)


@require_GET
def category_view(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    crumbs = [(category.parent.name, category.parent.get_absolute_url())] if category.parent_id else []
    return _listing(request, title=category.name, intro=category.description, kicker="Équipement",
                    category=category, crumbs=[*crumbs, (category.name, None)], meta_obj=category)


@require_GET
def discipline_category_view(request, discipline_slug, category_slug):
    discipline = get_object_or_404(Discipline, slug=discipline_slug)
    category = get_object_or_404(Category, slug=category_slug)
    return _listing(request, title=f"{category.name} · {discipline.name}", kicker=discipline.name,
                    discipline=discipline, category=category,
                    crumbs=[(discipline.name, discipline.get_absolute_url()), (category.name, None)],
                    meta_obj=category)


def _axis_values(variants):
    colors, seen = [], set()
    for v in variants:
        if v.color and v.color not in seen:
            seen.add(v.color)
            colors.append((v.color, v.color_hex))
    weights = sorted({v.weight_oz for v in variants if v.weight_oz})
    sizes = [s for s in Variant.SIZE_ORDER if any(v.size == s for v in variants)]
    return colors, weights, sizes


def _select_variant(variants, params):
    sku = params.get("sku")
    if sku:
        for v in variants:
            if v.sku == sku:
                return v
    color, weight, size = params.get("couleur"), params.get("poids"), params.get("taille")
    color = from_slug(color) or color  # ?couleur=bleu -> « Bleu »
    if color and not (weight or size):
        in_color = [v for v in variants if v.color == color]
        if in_color:
            return next((v for v in in_color if v.in_stock), in_color[0])
    if color or weight or size:
        for v in variants:
            if ((not color or v.color == color) and (not weight or str(v.weight_oz) == weight)
                    and (not size or v.size == size)):
                return v
    return next((v for v in variants if v.in_stock), variants[0] if variants else None)


@require_GET
def product_view(request, discipline_slug, category_slug, product_slug):
    product = get_object_or_404(
        Product.objects.active().select_related("discipline", "category__parent", "size_chart").prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.order_by("position", "id")),
            Prefetch("variants", queryset=Variant.objects.filter(is_active=True)),
        ),
        slug=product_slug,
    )
    canonical = product.get_absolute_url()
    if request.path != canonical:  # URL non canonique (ancienne discipline/catégorie) → 301
        query = request.GET.urlencode()
        return redirect(f"{canonical}?{query}" if query else canonical, permanent=True)

    variants = list(product.variants.all())
    if not variants:
        raise Http404("Produit sans déclinaison active")
    images = list(product.images.all())
    colors, weights, sizes = _axis_values(variants)
    selected = _select_variant(variants, request.GET)
    color_image = {img.color: i for i, img in reversed(list(enumerate(images))) if img.color}

    variant_data = [
        {"id": v.pk, "sku": v.sku, "color": v.color, "weight": v.weight_oz, "size": v.size,
         "price": str(v.price), "compare": str(v.compare_at_price) if v.on_sale else None, "stock": v.stock,
         "low": v.is_low_stock, "image": color_image.get(v.color), "color_slug": color_slug(v.color)}
        for v in variants
    ]
    chart = product.get_size_chart()
    chart_rows = list(chart.rows.all()) if chart else []
    guides = list(
        (Guide.objects.filter(is_published=True, products=product)
         | Guide.objects.filter(is_published=True, categories__in=[product.category_id, product.category.root.pk]))
        .distinct()
    )
    reviews = list(product.reviews.filter(is_published=True)[:10])
    rating = product.rating_summary()
    related = list(
        listing_queryset().filter(category=product.category).exclude(pk=product.pk).order_by("-sales_count")[:4]
    )
    related = decorate(related)
    crumbs = [
        (product.discipline.name, product.discipline.get_absolute_url()),
        (product.category.name, f"{product.discipline.get_absolute_url()}{product.category.slug}/"),
        (product.name, None),
    ]
    return render(request, "catalog/product.html", {
        "product": product, "images": images, "variants": variants, "selected": selected,
        "colors": colors, "weights": weights, "sizes": sizes, "variant_data": variant_data,
        "chart": chart, "chart_rows": chart_rows, "guides": guides,
        "chart_cols": chart_columns(chart_rows),
        "reviews": reviews, "rating": rating, "related": related, "crumbs": crumbs,
        "review_form": ReviewForm() if request.user.is_authenticated else None,
        "product_ld": product_jsonld(request, product, variants, images, rating, reviews),
        "breadcrumb_ld": breadcrumb_jsonld(request, crumbs),
    })


@login_required
@require_POST
@ratelimit("review", "5/h")
def review_create(request, product_id):
    product = get_object_or_404(Product.objects.active(), pk=product_id)
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.customer = request.user
        review.author_name = request.user.get_short_name() or request.user.first_name or "Client"
        review.save()
        messages.success(request, "Merci ! Votre avis sera publié après relecture par notre équipe.")
    else:
        messages.error(request, "Avis non enregistré : vérifiez la note et le texte.")
    return redirect(f"{product.get_absolute_url()}#avis")


@require_GET
def search_suggest(request):
    """Suggestions en direct pour le panneau de recherche : 6 produits au plus, données texte uniquement."""
    from django.db.models import Q
    from django.http import JsonResponse

    q = request.GET.get("q", "").strip()[:60]
    if len(q) < 2:
        return JsonResponse({"results": []})
    qs = (listing_queryset()
          .filter(Q(name__icontains=q) | Q(category__name__icontains=q) | Q(discipline__name__icontains=q))
          .order_by("-sales_count")[:6])
    results = []
    for p in qs:
        img = next(iter(p.images.all()), None)
        thumb = None
        if img and img.renditions:
            from django.core.files.storage import default_storage

            thumb = default_storage.url(img.renditions[str(min(int(w) for w in img.renditions))])
        results.append({
            "name": p.name, "url": p.get_absolute_url(), "category": p.category.name,
            "price": f"{p.min_price:.2f}".replace(".", ",") + " €" if p.min_price else "", "image": thumb,
        })
    response = JsonResponse({"results": results})
    response["Cache-Control"] = "public, max-age=60"
    return response


def chart_columns(rows):
    return {
        "weight": any(r.body_weight_min or r.body_weight_max for r in rows),
        "height": any(r.height_min or r.height_max for r in rows),
        "note": any(r.note for r in rows),
    }

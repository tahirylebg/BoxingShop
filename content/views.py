from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from catalog.filters import listing_queryset
from catalog.models import SizeChart
from catalog.views import chart_columns
from catalog.seo import breadcrumb_jsonld

from .models import Guide


@require_GET
def guide_list(request):
    from core.models import HomeSettings

    topics = dict(Guide.TOPICS)
    topic = request.GET.get("sujet", "")
    guides = Guide.objects.filter(is_published=True).select_related("photo")
    if topic in topics:
        guides = guides.filter(topic=topic)
    else:
        topic = ""
    guides = list(guides)
    return render(request, "content/guide_list.html", {
        "featured": guides[0] if guides else None, "guides": guides[1:], "topics": Guide.TOPICS,
        "topic": topic, "home": HomeSettings.objects.select_related("guides_photo").first(),
        "crumbs": [("Guides techniques", None)],
        "breadcrumb_ld": breadcrumb_jsonld(request, [("Guides techniques", None)]),
    })


@require_GET
def guide_detail(request, slug):
    guide = get_object_or_404(Guide.objects.filter(is_published=True).select_related("photo"), slug=slug)
    products = listing_queryset().filter(guides=guide).order_by("-sales_count")[:4]
    chart = SizeChart.objects.filter(category__in=guide.categories.all()).prefetch_related("rows").first()
    chart_rows = list(chart.rows.all()) if chart else []
    published = Guide.objects.filter(is_published=True).select_related("photo")
    crumbs = [("Guides techniques", "/guides/"), (guide.title, None)]
    article_ld = {
        "@context": "https://schema.org", "@type": "Article", "headline": guide.title,
        "description": guide.excerpt, "datePublished": guide.published_at.isoformat(),
        "dateModified": timezone.localdate(guide.updated_at).isoformat(),
        "author": {"@type": "Organization", "name": "Boxing Shop"},
        "publisher": {"@type": "Organization", "name": "Boxing Shop"},
    }
    return render(request, "content/guide_detail.html", {
        "guide": guide, "products": products, "article_ld": article_ld,
        "breadcrumb_ld": breadcrumb_jsonld(request, crumbs), "crumbs": crumbs,
        "chart": chart, "chart_rows": chart_rows, "chart_cols": chart_columns(chart_rows),
        "previous": published.filter(published_at__gt=guide.published_at).order_by("published_at").first(),
        "next": published.filter(published_at__lt=guide.published_at).order_by("-published_at").first(),
    })

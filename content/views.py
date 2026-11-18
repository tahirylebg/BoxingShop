from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from catalog.filters import listing_queryset
from catalog.seo import breadcrumb_jsonld

from .models import Guide


@require_GET
def guide_list(request):
    guides = Guide.objects.filter(is_published=True)
    return render(request, "content/guide_list.html", {
        "guides": guides, "crumbs": [("Guides techniques", None)],
        "breadcrumb_ld": breadcrumb_jsonld(request, [("Guides techniques", None)]),
    })


@require_GET
def guide_detail(request, slug):
    guide = get_object_or_404(Guide.objects.filter(is_published=True), slug=slug)
    products = listing_queryset().filter(guides=guide).order_by("-sales_count")[:8]
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
        "others": Guide.objects.filter(is_published=True).exclude(pk=guide.pk)[:3],
    })

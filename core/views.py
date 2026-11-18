from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET, require_POST

from catalog.filters import listing_queryset
from catalog.models import Category
from content.models import Guide

from .cache import cached
from .context_processors import CONSENT_COOKIE

LEGAL_PAGES = {
    "cgv": "Conditions générales de vente",
    "mentions-legales": "Mentions légales",
    "confidentialite": "Politique de confidentialité",
}
CONSENT_MAX_AGE = 60 * 60 * 24 * 182  # 6 mois (recommandation CNIL : 13 mois max.)


@require_GET
def home(request):
    def build():
        return {
            "best_sellers": list(listing_queryset().order_by("-sales_count")[:8]),
            "types": list(Category.objects.filter(parent__isnull=True)),
            "guides": list(Guide.objects.filter(is_published=True)[:3]),
        }

    data = cached("home", build)
    org_ld = {
        "@context": "https://schema.org", "@type": "Store", "name": "Boxing Shop", "url": settings.SITE_URL,
        "address": settings.SHOP["address"], "email": settings.SHOP["email"],
    }
    return render(request, "core/home.html", {**data, "org_ld": org_ld})


@require_GET
def legal(request, slug):
    if slug not in LEGAL_PAGES:
        raise Http404
    return render(request, f"core/legal/{slug}.html", {"title": LEGAL_PAGES[slug],
                                                       "crumbs": [(LEGAL_PAGES[slug], None)]})


@require_GET
def cookies(request):
    return render(request, "core/cookies.html", {"title": "Gestion des cookies",
                                                 "crumbs": [("Gestion des cookies", None)]})


@require_POST
def cookie_consent(request):
    choice = request.POST.get("choice")
    target = request.POST.get("next") or "/"
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        target = "/"
    response = redirect(target)
    if choice in ("accepted", "refused"):
        response.set_cookie(CONSENT_COOKIE, choice, max_age=CONSENT_MAX_AGE, samesite="Lax",
                            secure=request.is_secure(), httponly=True)
    return response


@require_GET
@cache_control(max_age=86400, public=True)
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /panier/",
        "Disallow: /commande/",
        "Disallow: /compte/",
        "Disallow: /*?*tri=",
        "Allow: /",
        f"Sitemap: {settings.SITE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)

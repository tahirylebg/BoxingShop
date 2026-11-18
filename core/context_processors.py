from django.conf import settings

from .cache import cached

CONSENT_COOKIE = "bs_consent"


def _nav():
    from catalog.models import Category, Discipline

    from .models import PageMeta, ShippingSettings

    return {
        "disciplines": list(Discipline.objects.all()),
        "categories": list(Category.objects.filter(parent__isnull=True)),
        "shipping": ShippingSettings.load(),
        "page_meta": {p.path: p for p in PageMeta.objects.all()},
    }


def site(request):
    nav = cached("nav", _nav)
    return {
        "SHOP": settings.SHOP,
        "SITE_URL": settings.SITE_URL,
        "nav_disciplines": nav["disciplines"],
        "nav_categories": nav["categories"],
        "shipping_settings": nav["shipping"],
        "page_meta": nav["page_meta"].get(request.path),
        "cookie_consent": request.COOKIES.get(CONSENT_COOKIE),
    }

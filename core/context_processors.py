from django.conf import settings

from .cache import cached

CONSENT_COOKIE = "bs_consent"


def _nav():
    from catalog.models import Category, Discipline

    from .models import PageMeta, ShippingSettings

    from catalog.models import Product

    from .models import HomeSettings

    disciplines = list(Discipline.objects.select_related("photo"))
    tops = list(Category.objects.filter(parent__isnull=True).prefetch_related("children"))
    pairs = set(Product.objects.filter(is_active=True).values_list("discipline_id", "category_id"))
    pairs |= set(Product.objects.filter(is_active=True).values_list("disciplines__id", "category_id"))
    mega = []
    for d in disciplines:
        cats = {c for disc, c in pairs if disc == d.pk}
        columns = []
        for top in tops:
            children = [c for c in top.children.all() if c.pk in cats]
            if top.pk in cats or children:
                columns.append({"category": top, "children": children})
        mega.append({"discipline": d, "columns": columns})
    return {
        "mega": mega,
        "campaign": HomeSettings.objects.select_related("campaign_photo").first(),
        "disciplines": disciplines,
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
        "nav_mega": nav["mega"],
        "campaign": nav["campaign"],
        "shipping_settings": nav["shipping"],
        "page_meta": nav["page_meta"].get(request.path),
        "cookie_consent": request.COOKIES.get(CONSENT_COOKIE),
    }

from django.conf import settings


def site(request):
    return {"SHOP": settings.SHOP, "SITE_URL": settings.SITE_URL}

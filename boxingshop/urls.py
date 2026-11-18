from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.static import serve
from django.views.decorators.cache import cache_page

from core.sitemaps import SITEMAPS
from core.views import robots_txt

handler404 = "core.views.error_404"
handler500 = "core.views.error_500"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("robots.txt", robots_txt),
    path("sitemap.xml", cache_page(3600)(sitemap), {"sitemaps": SITEMAPS},
         name="django.contrib.sitemaps.views.sitemap"),
    path("", include("core.urls")),
    path("guides/", include("content.urls")),
    path("panier/", include("cart.urls")),
    path("commande/", include("orders.urls")),
    path("compte/", include("accounts.urls")),
]
if settings.DEBUG or settings.SERVE_MEDIA:
    # En production, /media/ est servi par Nginx ; SERVE_MEDIA ne sert qu'aux audits locaux en mode prod.
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT})]

# Attrape-tout catalogue (/<discipline>/<type>/<produit>/) : TOUJOURS en dernier.
urlpatterns += [path("", include("catalog.urls"))]

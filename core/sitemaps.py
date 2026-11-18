from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from catalog.models import Category, Discipline, Product
from content.models import Guide


class StaticSitemap(Sitemap):
    priority = 0.6
    changefreq = "monthly"

    def items(self):
        return ["core:home", "catalog:shop", "content:guides"]

    def location(self, item):
        return reverse(item)


class DisciplineSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return Discipline.objects.all()


class CategorySitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return Category.objects.all()


class ProductSitemap(Sitemap):
    priority = 0.9
    changefreq = "weekly"

    def items(self):
        return Product.objects.active().select_related("discipline", "category")

    def lastmod(self, obj):
        return obj.updated_at


class GuideSitemap(Sitemap):
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        return Guide.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {
    "pages": StaticSitemap, "disciplines": DisciplineSitemap, "types": CategorySitemap,
    "produits": ProductSitemap, "guides": GuideSitemap,
}

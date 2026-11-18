from django.contrib import admin

from catalog.admin import SEO_FIELDSET

from .models import Guide


@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ("title", "published_at", "is_published", "reading_minutes")
    list_filter = ("is_published",)
    list_editable = ("is_published",)
    search_fields = ("title", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("products", "categories")
    fieldsets = (
        (None, {"fields": ("title", "slug", "kicker", "excerpt", "body", "reading_minutes", "is_published",
                           "published_at")}),
        ("Produits liés", {"fields": ("products", "categories")}),
        SEO_FIELDSET,
    )

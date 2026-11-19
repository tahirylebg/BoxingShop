from django.contrib import admin
from django.core.files.storage import default_storage
from django.utils.html import format_html

from .models import HomeSettings, PageMeta, Photo, ShippingSettings


class SingletonAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ShippingSettings)
class ShippingSettingsAdmin(SingletonAdmin):
    list_display = ("carrier_label", "flat_rate", "free_shipping_threshold")


@admin.register(HomeSettings)
class HomeSettingsAdmin(SingletonAdmin):
    list_display = ("__str__", "hero_title", "hero_photo")
    autocomplete_fields = ("hero_photo",)


@admin.register(PageMeta)
class PageMetaAdmin(admin.ModelAdmin):
    list_display = ("label", "path", "meta_title")
    search_fields = ("label", "path")


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("thumb", "title", "credit", "credit_source", "width", "height")
    search_fields = ("title", "alt", "credit")
    list_filter = ("credit_source",)
    readonly_fields = ("thumb", "width", "height")
    fields = ("thumb", "title", "image", "alt", "credit", "credit_source", "credit_url", "width", "height")

    @admin.display(description="aperçu")
    def thumb(self, obj):
        if not obj.renditions:
            return "—"
        smallest = obj.renditions[str(min(int(w) for w in obj.renditions))]
        return format_html('<img src="{}" alt="" class="bs-thumb">', default_storage.url(smallest))

from django.contrib import admin

from .models import PageMeta, ShippingSettings


@admin.register(ShippingSettings)
class ShippingSettingsAdmin(admin.ModelAdmin):
    list_display = ("carrier_label", "flat_rate", "free_shipping_threshold")

    def has_add_permission(self, request):
        return not ShippingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PageMeta)
class PageMetaAdmin(admin.ModelAdmin):
    list_display = ("label", "path", "meta_title")
    search_fields = ("label", "path")

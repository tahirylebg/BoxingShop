from django.contrib import admin

from .models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "value", "min_subtotal", "valid_from", "valid_until", "times_used",
                    "max_uses", "is_active")
    list_filter = ("is_active", "discount_type")
    list_editable = ("is_active",)
    search_fields = ("code", "description")
    readonly_fields = ("times_used",)

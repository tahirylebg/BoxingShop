from django.contrib import admin

from .models import Invoice, Order, OrderItem, StripeEvent


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "variant_label", "sku", "unit_price", "quantity", "line_total")
    fields = readonly_fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "created_at", "full_name", "email", "total", "status", "tracking_number")
    list_filter = ("status", "created_at")
    search_fields = ("number", "email", "last_name", "tracking_number")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "order", "issued_at")
    search_fields = ("number", "order__number")


@admin.register(StripeEvent)
class StripeEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "type", "received_at")
    search_fields = ("event_id",)

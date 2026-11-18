import csv
from datetime import datetime, time, timedelta

from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from . import emails
from .invoices import vat_breakdown
from .models import Invoice, Order, OrderItem, StripeEvent

PAID_STATUSES = [Order.Status.PAID, Order.Status.PREPARING, Order.Status.SHIPPED, Order.Status.DELIVERED]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "variant_label", "sku", "unit_price", "quantity", "line_total")
    fields = readonly_fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        previous = self.instance.status if self.instance.pk else None
        if status == Order.Status.SHIPPED and not cleaned.get("tracking_number"):
            self.add_error("tracking_number", "Le numéro de suivi est obligatoire pour passer la commande en « Expédiée ».")
        if previous == Order.Status.PENDING and status in PAID_STATUSES[1:]:
            self.add_error("status", "Une commande non payée ne peut pas être préparée ni expédiée.")
        if previous == Order.Status.CANCELLED and status != Order.Status.CANCELLED:
            self.add_error("status", "Une commande annulée ne peut pas être réactivée.")
        return cleaned


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    list_display = ("number", "created_at", "full_name", "email", "total_display", "status_badge", "tracking_number",
                    "stock_issue")
    list_filter = ("status", "stock_issue", ("created_at", admin.DateFieldListFilter), ("paid_at", admin.DateFieldListFilter))
    search_fields = ("number", "email", "last_name", "tracking_number", "items__sku")
    date_hierarchy = "created_at"
    inlines = [OrderItemInline]
    actions = ["mark_preparing", "mark_delivered", "export_csv"]
    list_per_page = 50
    save_on_top = True
    readonly_fields = ("number", "customer", "email", "created_at", "paid_at", "shipped_at", "delivered_at",
                       "subtotal", "club_discount", "promo_code", "promo_discount", "shipping_cost", "total",
                       "stripe_session_id", "stripe_payment_intent", "stock_issue", "invoice_link")
    fieldsets = (
        ("Suivi", {"fields": ("status", "carrier", "tracking_number", "tracking_url"),
                   "description": "Passer en « Expédiée » avec un n° de suivi envoie automatiquement un e-mail au client."}),
        ("Commande", {"fields": ("number", "customer", "email", "created_at", "paid_at", "shipped_at", "delivered_at",
                                 "invoice_link", "stock_issue")}),
        ("Livraison", {"fields": ("first_name", "last_name", "line1", "line2", "postal_code", "city", "country",
                                  "phone")}),
        ("Montants TTC", {"fields": ("subtotal", "club_discount", "promo_code", "promo_discount", "shipping_cost",
                                     "total")}),
        ("Stripe", {"fields": ("stripe_session_id", "stripe_payment_intent"), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        return False  # les commandes naissent du tunnel d'achat

    def has_delete_permission(self, request, obj=None):
        return False  # pièces comptables : on annule, on ne supprime pas

    @admin.display(description="total", ordering="total")
    def total_display(self, obj):
        return f"{obj.total} €"

    @admin.display(description="statut", ordering="status")
    def status_badge(self, obj):
        colors = {"pending": "#4a4945", "paid": "#B45309", "preparing": "#B45309", "shipped": "#0D0D0D",
                  "delivered": "#0D0D0D", "cancelled": "#C81E1E"}
        return format_html('<strong style="color:{}">{}</strong>', colors.get(obj.status, "#0D0D0D"),
                           obj.get_status_display())

    @admin.display(description="facture")
    def invoice_link(self, obj):
        invoice = getattr(obj, "invoice", None)
        if not invoice:
            return "—"
        url = reverse("orders:invoice", args=[obj.number, obj.access_token])
        return format_html('<a href="{}">{} (PDF)</a>', url, invoice.number)

    def save_model(self, request, obj, form, change):
        previous = Order.objects.get(pk=obj.pk).status if change else None
        now = timezone.now()
        if obj.status == Order.Status.SHIPPED and previous != Order.Status.SHIPPED:
            obj.shipped_at = obj.shipped_at or now
        if obj.status == Order.Status.DELIVERED and previous != Order.Status.DELIVERED:
            obj.delivered_at = obj.delivered_at or now
        super().save_model(request, obj, form, change)
        if obj.status == Order.Status.SHIPPED and previous != Order.Status.SHIPPED:
            emails.send_order_shipped(obj)
            messages.info(request, f"E-mail d'expédition envoyé à {obj.email}.")

    @admin.action(description="Passer en préparation (commandes payées)")
    def mark_preparing(self, request, queryset):
        n = queryset.filter(status=Order.Status.PAID).update(status=Order.Status.PREPARING)
        self.message_user(request, f"{n} commande(s) passée(s) en préparation.")

    @admin.action(description="Marquer comme livrées (commandes expédiées)")
    def mark_delivered(self, request, queryset):
        n = queryset.filter(status=Order.Status.SHIPPED).update(status=Order.Status.DELIVERED,
                                                                delivered_at=timezone.now())
        self.message_user(request, f"{n} commande(s) marquée(s) livrée(s).")

    @admin.action(description="Exporter la sélection (CSV comptable)")
    def export_csv(self, request, queryset):
        return accounting_csv(queryset, "selection")

    # --- Export comptable par période -------------------------------------------------------------
    def get_urls(self):
        custom = [path("export/", self.admin_site.admin_view(self.export_view), name="orders_order_export")]
        return custom + super().get_urls()

    def export_view(self, request):
        form = ExportForm(request.GET or None)
        if request.GET and form.is_valid():
            start, end = form.cleaned_data["start"], form.cleaned_data["end"]
            tz = timezone.get_current_timezone()
            qs = Order.objects.filter(
                status__in=PAID_STATUSES,
                paid_at__gte=timezone.make_aware(datetime.combine(start, time.min), tz),
                paid_at__lt=timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min), tz),
            )
            return accounting_csv(qs, f"{start:%Y%m%d}-{end:%Y%m%d}")
        context = {**self.admin_site.each_context(request), "title": "Export comptable CSV", "form": form,
                   "opts": self.model._meta}
        return TemplateResponse(request, "admin/orders/order/export.html", context)


class ExportForm(forms.Form):
    start = forms.DateField(label="Du", widget=forms.DateInput(attrs={"type": "date"}))
    end = forms.DateField(label="Au (inclus)", widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields["start"].initial = today.replace(day=1)
        self.fields["end"].initial = today

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("start") and cleaned.get("end") and cleaned["start"] > cleaned["end"]:
            raise forms.ValidationError("La date de début doit précéder la date de fin.")
        return cleaned


def _fr(amount):
    return f"{amount:.2f}".replace(".", ",")


def accounting_csv(queryset, suffix):
    """CSV pour tableur français : séparateur « ; », décimales à virgule, UTF-8 avec BOM."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="boxingshop-ventes-{suffix}.csv"'
    response.write("﻿")
    writer = csv.writer(response, delimiter=";")
    writer.writerow(["Date paiement", "N° commande", "N° facture", "Client", "E-mail", "Statut", "Code postal",
                     "Sous-total TTC", "Remise club", "Code promo", "Remise promo", "Livraison TTC", "Total HT",
                     "TVA", "Total TTC", "Paiement Stripe"])
    for o in queryset.select_related("invoice").order_by("paid_at", "created_at"):
        vat = vat_breakdown(o)
        invoice = getattr(o, "invoice", None)
        writer.writerow([
            timezone.localtime(o.paid_at).strftime("%d/%m/%Y %H:%M") if o.paid_at else "",
            o.number, invoice.number if invoice else "", o.full_name, o.email, o.get_status_display(),
            o.postal_code, _fr(o.subtotal), _fr(o.club_discount), o.promo_code, _fr(o.promo_discount),
            _fr(o.shipping_cost), _fr(vat["total_ht"]), _fr(vat["vat"]), _fr(o.total), o.stripe_payment_intent,
        ])
    return response


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "order", "issued_at", "download")
    search_fields = ("number", "order__number", "order__email")
    date_hierarchy = "issued_at"
    readonly_fields = ("order", "number", "issued_at", "pdf")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="PDF")
    def download(self, obj):
        url = reverse("orders:invoice", args=[obj.order.number, obj.order.access_token])
        return format_html('<a href="{}">Télécharger</a>', url)


@admin.register(StripeEvent)
class StripeEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "type", "received_at")
    search_fields = ("event_id",)
    readonly_fields = ("event_id", "type", "received_at")

    def has_add_permission(self, request):
        return False

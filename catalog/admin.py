from django.contrib import admin
from django.db.models import F
from django.utils.html import format_html

from .models import Category, Discipline, Product, ProductImage, Review, SizeChart, SizeChartRow, Variant

SEO_FIELDSET = ("Référencement (SEO)", {
    "fields": ("meta_title", "meta_description"),
    "description": "Laisser vide pour générer automatiquement le titre et la description.",
})


@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "slug", "position")
    list_editable = ("position",)
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = ((None, {"fields": ("name", "short_name", "slug", "tagline", "description", "position")}), SEO_FIELDSET)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "slug", "position")
    list_editable = ("position",)
    list_filter = ("parent",)
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = ((None, {"fields": ("name", "slug", "parent", "description", "position")}), SEO_FIELDSET)


class SizeChartRowInline(admin.TabularInline):
    model = SizeChartRow
    extra = 1


@admin.register(SizeChart)
class SizeChartAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "measure_label")
    search_fields = ("name",)
    inlines = [SizeChartRowInline]


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 1
    fields = ("sku", "color", "color_hex", "weight_oz", "size", "price", "compare_at_price", "stock",
              "low_stock_threshold", "is_active")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("preview", "image", "alt", "color", "position")
    readonly_fields = ("preview",)

    @admin.display(description="aperçu")
    def preview(self, obj):
        src = obj.renditions.get("360") if obj.pk and obj.renditions else None
        if not src:
            return "—"
        from django.core.files.storage import default_storage

        return format_html('<img src="{}" width="80" height="80" alt="" class="bs-thumb">', default_storage.url(src))


class LowStockFilter(admin.SimpleListFilter):
    title = "alerte stock"
    parameter_name = "stock_alerte"

    def lookups(self, request, model_admin):
        return [("bas", "Sous le seuil critique"), ("rupture", "En rupture")]

    def queryset(self, request, queryset):
        if self.value() == "bas":
            return queryset.filter(variants__is_active=True,
                                   variants__stock__lte=F("variants__low_stock_threshold")).distinct()
        if self.value() == "rupture":
            return queryset.filter(variants__is_active=True, variants__stock=0).distinct()
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "discipline", "category", "range_tier", "level", "variant_count", "stock_total",
                    "is_active", "is_featured", "sales_count")
    list_filter = ("is_active", "is_featured", LowStockFilter, "discipline", "category", "range_tier", "level",
                   "material")
    list_editable = ("is_active", "is_featured")
    search_fields = ("name", "slug", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("disciplines",)
    autocomplete_fields = ("size_chart",)
    inlines = [VariantInline, ProductImageInline]
    save_on_top = True
    fieldsets = (
        (None, {"fields": ("name", "slug", "discipline", "disciplines", "category", "is_active", "is_featured")}),
        ("Présentation", {"fields": ("short_description", "description")}),
        ("Spécifications techniques", {
            "fields": ("material", "level", "range_tier", "padding", "closure", "origin", "extra_specs", "size_chart")
        }),
        SEO_FIELDSET,
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("discipline", "category").prefetch_related("variants")

    @admin.display(description="SKU")
    def variant_count(self, obj):
        return len(obj.variants.all())

    @admin.display(description="stock")
    def stock_total(self, obj):
        variants = [v for v in obj.variants.all() if v.is_active]
        total = sum(v.stock for v in variants)
        low = any(v.stock <= v.low_stock_threshold for v in variants)
        return format_html('<span class="{}">{}</span>', "bs-low" if low else "", total)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.disciplines.add(form.instance.discipline)


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ("sku", "product", "color", "weight_oz", "size", "price", "stock", "low_stock_threshold",
                    "alert", "is_active")
    list_editable = ("stock", "low_stock_threshold", "price")
    list_filter = ("is_active", "product__category", "product__discipline")
    search_fields = ("sku", "product__name")
    list_select_related = ("product",)
    autocomplete_fields = ("product",)

    @admin.display(description="alerte", boolean=False)
    def alert(self, obj):
        if obj.stock == 0:
            return format_html('<strong class="bs-low">{}</strong>', "RUPTURE")
        if obj.stock <= obj.low_stock_threshold:
            return format_html('<strong class="bs-low">{}</strong>', "STOCK BAS")
        return "—"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "author_name", "rating", "title", "is_published", "created_at")
    list_filter = ("is_published", "rating")
    list_editable = ("is_published",)
    search_fields = ("title", "body", "product__name", "author_name")
    autocomplete_fields = ("product", "customer")
    actions = ["publish"]

    @admin.action(description="Publier les avis sélectionnés")
    def publish(self, request, queryset):
        queryset.update(is_published=True)

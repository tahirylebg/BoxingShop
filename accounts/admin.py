from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, ClubPriceTier, Customer


class AddressInline(admin.StackedInline):
    model = Address
    extra = 0


@admin.register(Customer)
class CustomerAdmin(UserAdmin):
    ordering = ("-date_joined",)
    list_display = ("email", "first_name", "last_name", "club_status", "club_name", "date_joined", "is_staff")
    list_filter = ("club_status", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name", "club_name")
    inlines = [AddressInline]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Identité", {"fields": ("first_name", "last_name", "phone")}),
        ("Statut Club / Coach", {"fields": ("club_status", "club_name", "club_siret", "club_message",
                                            "club_requested_at", "club_validated_at")}),
        ("Droits", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
                    "classes": ("collapse",)}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)
    readonly_fields = ("club_requested_at", "club_validated_at", "last_login", "date_joined")


@admin.register(ClubPriceTier)
class ClubPriceTierAdmin(admin.ModelAdmin):
    list_display = ("min_quantity", "discount_percent")

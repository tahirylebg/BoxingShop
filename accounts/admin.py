from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin

from orders.emails import send_club_status

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
    actions = ["approve_club", "reject_club"]

    @admin.action(description="Valider le statut Club / Coach (e-mail au client)")
    def approve_club(self, request, queryset):
        count = 0
        for customer in queryset.exclude(club_status=Customer.ClubStatus.APPROVED):
            customer.approve_club()
            customer.save(update_fields=["club_status", "club_validated_at"])
            send_club_status(customer)
            count += 1
        self.message_user(request, f"{count} compte(s) Club / Coach validé(s).", messages.SUCCESS)

    @admin.action(description="Refuser la demande Club / Coach (e-mail au client)")
    def reject_club(self, request, queryset):
        count = 0
        for customer in queryset.filter(club_status=Customer.ClubStatus.PENDING):
            customer.club_status = Customer.ClubStatus.REJECTED
            customer.save(update_fields=["club_status"])
            send_club_status(customer)
            count += 1
        self.message_user(request, f"{count} demande(s) refusée(s).", messages.WARNING)

    def save_model(self, request, obj, form, change):
        previous = Customer.objects.filter(pk=obj.pk).values_list("club_status", flat=True).first() if change else None
        if obj.club_status == Customer.ClubStatus.APPROVED and previous != Customer.ClubStatus.APPROVED:
            obj.approve_club()
        super().save_model(request, obj, form, change)
        if change and previous != obj.club_status and obj.club_status in (Customer.ClubStatus.APPROVED,
                                                                          Customer.ClubStatus.REJECTED):
            send_club_status(obj)


@admin.register(ClubPriceTier)
class ClubPriceTierAdmin(admin.ModelAdmin):
    list_display = ("min_quantity", "discount_percent")
    list_editable = ("discount_percent",)

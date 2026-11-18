import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from catalog.models import Review
from core.ratelimit import ratelimit
from orders.emails import _send_admin

from .forms import AddressForm, ClubRequestForm, DeleteAccountForm, LoginForm, ProfileForm, SignupForm
from .models import ClubPriceTier, Customer


@method_decorator(ratelimit("login", "5/m"), name="dispatch")
class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True


@method_decorator(ratelimit("pwreset", "5/h"), name="dispatch")
class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/emails/password_reset.txt"
    subject_template_name = "accounts/emails/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        messages.success(self.request, "Mot de passe modifié : vous pouvez vous connecter.")
        return super().form_valid(form)


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Vous êtes déconnecté.")
    return redirect("core:home")


@require_http_methods(["GET", "POST"])
@ratelimit("signup", "5/h")
def signup(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Bienvenue ! Votre compte est créé.")
        target = request.GET.get("next", "")
        if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()},
                                               require_https=request.is_secure()):
            target = "accounts:dashboard"
        return redirect(target)
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def dashboard(request):
    orders = request.user.orders.exclude(status="pending")[:3]
    return render(request, "accounts/dashboard.html", {"orders": orders, "section": "dashboard"})


@login_required
def orders(request):
    qs = request.user.orders.exclude(status="pending").select_related("invoice").prefetch_related("items")
    return render(request, "accounts/orders.html", {"orders": qs, "section": "orders"})


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profil mis à jour.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form, "section": "profile"})


@login_required
def addresses(request):
    return render(request, "accounts/addresses.html", {"addresses": request.user.addresses.all(),
                                                       "section": "addresses"})


@login_required
@require_http_methods(["GET", "POST"])
def address_edit(request, pk=None):
    address = get_object_or_404(request.user.addresses, pk=pk) if pk else None
    form = AddressForm(request.POST or None, instance=address,
                       initial=None if address else {"first_name": request.user.first_name,
                                                     "last_name": request.user.last_name})
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.customer = request.user
        if not request.user.addresses.exclude(pk=obj.pk).exists():
            obj.is_default = True
        obj.save()
        messages.success(request, "Adresse enregistrée.")
        return redirect("accounts:addresses")
    return render(request, "accounts/address_form.html", {
        "form": form, "address": address, "section": "addresses", "address_api_url": settings.ADDRESS_API_URL,
    })


@login_required
@require_POST
def address_delete(request, pk):
    get_object_or_404(request.user.addresses, pk=pk).delete()
    messages.success(request, "Adresse supprimée.")
    return redirect("accounts:addresses")


@login_required
@require_http_methods(["GET", "POST"])
def club_request(request):
    user = request.user
    form = ClubRequestForm(request.POST or None, instance=user)
    can_request = user.club_status in (Customer.ClubStatus.NONE, Customer.ClubStatus.REJECTED)
    if request.method == "POST" and can_request and form.is_valid():
        user = form.save(commit=False)
        user.club_status = Customer.ClubStatus.PENDING
        user.club_requested_at = timezone.now()
        user.save()
        _send_admin("Nouvelle demande Club / Coach",
                    f"{user.email} — {user.club_name} (SIRET {user.club_siret}).\n\n{user.club_message}\n\n"
                    f"Valider depuis l'admin : {settings.SITE_URL}/admin/accounts/customer/{user.pk}/change/")
        messages.success(request, "Demande envoyée : nous vous répondons sous 48 h ouvrées.")
        return redirect("accounts:club_request")
    return render(request, "accounts/club.html", {
        "form": form, "can_request": can_request, "tiers": ClubPriceTier.objects.all(), "section": "club",
    })


@login_required
def export_data(request):
    """RGPD — droit d'accès et de portabilité : export JSON de toutes les données du compte."""
    user = request.user
    data = {
        "exporte_le": timezone.now(),
        "compte": {
            "email": user.email, "prenom": user.first_name, "nom": user.last_name, "telephone": user.phone,
            "inscrit_le": user.date_joined, "derniere_connexion": user.last_login,
            "statut_club": user.get_club_status_display(), "club": user.club_name, "siret": user.club_siret,
        },
        "adresses": list(user.addresses.values("label", "first_name", "last_name", "line1", "line2",
                                               "postal_code", "city", "country", "phone", "is_default")),
        "commandes": [
            {
                "numero": o.number, "date": o.created_at, "statut": o.get_status_display(), "total": o.total,
                "livraison": f"{o.line1}, {o.postal_code} {o.city}",
                "articles": list(o.items.values("product_name", "variant_label", "sku", "quantity", "line_total")),
            }
            for o in user.orders.prefetch_related("items")
        ],
        "avis": list(user.reviews.values("product__name", "rating", "title", "body", "created_at")),
    }
    response = HttpResponse(json.dumps(data, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2),
                            content_type="application/json; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="mes-donnees-boxing-shop.json"'
    return response


@login_required
@require_http_methods(["GET", "POST"])
def delete_account(request):
    """RGPD — droit à l'effacement. Les commandes sont conservées 10 ans (obligation comptable),
    détachées du compte ; adresses, paniers et compte sont supprimés, les avis anonymisés."""
    form = DeleteAccountForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = request.user
        with transaction.atomic():
            Review.objects.filter(customer=user).update(customer=None, author_name="Client anonyme")
            user.orders.update(customer=None)
            user.delete()
        logout(request)
        messages.success(request, "Votre compte et vos données personnelles ont été supprimés.")
        return redirect("core:home")
    return render(request, "accounts/delete.html", {"form": form, "section": "privacy"})


@login_required
def privacy(request):
    return render(request, "accounts/privacy.html", {"section": "privacy"})

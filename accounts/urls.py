from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("connexion/", views.LoginView.as_view(), name="login"),
    path("deconnexion/", views.logout_view, name="logout"),
    path("inscription/", views.signup, name="signup"),
    path("mot-de-passe/", views.PasswordResetView.as_view(), name="password_reset"),
    path("mot-de-passe/envoye/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html"), name="password_reset_done"),
    path("mot-de-passe/<uidb64>/<token>/", views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("commandes/", views.orders, name="orders"),
    path("profil/", views.profile, name="profile"),
    path("adresses/", views.addresses, name="addresses"),
    path("adresses/nouvelle/", views.address_edit, name="address_add"),
    path("adresses/<int:pk>/", views.address_edit, name="address_edit"),
    path("adresses/<int:pk>/supprimer/", views.address_delete, name="address_delete"),
    path("club/", views.club_request, name="club_request"),
    path("donnees/", views.privacy, name="privacy"),
    path("donnees/export.json", views.export_data, name="export"),
    path("donnees/supprimer/", views.delete_account, name="delete"),
]

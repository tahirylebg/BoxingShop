from django.apps import AppConfig
from django.contrib.admin import apps as admin_apps


class CoreConfig(AppConfig):
    default = True
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Paramètres boutique"


class BoxingAdminConfig(admin_apps.AdminConfig):
    """Remplace le site admin par défaut par le back-office habillé Boxing Shop."""

    default = False
    default_site = "core.admin_site.BoxingAdminSite"

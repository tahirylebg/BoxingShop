from django.contrib import admin


class BoxingAdminSite(admin.AdminSite):
    site_header = "Boxing Shop — Back-office"
    site_title = "Boxing Shop admin"
    index_title = "Tableau de bord"

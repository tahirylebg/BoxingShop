from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("informations/<slug:slug>/", views.legal, name="legal"),
    path("cookies/", views.cookies, name="cookies"),
    path("cookies/consentement/", views.cookie_consent, name="cookie_consent"),
]

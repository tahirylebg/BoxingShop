from django.urls import path

from . import views

app_name = "orders"
urlpatterns = [
    path("", views.checkout, name="checkout"),
    path("merci/", views.success, name="success"),
    path("suivi/", views.track, name="track"),
    path("webhook/stripe/", views.stripe_webhook, name="stripe_webhook"),
    path("<str:number>/<uuid:token>/", views.detail, name="detail"),
    path("<str:number>/<uuid:token>/facture.pdf", views.invoice_pdf, name="invoice"),
]

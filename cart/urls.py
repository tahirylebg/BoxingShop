from django.urls import path

from . import views

app_name = "cart"
urlpatterns = [
    path("", views.detail, name="detail"),
    path("tiroir/", views.drawer, name="drawer"),
    path("ajouter/", views.add, name="add"),
    path("ligne/<int:item_id>/", views.update, name="update"),
    path("code-promo/", views.apply_promo, name="promo"),
]

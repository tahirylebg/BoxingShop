from django.urls import path

from core.stub import coming_soon

app_name = "cart"
urlpatterns = [
    path("", coming_soon, name="detail"),
    path("tiroir/", coming_soon, name="drawer"),
    path("ajouter/", coming_soon, name="add"),
]

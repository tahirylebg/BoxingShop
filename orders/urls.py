from django.urls import path

from core.stub import coming_soon

app_name = "orders"
urlpatterns = [
    path("suivi/", coming_soon, name="track"),
]

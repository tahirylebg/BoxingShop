from django.urls import path

from core.stub import coming_soon

app_name = "accounts"
urlpatterns = [
    path("", coming_soon, name="dashboard"),
    path("connexion/", coming_soon, name="login"),
    path("club/", coming_soon, name="club_request"),
]

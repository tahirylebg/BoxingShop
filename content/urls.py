from django.urls import path

from . import views

app_name = "content"
urlpatterns = [
    path("", views.guide_list, name="guides"),
    path("<slug:slug>/", views.guide_detail, name="guide"),
]

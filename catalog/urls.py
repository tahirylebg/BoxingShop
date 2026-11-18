from django.urls import path

from . import views

app_name = "catalog"

# Les routes « /<discipline>/… » sont incluses en DERNIER dans boxingshop/urls.py (attrape-tout).
urlpatterns = [
    path("boutique/", views.shop, name="shop"),
    path("equipement/<slug:category_slug>/", views.category_view, name="category"),
    path("avis/<int:product_id>/", views.review_create, name="review_create"),
    path("<slug:discipline_slug>/", views.discipline_view, name="discipline"),
    path("<slug:discipline_slug>/<slug:category_slug>/", views.discipline_category_view,
         name="discipline_category"),
    path("<slug:discipline_slug>/<slug:category_slug>/<slug:product_slug>/", views.product_view, name="product"),
]

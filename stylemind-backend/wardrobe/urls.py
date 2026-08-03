from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("wardrobe/upload/", views.upload_item, name="upload_item"),
    path("wardrobe/", views.list_wardrobe, name="list_wardrobe"),
    path("recommend/", views.recommend, name="recommend"),
]
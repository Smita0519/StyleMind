from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("wardrobe/", views.list_wardrobe, name="list_wardrobe"),
    path("wardrobe/upload/", views.upload_item, name="upload_item"),
    path("recommend/", views.recommend, name="recommend"),
    path("me/", views.me, name="me"),
    path("wardrobe/<int:item_id>/", views.delete_item, name="delete_item"),
    path("wardrobe/<int:item_id>/favorite/", views.toggle_favorite, name="toggle_favorite"),
    path("outfits/", views.outfits, name="outfits"),
    path("outfits/<int:outfit_id>/", views.delete_outfit, name="delete_outfit"),
    path("health/", views.health, name="health"),
    path("chat/sessions/", views.chat_sessions, name="chat_sessions"),
    path("chat/sessions/<int:session_id>/", views.chat_session_detail, name="chat_session_detail"),
    path("chat/", views.chat, name="chat"),
    # ===================== CHANGE START =====================
    path("tryon/", views.start_tryon, name="start_tryon"),
    path("tryon/<int:tryon_id>/cancel/", views.cancel_tryon, name="cancel_tryon"),
    path("tryon/<int:tryon_id>/", views.tryon_status, name="tryon_status"),
    # ===================== CHANGE END =====================
]
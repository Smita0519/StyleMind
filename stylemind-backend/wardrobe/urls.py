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
    # ===================== CHANGE START =====================
    # FIXED — this route was completely missing, even though the view
    # function for it (chat_sessions) already existed in views.py
    path("chat/sessions/", views.chat_sessions, name="chat_sessions"),
    # ===================== CHANGE END =====================
    path("chat/sessions/<int:session_id>/", views.chat_session_detail, name="chat_session_detail"),
    path("chat/", views.chat, name="chat"),
]
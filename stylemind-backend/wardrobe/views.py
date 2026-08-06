from io import BytesIO
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile

from .models import Profile, WardrobeItem, Outfit,ChatMessage,ChatSession
from .serializers import SignupSerializer, ProfileSerializer, WardrobeItemSerializer, OutfitSerializer,ChatSessionSerializer
from src.predict import predict            # the ML classification pipeline (category/texture/season/colors)
from .weather import resolve_temperature
from src.recommend.recommend import get_recommendations  # the outfit-matching algorithm

from .chatbot import get_stylist_reply


# ────────────────────────────────────────────────
# AUTH
# ────────────────────────────────────────────────

# POST /api/signup/ — creates a new account
@api_view(["POST"])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()  # creates both the User and Profile rows
        return Response({"message": "User created"}, status=201)
    return Response(serializer.errors, status=400)


# ===================== CHANGE START =====================
# GET /api/me/ — fetch profile. PATCH /api/me/ — update display_name and/or profile_picture.
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def me(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"display_name": request.user.username, "email": request.user.email},
    )
    if request.method == "PATCH":
        # ===================== CHANGE START =====================
        # NEW — explicit "remove photo" support. A plain empty value in
        # multipart form data doesn't reliably tell DRF's ImageField to
        # clear itself, so the frontend sends a dedicated remove_picture
        # flag instead, handled directly here before the normal serializer
        # update runs.
        if request.data.get("remove_picture") == "true":
            if profile.profile_picture:
                profile.profile_picture.delete(save=False)  # deletes the actual file from disk
            profile.profile_picture = None
            profile.save()
        # ===================== CHANGE END =====================

        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ProfileSerializer(profile).data)
        return Response(serializer.errors, status=400)
    return Response(ProfileSerializer(profile).data)
# ===================== CHANGE END =====================


# ────────────────────────────────────────────────
# WARDROBE
# ────────────────────────────────────────────────

# GET /api/wardrobe/ — lists only the logged-in user's own items
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_wardrobe(request):
    items = WardrobeItem.objects.filter(owner=request.user).order_by("-uploaded_at")  # newest first
    return Response(WardrobeItemSerializer(items, many=True).data)


# POST /api/wardrobe/upload/ — uploads a photo and runs it through the ML pipeline
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])  # required for handling file uploads (not plain JSON)
def upload_item(request):
    image_file = request.FILES.get("image")
    if not image_file:
        return Response({"error": "No image provided"}, status=400)

    # Save the raw item first with placeholder values — we need item.image.path
    # to exist on disk before predict() can run on the actual file
    item = WardrobeItem.objects.create(
        owner=request.user,
        image=image_file,
        category="", category_confidence=0,
        texture="", texture_confidence=0,
        season="", season_confidence=0,
        season_probs={}, dominant_colors=[], mask_found=False,
    )

    # ===================== CHANGE START =====================
    # Changed: previously just `result = predict(item.image.path)`.
    # return_segmentation=True also gives us `seg`, which contains the
    # actual processed (background-removed/letterboxed) image, so we can
    # save it instead of discarding it after classification.
    result, seg = predict(item.image.path, return_segmentation=True)
    # ===================== CHANGE END =====================

    # Fill in the real classification results now that we have them
    item.category = result["category"]
    item.category_confidence = result["category_confidence"]
    item.texture = result["texture"]
    item.texture_confidence = result["texture_confidence"]
    item.season = result["season"]
    item.season_confidence = result["season_confidence"]
    item.season_probs = result["season_probs"]
    item.dominant_colors = result["dominant_colors"]
    item.mask_found = result["mask_found"]

    # ===================== CHANGE START =====================
    # New: save the processed image (a PIL Image object) into the
    # processed_image field. BytesIO acts as an in-memory "file" so we
    # don't need to write a temp file to disk first.
    buffer = BytesIO()
    seg["final"].save(buffer, format="PNG")
    filename = item.image.name.split("/")[-1]
    item.processed_image.save(f"processed_{filename}.png", ContentFile(buffer.getvalue()), save=False)
    # ===================== CHANGE END =====================

    item.save()  # writes everything (classification + processed image) to the database
    return Response(WardrobeItemSerializer(item).data, status=201)


# ===================== CHANGE START =====================
# New endpoint: DELETE /api/wardrobe/<item_id>/ — removes one item
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_item(request, item_id):
    # get_object_or_404 with owner=request.user filter means: if the item
    # doesn't exist OR belongs to someone else, return a 404 either way
    # (never reveal "this item exists but isn't yours")
    item = get_object_or_404(WardrobeItem, id=item_id, owner=request.user)
    item.delete()
    return Response(status=204)  # 204 = success, no content to return


# New endpoint: PATCH /api/wardrobe/<item_id>/favorite/ — toggles/sets favorite
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def toggle_favorite(request, item_id):
    item = get_object_or_404(WardrobeItem, id=item_id, owner=request.user)
    # If the frontend sends a specific true/false, use that; otherwise flip
    # whatever the current value is
    item.favorite = request.data.get("favorite", not item.favorite)
    item.save()
    return Response(WardrobeItemSerializer(item).data)
# ===================== CHANGE END =====================


# ────────────────────────────────────────────────
# RECOMMENDATIONS
# ────────────────────────────────────────────────

# GET /api/recommend/?city=...&lat=...&lon=...&temp_c=...&intent=...&style_preference=...&top_k=...
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommend(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    manual_temp = request.GET.get("temp_c")

    # ===================== CHANGE START =====================
    # CHANGED — now goes through the shared resolve_temperature() helper,
    # which also accepts lat/lon (GPS) as a middle priority between a
    # typed city and the manual slider value.
    try:
        temp_c, weather_info = resolve_temperature(lat=lat, lon=lon, manual_temp=manual_temp)    
    except ValueError as e:
        return Response({"error": str(e)}, status=400)
    # ===================== CHANGE END =====================

    intent = request.GET.get("intent")
    style_preference = request.GET.get("style_preference", "safe")
    top_k = int(request.GET.get("top_k", 3))

    items = WardrobeItem.objects.filter(owner=request.user)
    wardrobe = [WardrobeItemSerializer(i).data for i in items]
    results = get_recommendations(wardrobe, temp_c=temp_c, intent=intent, top_k=top_k, style_preference=style_preference)

    return Response({"weather": weather_info, "recommendations": results})


# ===================== CHANGE START =====================
# New endpoint: GET/POST /api/outfits/ — list saved outfits, or save a new one
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def outfits(request):
    if request.method == "GET":
        # Return only this user's saved outfits, most recent first
        saved = Outfit.objects.filter(owner=request.user).order_by("-saved_at")
        return Response(OutfitSerializer(saved, many=True).data)

    # POST — saving a new outfit.
    # Security check: before trusting the submitted top/bottom/jacket IDs,
    # confirm each one actually belongs to the logged-in user. Without
    # this, someone could submit another user's item ID and "save" an
    # outfit using clothes that aren't theirs.
    for field in ["top", "bottom", "jacket"]:
        item_id = request.data.get(field)
        if item_id:
            get_object_or_404(WardrobeItem, id=item_id, owner=request.user)

    serializer = OutfitSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(owner=request.user)  # owner is set here, not trusted from the request body
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)
# ===================== CHANGE END =====================

# ────────────────────────────────────────────────
# Outfit
# ────────────────────────────────────────────────

# ===================== CHANGE START =====================
# New endpoint: DELETE /api/outfits/<outfit_id>/ — removes one saved outfit.
# Deleting an Outfit does NOT delete the underlying WardrobeItems it
# references — it only removes the "these items go together" record.
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_outfit(request, outfit_id):
    outfit = get_object_or_404(Outfit, id=outfit_id, owner=request.user)
    outfit.delete()
    return Response(status=204)
# ===================== CHANGE END =====================

# ===================== CHANGE START =====================
# New — replaces the entire chat-proxy Node server. Gemini is now called
# directly from Django, with real wardrobe/weather/preference data.

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    if request.method == "GET":
        # ===================== CHANGE START =====================
        # FIXED — was returning ALL of a user's messages ever, ignoring
        # sessions entirely. Now requires and filters by session id.
        session_id = request.GET.get("session")
        if not session_id:
            return Response({"error": "session query param is required"}, status=400)
        session = get_object_or_404(ChatSession, id=session_id, owner=request.user)
        messages = ChatMessage.objects.filter(session=session)
        # ===================== CHANGE END =====================
        data = [
            {"id": m.id, "role": m.role, "text": m.text, "segments": m.segments, "timestamp": m.created_at}
            for m in messages
        ]
        return Response(data)

    message = request.data.get("message", "").strip()
    # ===================== CHANGE START =====================
    # FIXED — session is now required and actually used
    session_id = request.data.get("session")
    lat = request.data.get("lat")
    lon = request.data.get("lon")
    if not message:
        return Response({"error": "Message is required"}, status=400)
    if not session_id:
        return Response({"error": "session is required"}, status=400)
    session = get_object_or_404(ChatSession, id=session_id, owner=request.user)
    # ===================== CHANGE END =====================

    ChatMessage.objects.create(owner=request.user, session=session, role="user", text=message)

    try:
        reply_text, segments = get_stylist_reply(request.user, message, session=session, lat=lat, lon=lon)
    except Exception as e:
        return Response({"error": f"Chat failed: {str(e)}"}, status=500)

    ChatMessage.objects.create(owner=request.user, session=session, role="assistant", text=reply_text, segments=segments)

    # ===================== CHANGE START =====================
    # NEW — auto-title the session from the first message, and bump
    # updated_at so it sorts to the top of the sidebar
    if not session.title:
        session.title = message[:40] + ("…" if len(message) > 40 else "")
    session.save()
    # ===================== CHANGE END =====================

    return Response({"segments": segments})

# ===================== CHANGE START =====================
# New — list this user's chat sessions (for the sidebar), or start a
# brand new empty one (the "New Chat" button)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def chat_sessions(request):
    if request.method == "GET":
        sessions = ChatSession.objects.filter(owner=request.user)
        return Response(ChatSessionSerializer(sessions, many=True).data)

    # POST — create a new, empty session and return it immediately
    session = ChatSession.objects.create(owner=request.user, title="")
    return Response(ChatSessionSerializer(session).data, status=201)
# ===================== CHANGE END =====================

# ===================== CHANGE START =====================
# New endpoint: PATCH/DELETE /api/chat/sessions/<id>/ — rename or delete
# one specific conversation. Deleting a session also deletes all its
# messages automatically (ChatMessage.session has on_delete=CASCADE).
@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def chat_session_detail(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, owner=request.user)

    if request.method == "DELETE":
        session.delete()
        return Response(status=204)

    # PATCH — rename
    new_title = request.data.get("title", "").strip()
    if not new_title:
        return Response({"error": "Title cannot be empty"}, status=400)
    session.title = new_title
    session.save(update_fields=["title"])
    return Response(ChatSessionSerializer(session).data)
# ===================== CHANGE END =====================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    if request.method == "GET":
        # ===================== CHANGE START =====================
        # CHANGED — now requires a session id, and only returns THAT
        # session's messages, not everything the user has ever sent
        session_id = request.GET.get("session")
        if not session_id:
            return Response({"error": "session query param is required"}, status=400)
        session = get_object_or_404(ChatSession, id=session_id, owner=request.user)
        messages = ChatMessage.objects.filter(session=session)
        # ===================== CHANGE END =====================
        data = [
            {"id": m.id, "role": m.role, "text": m.text, "segments": m.segments, "timestamp": m.created_at}
            for m in messages
        ]
        return Response(data)

    # POST — send a new message within a specific session
    message = request.data.get("message", "").strip()
    # ===================== CHANGE START =====================
    # CHANGED — city removed, session is now required
    session_id = request.data.get("session")
    lat = request.data.get("lat")
    lon = request.data.get("lon")
    if not message:
        return Response({"error": "Message is required"}, status=400)
    if not session_id:
        return Response({"error": "session is required"}, status=400)
    session = get_object_or_404(ChatSession, id=session_id, owner=request.user)
    # ===================== CHANGE END =====================

    ChatMessage.objects.create(owner=request.user, session=session, role="user", text=message)

    try:
        # CHANGED — pass session through so history stays scoped to it, and city dropped
        reply_text, segments = get_stylist_reply(request.user, message, session=session, lat=lat, lon=lon)
    except Exception as e:
        return Response({"error": f"Chat failed: {str(e)}"}, status=500)

    ChatMessage.objects.create(owner=request.user, session=session, role="assistant", text=reply_text, segments=segments)

    # ===================== CHANGE START =====================
    # New — auto-title the session from the first message, and bump
    # updated_at so it sorts to the top of the sidebar
    if not session.title:
        session.title = message[:40] + ("…" if len(message) > 40 else "")
    session.save()  # save() alone bumps updated_at thanks to auto_now=True
    # ===================== CHANGE END =====================

    return Response({"segments": segments})
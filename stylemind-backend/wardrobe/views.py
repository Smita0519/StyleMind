# wardrobe/views.py
import time
import threading
from io import BytesIO
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny  # AllowAny ADDED — needed by the new health() endpoint below
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.db import connections  # NEW — used to close DB connections cleanly inside background threads

from .models import Profile, WardrobeItem, Outfit, ChatMessage, ChatSession
from .serializers import SignupSerializer, ProfileSerializer, WardrobeItemSerializer, OutfitSerializer, ChatSessionSerializer
from src.predict import predict            # the ML classification pipeline (category/texture/season/colors)
from .weather import resolve_temperature, get_rain_nudge  # CHANGED — merged what used to be two separate import lines
from src.recommend.recommend import get_recommendations   # the outfit-matching algorithm

from .chatbot import get_stylist_reply

# NEW — set once, when this module is first loaded (i.e. at process
# start). Lets the frontend detect "the backend restarted since I last
# checked" by comparing this value over time via GET /api/health/.
SERVER_STARTED_AT = time.time()


# ────────────────────────────────────────────────
# HEALTH
# ────────────────────────────────────────────────

# GET /api/health/ — lets the frontend detect a backend restart
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"started_at": SERVER_STARTED_AT})


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
        # Explicit "remove photo" support. A plain empty value in
        # multipart form data doesn't reliably tell DRF's ImageField to
        # clear itself, so the frontend sends a dedicated remove_picture
        # flag instead, handled directly here before the normal serializer
        # update runs.
        if request.data.get("remove_picture") == "true":
            if profile.profile_picture:
                profile.profile_picture.delete(save=False)  # deletes the actual file from disk
            profile.profile_picture = None
            profile.save()

        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ProfileSerializer(profile).data)
        return Response(serializer.errors, status=400)
    return Response(ProfileSerializer(profile).data)


# ────────────────────────────────────────────────
# WARDROBE
# ────────────────────────────────────────────────

# GET /api/wardrobe/ — lists only the logged-in user's own items
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_wardrobe(request):
    items = WardrobeItem.objects.filter(owner=request.user).order_by("-uploaded_at")  # newest first
    return Response(WardrobeItemSerializer(items, many=True).data)


# ===================== CHANGE START =====================
# NEW — runs the actual ML pipeline (YOLO segmentation, classification,
# color extraction) in a background thread, so upload_item can return to
# the browser almost immediately instead of blocking for however long
# that pipeline takes.
def _process_item_async(item_id):
    try:
        item = WardrobeItem.objects.get(id=item_id)
        result, seg = predict(item.image.path, return_segmentation=True)

        item.category = result["category"]
        item.category_confidence = result["category_confidence"]
        item.texture = result["texture"]
        item.texture_confidence = result["texture_confidence"]
        item.season = result["season"]
        item.season_confidence = result["season_confidence"]
        item.season_probs = result["season_probs"]
        item.dominant_colors = result["dominant_colors"]
        item.mask_found = result["mask_found"]

        buffer = BytesIO()
        seg["final"].save(buffer, format="PNG")
        filename = item.image.name.split("/")[-1]
        item.processed_image.save(f"processed_{filename}.png", ContentFile(buffer.getvalue()), save=False)

        item.status = "done"
        item.save()
    except Exception as e:
        print(f"Background processing failed for item {item_id}: {e}")
        try:
            WardrobeItem.objects.filter(id=item_id).update(status="failed")
        except Exception:
            pass
    finally:
        # Each thread opens its own DB connection — close it explicitly so
        # connections don't pile up across repeated uploads
        connections.close_all()


# POST /api/wardrobe/upload/ — uploads a photo, returns immediately, and
# runs classification in the background (see _process_item_async above)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload_item(request):
    image_file = request.FILES.get("image")
    if not image_file:
        return Response({"error": "No image provided"}, status=400)

    # Created immediately with placeholder values and status="processing" —
    # the frontend shows this right away, then polls until it flips to "done"
    item = WardrobeItem.objects.create(
        owner=request.user,
        image=image_file,
        category="", category_confidence=0,
        texture="", texture_confidence=0,
        season="", season_confidence=0,
        season_probs={}, dominant_colors=[], mask_found=False,
        status="processing",
    )

    thread = threading.Thread(target=_process_item_async, args=(item.id,), daemon=True)
    thread.start()

    return Response(WardrobeItemSerializer(item).data, status=202)  # 202 Accepted — processing isn't finished yet
# ===================== CHANGE END =====================


# DELETE /api/wardrobe/<item_id>/ — removes one item
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_item(request, item_id):
    # get_object_or_404 with owner=request.user filter means: if the item
    # doesn't exist OR belongs to someone else, return a 404 either way
    # (never reveal "this item exists but isn't yours")
    item = get_object_or_404(WardrobeItem, id=item_id, owner=request.user)
    item.delete()
    return Response(status=204)  # 204 = success, no content to return


# PATCH /api/wardrobe/<item_id>/favorite/ — toggles/sets favorite
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def toggle_favorite(request, item_id):
    item = get_object_or_404(WardrobeItem, id=item_id, owner=request.user)
    # If the frontend sends a specific true/false, use that; otherwise flip
    # whatever the current value is
    item.favorite = request.data.get("favorite", not item.favorite)
    item.save()
    return Response(WardrobeItemSerializer(item).data)


# ────────────────────────────────────────────────
# RECOMMENDATIONS
# ────────────────────────────────────────────────

# GET /api/recommend/?lat=...&lon=...&temp_c=...&intent=...&style_preference=...&top_k=...
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommend(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    manual_temp = request.GET.get("temp_c")

    # Goes through the shared resolve_temperature() helper, which accepts
    # lat/lon (GPS) as a middle priority between a typed city and the
    # manual slider value.
    try:
        temp_c, weather_info = resolve_temperature(lat=lat, lon=lon, manual_temp=manual_temp)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    intent = request.GET.get("intent")
    style_preference = request.GET.get("style_preference", "safe")
    top_k = int(request.GET.get("top_k", 3))

    # ===================== CHANGE START =====================
    # CHANGED — added .order_by("id") so the wardrobe comes back in the
    # SAME order every time. Without it, when multiple outfits are tied
    # in score, which one "wins" as the top pick could differ between
    # separate requests purely due to unordered row order — not an
    # actual disagreement in the scoring logic itself.
    items = WardrobeItem.objects.filter(owner=request.user).order_by("id")
    # ===================== CHANGE END =====================
    wardrobe = [WardrobeItemSerializer(i).data for i in items]
    results = get_recommendations(wardrobe, temp_c=temp_c, intent=intent, top_k=top_k, style_preference=style_preference)

    rain_nudge = get_rain_nudge(weather_info)

    return Response({
        "weather": weather_info,
        "recommendations": results,
        # `results` already contains the full ranked pool (up to
        # browse_pool_size, default 15), not just top_k. initial_count tells
        # the frontend how many to show upfront; the rest is already here
        # for "browse more" with zero extra requests or re-scoring.
        "initial_count": top_k,
        "rain_nudge": rain_nudge,
    })


# GET/POST /api/outfits/ — list saved outfits, or save a new one
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


# DELETE /api/outfits/<outfit_id>/ — removes one saved outfit.
# Deleting an Outfit does NOT delete the underlying WardrobeItems it
# references — it only removes the "these items go together" record.
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_outfit(request, outfit_id):
    outfit = get_object_or_404(Outfit, id=outfit_id, owner=request.user)
    outfit.delete()
    return Response(status=204)


# ────────────────────────────────────────────────
# CHATBOT
# ────────────────────────────────────────────────
# Gemini is called directly from Django (see chatbot.py), with real
# wardrobe/weather/preference data pulled from the database — this
# replaces the old standalone chat-proxy Node server entirely.

# ===================== CHANGE START =====================
# CHANGED — this file previously had `chat()` defined TWICE (Python
# silently keeps only the last one, making the first a dead duplicate).
# Consolidated into a single, correct version here.
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    if request.method == "GET":
        # Requires a session id, and only returns THAT session's
        # messages, not everything the user has ever sent
        session_id = request.GET.get("session")
        if not session_id:
            return Response({"error": "session query param is required"}, status=400)
        session = get_object_or_404(ChatSession, id=session_id, owner=request.user)
        messages = ChatMessage.objects.filter(session=session)
        data = [
            {"id": m.id, "role": m.role, "text": m.text, "segments": m.segments, "timestamp": m.created_at}
            for m in messages
        ]
        return Response(data)

    # POST — send a new message within a specific session
    message = request.data.get("message", "").strip()
    session_id = request.data.get("session")
    lat = request.data.get("lat")
    lon = request.data.get("lon")
    if not message:
        return Response({"error": "Message is required"}, status=400)
    if not session_id:
        return Response({"error": "session is required"}, status=400)
    session = get_object_or_404(ChatSession, id=session_id, owner=request.user)

    ChatMessage.objects.create(owner=request.user, session=session, role="user", text=message)

    try:
        reply_text, segments = get_stylist_reply(request.user, message, session=session, lat=lat, lon=lon)
    except Exception as e:
        return Response({"error": f"Chat failed: {str(e)}"}, status=500)

    ChatMessage.objects.create(owner=request.user, session=session, role="assistant", text=reply_text, segments=segments)

    # Auto-title the session from the first message, and bump updated_at
    # (via save(), thanks to auto_now=True) so it sorts to the top of the sidebar
    if not session.title:
        session.title = message[:40] + ("…" if len(message) > 40 else "")
    session.save()

    return Response({"segments": segments})
# ===================== CHANGE END =====================


# GET /api/chat/sessions/ — list this user's chat sessions (for the
# sidebar). POST — start a brand new empty one (the "New Chat" button)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def chat_sessions(request):
    if request.method == "GET":
        sessions = ChatSession.objects.filter(owner=request.user)
        return Response(ChatSessionSerializer(sessions, many=True).data)

    session = ChatSession.objects.create(owner=request.user, title="")
    return Response(ChatSessionSerializer(session).data, status=201)


# PATCH/DELETE /api/chat/sessions/<id>/ — rename or delete one specific
# conversation. Deleting a session also deletes all its messages
# automatically (ChatMessage.session has on_delete=CASCADE).
@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def chat_session_detail(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, owner=request.user)

    if request.method == "DELETE":
        session.delete()
        return Response(status=204)

    new_title = request.data.get("title", "").strip()
    if not new_title:
        return Response({"error": "Title cannot be empty"}, status=400)
    session.title = new_title
    session.save(update_fields=["title"])
    return Response(ChatSessionSerializer(session).data)
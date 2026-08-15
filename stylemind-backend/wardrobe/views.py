# wardrobe/views.py
import time
import threading
import hashlib  # NEW — was used in upload_item's duplicate check below but never imported (would have thrown NameError on first upload)
from io import BytesIO
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.db import connections

from .models import Profile, WardrobeItem, Outfit, ChatMessage, ChatSession
from .serializers import SignupSerializer, ProfileSerializer, WardrobeItemSerializer, OutfitSerializer, ChatSessionSerializer
from src.predict import predict
from .weather import resolve_temperature, get_rain_nudge
from src.recommend.recommend import get_recommendations

from .chatbot import get_stylist_reply

SERVER_STARTED_AT = time.time()


# ────────────────────────────────────────────────
# HEALTH
# ────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    return Response({"started_at": SERVER_STARTED_AT})


# ────────────────────────────────────────────────
# AUTH
# ────────────────────────────────────────────────

@api_view(["POST"])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created"}, status=201)
    return Response(serializer.errors, status=400)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def me(request):
    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"display_name": request.user.username, "email": request.user.email},
    )
    if request.method == "PATCH":
        if request.data.get("remove_picture") == "true":
            if profile.profile_picture:
                profile.profile_picture.delete(save=False)
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

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_wardrobe(request):
    items = WardrobeItem.objects.filter(owner=request.user).order_by("-uploaded_at")
    return Response(WardrobeItemSerializer(items, many=True).data)


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
        seg["display"].save(buffer, format="PNG")
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
        connections.close_all()


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload_item(request):
    image_file = request.FILES.get("image")
    if not image_file:
        return Response({"error": "No image provided"}, status=400)

    file_bytes = image_file.read()
    image_file.seek(0)
    image_hash = hashlib.sha256(file_bytes).hexdigest()

    # If this exact photo (by content, not filename) already exists for
    # this user, skip the ML pipeline entirely (same bytes = guaranteed
    # same classification result — re-running it would be pure waste),
    # copy the matched item's classification data, and flag it for the
    # user to confirm keep/discard.
    existing_match = WardrobeItem.objects.filter(owner=request.user, image_hash=image_hash).first()

    if existing_match:
        item = WardrobeItem.objects.create(
            owner=request.user,
            image=image_file,
            category=existing_match.category,
            category_confidence=existing_match.category_confidence,
            texture=existing_match.texture,
            texture_confidence=existing_match.texture_confidence,
            season=existing_match.season,
            season_confidence=existing_match.season_confidence,
            season_probs=existing_match.season_probs,
            dominant_colors=existing_match.dominant_colors,
            mask_found=existing_match.mask_found,
            status="duplicate_review",
            image_hash=image_hash,
            possible_duplicate_of=existing_match,
        )
        # ===================== CHANGE START =====================
        # NEW — copies the already-generated background-removed image
        # too. Identical input bytes guarantee an identical segmentation
        # result, so there's no need to re-run YOLO for this — just reuse
        # the file that's already sitting on disk.
        if existing_match.processed_image:
            existing_match.processed_image.open("rb")
            item.processed_image.save(
                existing_match.processed_image.name.split("/")[-1],
                ContentFile(existing_match.processed_image.read()),
                save=True,
            )
            existing_match.processed_image.close()
        # ===================== CHANGE END =====================
        return Response(WardrobeItemSerializer(item).data, status=202)

    item = WardrobeItem.objects.create(
        owner=request.user,
        image=image_file,
        category="", category_confidence=0,
        texture="", texture_confidence=0,
        season="", season_confidence=0,
        season_probs={}, dominant_colors=[], mask_found=False,
        status="processing",
        image_hash=image_hash,
    )

    thread = threading.Thread(target=_process_item_async, args=(item.id,), daemon=True)
    thread.start()

    return Response(WardrobeItemSerializer(item).data, status=202)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_item(request, item_id):
    item = get_object_or_404(WardrobeItem, id=item_id, owner=request.user)
    item.delete()
    return Response(status=204)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def toggle_favorite(request, item_id):
    item = get_object_or_404(WardrobeItem, id=item_id, owner=request.user)
    item.favorite = request.data.get("favorite", not item.favorite)
    item.save()
    return Response(WardrobeItemSerializer(item).data)


# ===================== CHANGE START =====================
# NEW — PATCH /api/wardrobe/<id>/resolve-duplicate/ — { "keep": true/false }
# keep=true: user confirms it's fine, marks it "done"
# keep=false: deletes it
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def resolve_duplicate(request, item_id):
    item = get_object_or_404(WardrobeItem, id=item_id, owner=request.user)
    if request.data.get("keep"):
        item.status = "done"
        item.save(update_fields=["status"])
        return Response(WardrobeItemSerializer(item).data)
    else:
        item.delete()
        return Response(status=204)
# ===================== CHANGE END =====================


# ────────────────────────────────────────────────
# RECOMMENDATIONS
# ────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommend(request):
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")
    manual_temp = request.GET.get("temp_c")

    try:
        temp_c, weather_info = resolve_temperature(lat=lat, lon=lon, manual_temp=manual_temp)
    except ValueError as e:
        return Response({"error": str(e)}, status=400)

    intent = request.GET.get("intent")
    style_preference = request.GET.get("style_preference", "safe")
    top_k = int(request.GET.get("top_k", 3))

    items = WardrobeItem.objects.filter(owner=request.user).order_by("id")
    wardrobe = [WardrobeItemSerializer(i).data for i in items]
    results = get_recommendations(wardrobe, temp_c=temp_c, intent=intent, top_k=top_k, style_preference=style_preference)

    rain_nudge = get_rain_nudge(weather_info)

    return Response({
        "weather": weather_info,
        "recommendations": results,
        "initial_count": top_k,
        "rain_nudge": rain_nudge,
    })


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def outfits(request):
    if request.method == "GET":
        saved = Outfit.objects.filter(owner=request.user).order_by("-saved_at")
        return Response(OutfitSerializer(saved, many=True).data)

    for field in ["top", "bottom", "jacket"]:
        item_id = request.data.get(field)
        if item_id:
            get_object_or_404(WardrobeItem, id=item_id, owner=request.user)

    serializer = OutfitSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(owner=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_outfit(request, outfit_id):
    outfit = get_object_or_404(Outfit, id=outfit_id, owner=request.user)
    outfit.delete()
    return Response(status=204)


# ────────────────────────────────────────────────
# CHATBOT
# ────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def chat(request):
    if request.method == "GET":
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

    if not session.title:
        session.title = message[:40] + ("…" if len(message) > 40 else "")
    session.save()

    return Response({"segments": segments})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def chat_sessions(request):
    if request.method == "GET":
        sessions = ChatSession.objects.filter(owner=request.user)
        return Response(ChatSessionSerializer(sessions, many=True).data)

    session = ChatSession.objects.create(owner=request.user, title="")
    return Response(ChatSessionSerializer(session).data, status=201)


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
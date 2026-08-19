# wardrobe/views.py

import time
import threading
import hashlib

from io import BytesIO

from rest_framework.decorators import (
    api_view,
    permission_classes,
    parser_classes,
)
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.core.files import File
from django.db import connections

from .models import (
    Profile,
    WardrobeItem,
    Outfit,
    ChatMessage,
    ChatSession,
    TryOnResult,
)

from .serializers import (
    SignupSerializer,
    ProfileSerializer,
    WardrobeItemSerializer,
    OutfitSerializer,
    ChatSessionSerializer,
    TryOnResultSerializer,
)

from .tryon import generate_tryon

from src.predict import predict
from .weather import resolve_temperature, get_rain_nudge
from src.recommend.recommend import get_recommendations
from .chatbot import get_stylist_reply


# ────────────────────────────────────────────────
# SERVER START TIME
# ────────────────────────────────────────────────

SERVER_STARTED_AT = time.time()


# ────────────────────────────────────────────────
# HEALTH
# ────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):

    return Response({
        "started_at": SERVER_STARTED_AT
    })


# ────────────────────────────────────────────────
# AUTH
# ────────────────────────────────────────────────

@api_view(["POST"])
def signup(request):

    serializer = SignupSerializer(
        data=request.data
    )

    if serializer.is_valid():

        serializer.save()

        return Response(
            {
                "message": "User created"
            },
            status=201
        )

    return Response(
        serializer.errors,
        status=400
    )


# ────────────────────────────────────────────────
# PROFILE
# GET /api/me/
# PATCH /api/me/
# ────────────────────────────────────────────────

@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def me(request):

    profile, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            "display_name": request.user.username,
            "email": request.user.email,
        },
    )

    if request.method == "PATCH":

        if request.data.get(
            "remove_picture"
        ) == "true":

            if profile.profile_picture:

                profile.profile_picture.delete(
                    save=False
                )

            profile.profile_picture = None

            profile.save()

        serializer = ProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                ProfileSerializer(
                    profile
                ).data
            )

        return Response(
            serializer.errors,
            status=400
        )

    return Response(
        ProfileSerializer(
            profile
        ).data
    )


# ────────────────────────────────────────────────
# WARDROBE
# ────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_wardrobe(request):

    items = (
        WardrobeItem.objects
        .filter(
            owner=request.user
        )
        .order_by("-uploaded_at")
    )

    return Response(
        WardrobeItemSerializer(
            items,
            many=True
        ).data
    )


# ────────────────────────────────────────────────
# BACKGROUND IMAGE PROCESSING
# ────────────────────────────────────────────────

def _process_item_async(item_id):

    try:

        item = WardrobeItem.objects.get(
            id=item_id
        )

        result, seg = predict(
            item.image.path,
            return_segmentation=True
        )

        # ML classification results

        item.category = result["category"]

        item.category_confidence = (
            result["category_confidence"]
        )

        item.texture = result["texture"]

        item.texture_confidence = (
            result["texture_confidence"]
        )

        item.season = result["season"]

        item.season_confidence = (
            result["season_confidence"]
        )

        item.season_probs = (
            result["season_probs"]
        )

        item.dominant_colors = (
            result["dominant_colors"]
        )

        item.mask_found = (
            result["mask_found"]
        )

        # Processed image

        buffer = BytesIO()

        seg["display"].save(
            buffer,
            format="PNG"
        )

        filename = (
            item.image.name
            .split("/")[-1]
        )

        item.processed_image.save(
            f"processed_{filename}.png",
            ContentFile(
                buffer.getvalue()
            ),
            save=False
        )

        item.status = "done"

        item.save()

    except Exception as e:

        print(
            f"Background processing failed "
            f"for item {item_id}: {e}"
        )

        try:

            WardrobeItem.objects.filter(
                id=item_id
            ).update(
                status="failed"
            )

        except Exception:
            pass

    finally:

        connections.close_all()


# ────────────────────────────────────────────────
# UPLOAD WARDROBE ITEM
# ────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload_item(request):

    image_file = request.FILES.get(
        "image"
    )

    if not image_file:

        return Response(
            {
                "error": "No image provided"
            },
            status=400
        )

    # Read file for SHA-256 hash

    file_bytes = image_file.read()

    image_file.seek(0)

    image_hash = hashlib.sha256(
        file_bytes
    ).hexdigest()

    # ------------------------------------------------
    # CHECK DUPLICATE
    # ------------------------------------------------

    existing_match = (
        WardrobeItem.objects
        .filter(
            owner=request.user,
            image_hash=image_hash
        )
        .first()
    )

    if existing_match:

        item = WardrobeItem.objects.create(

            owner=request.user,

            image=image_file,

            category=(
                existing_match.category
            ),

            category_confidence=(
                existing_match.category_confidence
            ),

            texture=(
                existing_match.texture
            ),

            texture_confidence=(
                existing_match.texture_confidence
            ),

            season=(
                existing_match.season
            ),

            season_confidence=(
                existing_match.season_confidence
            ),

            season_probs=(
                existing_match.season_probs
            ),

            dominant_colors=(
                existing_match.dominant_colors
            ),

            mask_found=(
                existing_match.mask_found
            ),

            status="duplicate_review",

            image_hash=image_hash,

            possible_duplicate_of=(
                existing_match
            ),
        )

        # Copy processed image

        if existing_match.processed_image:

            existing_match.processed_image.open(
                "rb"
            )

            item.processed_image.save(

                existing_match
                .processed_image
                .name
                .split("/")[-1],

                ContentFile(
                    existing_match
                    .processed_image
                    .read()
                ),

                save=True,
            )

            existing_match.processed_image.close()

        return Response(
            WardrobeItemSerializer(
                item
            ).data,
            status=202
        )

    # ------------------------------------------------
    # CREATE NEW ITEM
    # ------------------------------------------------

    item = WardrobeItem.objects.create(

        owner=request.user,

        image=image_file,

        category="",

        category_confidence=0,

        texture="",

        texture_confidence=0,

        season="",

        season_confidence=0,

        season_probs={},

        dominant_colors=[],

        mask_found=False,

        status="processing",

        image_hash=image_hash,
    )

    # ------------------------------------------------
    # PROCESS IN BACKGROUND
    # ------------------------------------------------

    thread = threading.Thread(

        target=_process_item_async,

        args=(item.id,),

        daemon=True
    )

    thread.start()

    return Response(
        WardrobeItemSerializer(
            item
        ).data,
        status=202
    )


# ────────────────────────────────────────────────
# DELETE WARDROBE ITEM
# ────────────────────────────────────────────────

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_item(
    request,
    item_id
):

    item = get_object_or_404(

        WardrobeItem,

        id=item_id,

        owner=request.user
    )

    item.delete()

    return Response(
        status=204
    )


# ────────────────────────────────────────────────
# FAVORITE
# ────────────────────────────────────────────────

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def toggle_favorite(
    request,
    item_id
):

    item = get_object_or_404(

        WardrobeItem,

        id=item_id,

        owner=request.user
    )

    item.favorite = request.data.get(
        "favorite",
        not item.favorite
    )

    item.save()

    return Response(
        WardrobeItemSerializer(
            item
        ).data
    )


# ────────────────────────────────────────────────
# RESOLVE DUPLICATE
# ────────────────────────────────────────────────

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def resolve_duplicate(
    request,
    item_id
):

    item = get_object_or_404(

        WardrobeItem,

        id=item_id,

        owner=request.user
    )

    if request.data.get("keep"):

        item.status = "done"

        item.save(
            update_fields=[
                "status"
            ]
        )

        return Response(
            WardrobeItemSerializer(
                item
            ).data
        )

    item.delete()

    return Response(
        status=204
    )


# ────────────────────────────────────────────────
# RECOMMENDATIONS
# ────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommend(request):

    lat = request.GET.get(
        "lat"
    )

    lon = request.GET.get(
        "lon"
    )

    manual_temp = request.GET.get(
        "temp_c"
    )

    try:

        temp_c, weather_info = (
            resolve_temperature(
                lat=lat,
                lon=lon,
                manual_temp=manual_temp
            )
        )

    except ValueError as e:

        return Response(
            {
                "error": str(e)
            },
            status=400
        )

    intent = request.GET.get(
        "intent"
    )

    style_preference = request.GET.get(
        "style_preference",
        "safe"
    )

    top_k = int(
        request.GET.get(
            "top_k",
            3
        )
    )

    items = (
        WardrobeItem.objects
        .filter(
            owner=request.user
        )
        .order_by("id")
    )

    wardrobe = [
        WardrobeItemSerializer(
            i
        ).data
        for i in items
    ]

    results = get_recommendations(

        wardrobe,

        temp_c=temp_c,

        intent=intent,

        top_k=top_k,

        style_preference=(
            style_preference
        )
    )

    rain_nudge = get_rain_nudge(
        weather_info
    )

    return Response({

        "weather": weather_info,

        "recommendations": results,

        "initial_count": top_k,

        "rain_nudge": rain_nudge,
    })


# ────────────────────────────────────────────────
# SAVED OUTFITS
# ────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def outfits(request):

    if request.method == "GET":

        saved = (
            Outfit.objects
            .filter(
                owner=request.user
            )
            .order_by("-saved_at")
        )

        return Response(
            OutfitSerializer(
                saved,
                many=True
            ).data
        )

    # Validate wardrobe items

    for field in [
        "top",
        "bottom",
        "jacket"
    ]:

        item_id = request.data.get(
            field
        )

        if item_id:

            get_object_or_404(

                WardrobeItem,

                id=item_id,

                owner=request.user
            )

    serializer = OutfitSerializer(
        data=request.data
    )

    if serializer.is_valid():

        serializer.save(
            owner=request.user
        )

        return Response(
            serializer.data,
            status=201
        )

    return Response(
        serializer.errors,
        status=400
    )


# ────────────────────────────────────────────────
# DELETE SAVED OUTFIT
# ────────────────────────────────────────────────

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_outfit(
    request,
    outfit_id
):

    outfit = get_object_or_404(

        Outfit,

        id=outfit_id,

        owner=request.user
    )

    outfit.delete()

    return Response(
        status=204
    )


# ────────────────────────────────────────────────
# CHATBOT
# ────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def chat(request):

    if request.method == "GET":

        session_id = request.GET.get(
            "session"
        )

        if not session_id:

            return Response(
                {
                    "error":
                    "session query param is required"
                },
                status=400
            )

        session = get_object_or_404(

            ChatSession,

            id=session_id,

            owner=request.user
        )

        messages = (
            ChatMessage.objects
            .filter(
                session=session
            )
        )

        data = [

            {
                "id": m.id,

                "role": m.role,

                "text": m.text,

                "segments": m.segments,

                "timestamp":
                    m.created_at,
            }

            for m in messages
        ]

        return Response(
            data
        )

    message = request.data.get(
        "message",
        ""
    ).strip()

    session_id = request.data.get(
        "session"
    )

    lat = request.data.get(
        "lat"
    )

    lon = request.data.get(
        "lon"
    )

    if not message:

        return Response(
            {
                "error":
                "Message is required"
            },
            status=400
        )

    if not session_id:

        return Response(
            {
                "error":
                "session is required"
            },
            status=400
        )

    session = get_object_or_404(

        ChatSession,

        id=session_id,

        owner=request.user
    )

    ChatMessage.objects.create(

        owner=request.user,

        session=session,

        role="user",

        text=message
    )

    try:

        reply_text, segments = (
            get_stylist_reply(

                request.user,

                message,

                session=session,

                lat=lat,

                lon=lon
            )
        )

    except Exception as e:

        return Response(
            {
                "error":
                f"Chat failed: {str(e)}"
            },
            status=500
        )

    ChatMessage.objects.create(

        owner=request.user,

        session=session,

        role="assistant",

        text=reply_text,

        segments=segments
    )

    if not session.title:

        session.title = (
            message[:40]
            +
            (
                "…"
                if len(message) > 40
                else ""
            )
        )

    session.save()

    return Response(
        {
            "segments": segments
        }
    )


# ────────────────────────────────────────────────
# CHAT SESSIONS
# ────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def chat_sessions(request):

    if request.method == "GET":

        sessions = (
            ChatSession.objects
            .filter(
                owner=request.user
            )
        )

        return Response(
            ChatSessionSerializer(
                sessions,
                many=True
            ).data
        )

    session = ChatSession.objects.create(

        owner=request.user,

        title=""
    )

    return Response(
        ChatSessionSerializer(
            session
        ).data,
        status=201
    )


# ────────────────────────────────────────────────
# CHAT SESSION DETAIL
# ────────────────────────────────────────────────

@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def chat_session_detail(
    request,
    session_id
):

    session = get_object_or_404(

        ChatSession,

        id=session_id,

        owner=request.user
    )

    if request.method == "DELETE":

        session.delete()

        return Response(
            status=204
        )

    new_title = request.data.get(
        "title",
        ""
    ).strip()

    if not new_title:

        return Response(
            {
                "error":
                "Title cannot be empty"
            },
            status=400
        )

    session.title = new_title

    session.save(
        update_fields=[
            "title"
        ]
    )

    return Response(
        ChatSessionSerializer(
            session
        ).data
    )


# ────────────────────────────────────────────────
# VIRTUAL TRY-ON
# ────────────────────────────────────────────────

def _process_tryon_async(tryon_id):

    try:

        tryon = TryOnResult.objects.get(
            id=tryon_id
        )

        # ------------------------------------------------
        # TOP IMAGE
        # ------------------------------------------------

        if tryon.top:

            if tryon.top.processed_image:

                top_path = (
                    tryon.top
                    .processed_image
                    .path
                )

            else:

                top_path = (
                    tryon.top
                    .image
                    .path
                )

        else:

            top_path = None

        # ------------------------------------------------
        # BOTTOM IMAGE
        # ------------------------------------------------

        if tryon.bottom:

            if tryon.bottom.processed_image:

                bottom_path = (
                    tryon.bottom
                    .processed_image
                    .path
                )

            else:

                bottom_path = (
                    tryon.bottom
                    .image
                    .path
                )

        else:

            bottom_path = None

        # ------------------------------------------------
        # DETERMINE CATEGORY
        # ------------------------------------------------

        if (
            tryon.bottom
            and tryon.bottom.category
            and tryon.bottom.category.lower()
            == "dress"
        ):

            bottom_category = "Dress"

        else:

            bottom_category = "Lower-body"

        # ------------------------------------------------
        # GENERATE TRY-ON
        # ------------------------------------------------

        result_path = generate_tryon(

            person_image_path=(
                tryon
                .person_photo
                .path
            ),

            top_image_path=top_path,

            bottom_image_path=bottom_path,

            bottom_category=(
                bottom_category
            ),
        )

        # ------------------------------------------------
        # SAVE RESULT
        # ------------------------------------------------

        with open(
            result_path,
            "rb"
        ) as f:

            tryon.result_image.save(

                f"tryon_{tryon_id}.png",

                File(f),

                save=False
            )

        tryon.status = "done"

        tryon.error_message = ""

        tryon.save()

    except Exception as e:

        print(
            f"Try-on generation failed "
            f"for {tryon_id}: {e}"
        )

        TryOnResult.objects.filter(
            id=tryon_id
        ).update(

            status="failed",

            error_message=str(e)[:255]
        )

    finally:

        connections.close_all()


# ────────────────────────────────────────────────
# START TRY-ON
# ────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def start_tryon(request):

    # ------------------------------------------------
    # PERSON PHOTO
    # ------------------------------------------------

    photo_file = request.FILES.get(
        "photo"
    )

    if not photo_file:

        return Response(
            {
                "error":
                "No photo provided"
            },
            status=400
        )

    # ------------------------------------------------
    # SELECTED ITEMS
    # ------------------------------------------------

    top_id = request.data.get(
        "top_id"
    )

    bottom_id = request.data.get(
        "bottom_id"
    )

    if not top_id and not bottom_id:

        return Response(
            {
                "error":
                "Select at least one item "
                "to try on"
            },
            status=400
        )

    # ------------------------------------------------
    # GET TOP
    # ------------------------------------------------

    if top_id:

        top = get_object_or_404(

            WardrobeItem,

            id=top_id,

            owner=request.user
        )

    else:

        top = None

    # ------------------------------------------------
    # GET BOTTOM
    # ------------------------------------------------

    if bottom_id:

        bottom = get_object_or_404(

            WardrobeItem,

            id=bottom_id,

            owner=request.user
        )

    else:

        bottom = None

    # ------------------------------------------------
    # CREATE TRY-ON
    # ------------------------------------------------

    tryon = TryOnResult.objects.create(

        owner=request.user,

        person_photo=photo_file,

        top=top,

        bottom=bottom,

        status="processing",
    )

    # ------------------------------------------------
    # BACKGROUND PROCESSING
    # ------------------------------------------------

    thread = threading.Thread(

        target=_process_tryon_async,

        args=(tryon.id,),

        daemon=True
    )

    thread.start()

    # ------------------------------------------------
    # RETURN
    # ------------------------------------------------

    return Response(

        TryOnResultSerializer(
            tryon
        ).data,

        status=202
    )


# ────────────────────────────────────────────────
# TRY-ON STATUS
# ────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tryon_status(
    request,
    tryon_id
):

    tryon = get_object_or_404(

        TryOnResult,

        id=tryon_id,

        owner=request.user
    )

    return Response(
        TryOnResultSerializer(
            tryon
        ).data
    )

# POST /api/tryon/<id>/cancel/ — marks a try-on as cancelled. Can't force-kill
# the background thread mid-network-call (Python doesn't support that
# safely), but marking it "failed" here means: (a) the frontend stops
# polling it immediately, and (b) even if the thread eventually finishes,
# nothing will ever display that result — it's already discarded.
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cancel_tryon(request, tryon_id):
    result = get_object_or_404(TryOnResult, id=tryon_id, owner=request.user)
    result.status = "failed"
    result.error_message = "Cancelled by user"
    result.save(update_fields=["status", "error_message"])
    return Response(status=204)
from django.shortcuts import render

# Create your views here.
import sys
from pathlib import Path
from .weather import get_current_temp

sys.path.append(str(Path(__file__).resolve().parent.parent))  # so "src" is importable

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User

from .models import WardrobeItem
from .serializers import WardrobeItemSerializer, SignupSerializer

from src.predict import predict
from src.recommend.recommend import get_recommendations



@api_view(["POST"])
@permission_classes([AllowAny])
def signup(request):
    serializer = SignupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({"message": "User created"}, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_item(request):
    image_file = request.FILES["image"]

    # save temporarily so predict() can read it via a real file path
    item = WardrobeItem.objects.create(owner=request.user, image=image_file,
                                        category="", category_confidence=0,
                                        texture="", texture_confidence=0,
                                        season="", season_confidence=0,
                                        season_probs={}, dominant_colors=[],
                                        mask_found=False)

    result = predict(item.image.path)

    item.category = result["category"]
    item.category_confidence = result["category_confidence"]
    item.texture = result["texture"]
    item.texture_confidence = result["texture_confidence"]
    item.season = result["season"]
    item.season_confidence = result["season_confidence"]
    item.season_probs = result["season_probs"]
    item.dominant_colors = result["dominant_colors"]
    item.mask_found = result["mask_found"]
    item.save()

    return Response(WardrobeItemSerializer(item).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_wardrobe(request):
    items = WardrobeItem.objects.filter(owner=request.user)
    return Response(WardrobeItemSerializer(items, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommend(request):
    # city = request.GET.get("city") 
    # temp_c_param = request.GET.get("temp_c") 
    # if city: 
    #     temp_c = get_current_temp(city) 
    #     elif temp_c_param: temp_c = float(temp_c_param) else: return Response({"error": "Provide either 'city' or 'temp_c'"}, status=400)
    temp_c = float(request.GET.get("temp_c"))
    intent = request.GET.get("intent")
    style_preference = request.GET.get("style_preference", "safe")
    top_k = int(request.GET.get("top_k", 3))

    items = WardrobeItem.objects.filter(owner=request.user)
    wardrobe = [WardrobeItemSerializer(i).data for i in items]

    results = get_recommendations(wardrobe, temp_c=temp_c, intent=intent,
                                   top_k=top_k, style_preference=style_preference)
    return Response(results)
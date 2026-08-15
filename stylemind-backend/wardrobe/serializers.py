from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Profile, WardrobeItem, Outfit
from .models import ChatSession
from django.db.models import Q

# ===================== CHANGE START =====================
# Updated: now also accepts email + display_name (previously only
# username + password), and creates a matching Profile row alongside
# the Django User, so the real name/email actually gets stored.
class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    email = serializers.EmailField()
    display_name = serializers.CharField(max_length=150)

    # Custom validation: reject signup if the username is already taken
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    # Runs when serializer.save() is called — creates both the User
    # (Django's built-in auth table) AND our custom Profile row
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data["email"],
        )
        Profile.objects.create(
            user=user,
            display_name=validated_data["display_name"],
            email=validated_data["email"],
        )
        return user


# Serializes a Profile object. Also handles updates (PATCH) now — display_name
# and profile_picture are editable, email is read-only since it's tied to the
# login username, and date_joined is a nice-to-have shown read-only.
class ProfileSerializer(serializers.Serializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(read_only=True)
    display_name = serializers.CharField()
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    date_joined = serializers.DateTimeField(source="user.date_joined", read_only=True)

    def update(self, instance, validated_data):
        instance.display_name = validated_data.get("display_name", instance.display_name)
        if "profile_picture" in validated_data:
            instance.profile_picture = validated_data["profile_picture"]
        instance.save()
        return instance
# ===================== CHANGE END =====================


class WardrobeItemSerializer(serializers.ModelSerializer):
    selection_count = serializers.SerializerMethodField()
    # NEW — nested detail of the existing item this one's photo matches,
    # so the frontend can show its real category, not just an id
    possible_duplicate_of_detail = serializers.SerializerMethodField()

    def get_selection_count(self, obj):
        return Outfit.objects.filter(Q(top=obj) | Q(bottom=obj) | Q(jacket=obj)).count()

    def get_possible_duplicate_of_detail(self, obj):
        if obj.possible_duplicate_of:
            return WardrobeItemSerializer(obj.possible_duplicate_of).data
        return None

    class Meta:
        model = WardrobeItem
        fields = "__all__"
        read_only_fields = ["owner"]

# ===================== CHANGE START =====================
# New: serializes a saved Outfit. Includes both the raw IDs (top/bottom/
# jacket — used when the frontend SUBMITS a new outfit) and the full
# nested item details (top_detail etc. — used when DISPLAYING a saved
# outfit, so the frontend doesn't need a second request to get item info).
class OutfitSerializer(serializers.ModelSerializer):
    top_detail = WardrobeItemSerializer(source="top", read_only=True)
    bottom_detail = WardrobeItemSerializer(source="bottom", read_only=True)
    jacket_detail = WardrobeItemSerializer(source="jacket", read_only=True)

    class Meta:
        model = Outfit
        # temp_c, city, style_preference ADDED — so the frontend can both
        # submit and later display exactly what conditions this outfit was saved under
        fields = [
            "id", "occasion", "temp_c", "location_name", "region", "country", "style_preference",
            "top", "bottom", "jacket", "top_detail", "bottom_detail", "jacket_detail", "saved_at",
        ]
        read_only_fields = ["owner"]
# ===================== CHANGE END =====================

# ===================== CHANGE START =====================
# New — used by the sidebar to show the list of past conversations
class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ["id", "title", "created_at", "updated_at"]
# ===================== CHANGE END =====================
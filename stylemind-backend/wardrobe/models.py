from django.db import models
from django.contrib.auth.models import User

# New model: stores the real name/email a user typed at signup.
# Django's built-in User model only has username/password by default,
# so this separate table holds the extra profile info the frontend needs
# (e.g. to greet the user by their real name).
class Profile(models.Model):
    # One-to-one link: each Django User has exactly one Profile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=150)  # the real name typed at signup
    email = models.EmailField()
    profile_picture = models.ImageField(upload_to="profile_pics/", null=True, blank=True)

    def __str__(self):
        return self.display_name


class WardrobeItem(models.Model):
    # Every wardrobe item belongs to exactly one user (the owner)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wardrobe_items")

    # The original photo the user uploaded, unmodified
    image = models.ImageField(upload_to="wardrobe/")

    # The background-removed / letterboxed version of the photo that
    # predict.py generates for the classifier. null=True and blank=True
    # mean older items (uploaded before this field existed) won't break —
    # they just have processed_image = None.
    processed_image = models.ImageField(upload_to="wardrobe/processed/", null=True, blank=True)

    # These fields all come directly from the ML classification pipeline
    category = models.CharField(max_length=30)
    category_confidence = models.FloatField()
    texture = models.CharField(max_length=30)
    texture_confidence = models.FloatField()
    season = models.CharField(max_length=20)
    season_confidence = models.FloatField()
    season_probs = models.JSONField()      # e.g. {"summer": 0.8, "winter": 0.1, ...}
    dominant_colors = models.JSONField()   # e.g. ["#FFFFFF", "#111827"]
    mask_found = models.BooleanField()     # did YOLO successfully detect the garment?

    # Lets the user mark an item as a favorite from the frontend.
    # default=False means every existing item starts as "not favorited".
    favorite = models.BooleanField(default=False)

    # NEW — "duplicate_review" is a third state: this item's photo exactly
    # matches one already in the wardrobe, so it's held for the user to
    # confirm keep/discard instead of silently becoming "done".
    STATUS_CHOICES = [
        ("processing", "Processing"),
        ("done", "Done"),
        ("failed", "Failed"),
        ("duplicate_review", "Possible Duplicate"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="done")

    # SHA-256 of the raw uploaded file bytes — catches the exact same
    # photo being re-uploaded, even if renamed
    image_hash = models.CharField(max_length=64, blank=True, db_index=True)

    # Points at the existing item this one's photo matches, once flagged.
    # on_delete=SET_NULL so deleting the original doesn't cascade-delete this one.
    possible_duplicate_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    uploaded_at = models.DateTimeField(auto_now_add=True)  # auto-set when the row is created

    def __str__(self):
        return f"{self.category} ({self.owner.username})"


# Represents one "saved outfit" — a combination of wardrobe items the
# user chose to keep from a recommendation. Each slot (top/bottom/jacket)
# points to a WardrobeItem, or can be empty/None (e.g. a dress-only
# outfit has no separate "top").
class Outfit(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="outfits")
    occasion = models.CharField(max_length=30)  # e.g. "Formal", "Casual"

    temp_c = models.FloatField(null=True, blank=True)  # temperature used at generation time (slider value, or resolved from weather)
    # 'city' renamed to 'location_name', plus 'region' and 'country'
    # added, so a saved outfit can show a full location breadcrumb (e.g.
    # "Kathmandu, Bagmati, Nepal") instead of just one city string. All
    # blank when GPS wasn't used (slider fallback).
    location_name = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    style_preference = models.CharField(max_length=20, blank=True)  # "safe" or "bold"

    # if a WardrobeItem that's part of a saved outfit gets
    # deleted, Django automatically deletes the ENTIRE Outfit row too,
    # instead of leaving it behind with a missing piece.
    top = models.ForeignKey(WardrobeItem, on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    bottom = models.ForeignKey(WardrobeItem, on_delete=models.CASCADE, null=True, blank=True, related_name="+")
    jacket = models.ForeignKey(WardrobeItem, on_delete=models.CASCADE, null=True, blank=True, related_name="+")


    saved_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Outfit for {self.occasion} ({self.owner.username})"


# Represents ONE distinct conversation thread. Each "New Chat" click gets
# its own separate history, shown as its own entry in the sidebar.
class ChatSession(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_sessions")
    title = models.CharField(max_length=100, blank=True)
    # NEW — lets the chatbot remember "which occasion am I currently
    # recommending for" and "how far into the ranked list have I already
    # gone", so a follow-up like "I don't want this, suggest something
    # else" advances to the NEXT real ranked pick from the recommendation
    # engine, instead of Gemini inventing a substitute on its own.
    last_intent = models.CharField(max_length=20, blank=True)
    last_outfit_index = models.IntegerField(default=0)
    last_temp_c = models.FloatField(null=True, blank=True)  # NEW — so a temperature-less follow-up ("something else") can still fall back to what was already established
    # ===================== CHANGE END =====================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]  # most recently active conversation first, for the sidebar

    def __str__(self):
        return self.title or f"Chat {self.id}"


# Stores every chat message (both user and AI) so conversations persist
# across sessions instead of resetting every time the page reloads.
# Gemini is called directly from Django, with real wardrobe/weather data
# pulled straight from the database instead of trusted from the frontend.
class ChatMessage(models.Model):
    ROLE_CHOICES = [("user", "User"), ("assistant", "Assistant")]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")

    # Every message belongs to a specific session. null=True only so
    # older messages (saved before this field existed) don't break the
    # migration; every message going forward will always have one.
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    text = models.TextField()  # the raw message — user's typed text, or Gemini's raw reply text
    # For assistant messages only: the reply broken into segments so the
    # frontend can render item photos inline. Stored as JSON like:
    # [{"type": "text", "text": "..."}, {"type": "item", "item_id": 42}, ...]
    segments = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]  # oldest first, so history reads top-to-bottom naturally

    def __str__(self):
        return f"{self.role}: {self.text[:40]}"


# Tracks one virtual try-on request: the photo the user uploaded, which
# wardrobe item(s) to put on them, and the generated result. Same
# processing/done/failed pattern as WardrobeItem, since generation takes
# a while and runs in a background thread.
class TryOnResult(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tryon_results")
    person_photo = models.ImageField(upload_to="tryon/person/")
    top = models.ForeignKey(WardrobeItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    bottom = models.ForeignKey(WardrobeItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    result_image = models.ImageField(upload_to="tryon/results/", null=True, blank=True)

    STATUS_CHOICES = [("processing", "Processing"), ("done", "Done"), ("failed", "Failed")]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="processing")
    error_message = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TryOn {self.id} ({self.owner.username}) - {self.status}"
# wardrobe/chatbot.py
# Everything related to talking to Gemini lives here, separate from
# views.py, so the view function itself stays short and readable.
import os
import re
from google import genai
from .models import WardrobeItem, Outfit, ChatMessage 
from src.recommend.recommend import get_recommendations
from .weather import resolve_temperature

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Same persona/grounding rules as before, updated with the real instruction
# for how to reference a wardrobe item inline — using [[item:ID]] markers
# that this file parses back out into real segments afterward.
SYSTEM_PROMPT = """You are the AI Stylist inside StyleMind, a friendly and knowledgeable personal fashion assistant.

You have normal conversations when the user just wants to chat, but your specialty is fashion advice.

When giving fashion advice, ground your reasoning in the structured wardrobe data you're given. Each wardrobe item includes:
- category (one of 21 clothing categories)
- texture (one of 7 fabric/texture types)
- season (one of 3 seasons the item suits)
- dominant_colors (the item's top 3 hex color codes)

Use color theory when reasoning about which colors pair well. Consider season and weather. Factor in the user's preference history to personalize suggestions.

When you mention a SPECIFIC item from the wardrobe list by name, write it inline as [[item:ID]] using that item's real id from the list — for example "your [[item:14]] would pair nicely with..." Do not invent ids that aren't in the wardrobe list provided.

Keep responses conversational and concise — this is a chat panel, not an essay."""

# Simple keyword detection, same idea as the old client-side version — but
# now it runs server-side, on real data, not duplicated in the frontend.
INTENT_KEYWORDS = {
    "Formal": ["formal", "wedding", "interview", "office", "meeting", "gala"],
    "Casual": ["casual", "weekend", "hangout", "everyday", "chill"],
    "Picnic": ["picnic", "park", "outdoor", "brunch"],
    "Travel": ["travel", "trip", "vacation", "flight", "airport"],
}
SEASON_TEMP_MAP = {
    "winter": 5, "cold": 5, "fall": 18, "autumn": 18,
    "spring": 20, "summer": 32, "hot": 32, "warm": 28,
}
# ===================== CHANGE START =====================
# REMOVED — DEFAULT_TEMP_C no longer exists. Weather is now only ever
# used in the prompt when it comes from a real source (resolved city/GPS,
# or the user naming a temperature/season themselves) — never a silent
# made-up default.
# ===================== CHANGE END =====================


def detect_intent(message):
    lower = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return intent
    return None


def detect_temp_c(message):
    lower = message.lower()
    for word, temp in SEASON_TEMP_MAP.items():
        if word in lower:
            return temp
    return None


def parse_segments(reply_text):
    """Splits Gemini's raw reply on [[item:ID]] markers into the
    {type, text/item_id} segment list the frontend expects."""
    parts = re.split(r"\[\[item:(\d+)\]\]", reply_text)
    segments = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part:  # skip empty strings between adjacent markers
                segments.append({"type": "text", "text": part})
        else:
            segments.append({"type": "item", "item_id": int(part)})
    return segments


def get_stylist_reply(user, message, session=None, lat=None, lon=None):    # Real wardrobe, straight from the database — no longer trusted from
    # whatever the frontend happens to send
    wardrobe_items = list(WardrobeItem.objects.filter(owner=user))
    wardrobe_context = [
        {
            "id": item.id, "category": item.category, "texture": item.texture,
            "season": item.season, "dominant_colors": item.dominant_colors,
        }
        for item in wardrobe_items
    ]

    # Real preference history, from actually-saved outfits
    preference_history = [
        {"occasion": o.occasion, "liked": True}
        for o in Outfit.objects.filter(owner=user)
    ]

    # ===================== CHANGE START =====================
    # CHANGED — no more silent 22°C default. Weather is only ever included
    # if we have a REAL source for it: a resolved city/GPS lookup, or the
    # user explicitly naming a temperature/season in their own message
    # (e.g. "it's cold today", "32 degrees"). If none of those exist,
    # temp_c and weather_desc both stay None — Gemini gives style advice
    # without pretending to know the weather.
    try:
        temp_c, weather_info = resolve_temperature(lat=lat, lon=lon, manual_temp=None)
        # CHANGED — 'city' renamed to 'location_name' to match the new
        # WeatherAPI.com response shape from weather.py
        weather_desc = f"{temp_c}°C, {weather_info['description']} in {weather_info['location_name']}" if weather_info else f"{temp_c}°C"
    except ValueError:
        detected = detect_temp_c(message)
        if detected is not None:
            temp_c = detected
            weather_desc = f"{temp_c}°C (mentioned in your message)"
        else:
            temp_c = None
            weather_desc = None
    # ===================== CHANGE END =====================

    # If the message names an occasion AND we actually know the
    # temperature, ground the reply in a REAL recommendation from the
    # actual scoring engine, not just raw wardrobe data
    recommended_outfit = None
    intent = detect_intent(message)
    # ===================== CHANGE START =====================
    # CHANGED — added "and temp_c is not None" so this never runs with a
    # fake/guessed temperature
    if intent and temp_c is not None:
    # ===================== CHANGE END =====================
        try:
            results = get_recommendations(wardrobe_context, temp_c=temp_c, intent=intent, top_k=1, style_preference="safe")
            if results:
                recommended_outfit = results[0]
        except Exception:
            pass  # non-fatal — chat still works without a grounded recommendation
    # DEBUG
    print("=" * 60)
    print("User message:", message)
    print("Intent:", intent)
    print("Temperature:", temp_c)
    print("Recommended Outfit:", recommended_outfit)
    print("=" * 60)
        
    # Pull the last 10 messages for this user as conversation history,
    # so Gemini has context of the recent back-and-forth
    recent = ChatMessage.objects.filter(owner=user, session=session).order_by("-created_at")[:10]    
    history_text = "\n".join(f"{m.role}: {m.text}" for m in reversed(list(recent)))

    # ===================== CHANGE START =====================
    # NEW — the "Weather:" line is now conditional, not always present.
    # When weather_desc is None, we tell Gemini explicitly that it's
    # unknown rather than omitting the line silently (which could make it
    # guess or hallucinate a temperature on its own).
    weather_line = (
        f"- Weather: {weather_desc}"
        if weather_desc
        else "- Weather: not provided — do not assume or guess a temperature; only factor in weather if the user mentions it themselves."
    )
    # ===================== CHANGE END =====================

    prompt = f"""Conversation so far:
{history_text}

Current context:
{weather_line}
- Wardrobe: {wardrobe_context}
- Preference history: {preference_history}
- Suggested outfit match (if relevant): {recommended_outfit}

User message: {message}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT},
    )
    reply_text = response.text
    segments = parse_segments(reply_text)

    # Attach the full item object to each "item" segment right here,
    # server-side, so the frontend doesn't need to re-look-up ids itself —
    # it just attaches image URLs and displays what it's given.
    item_lookup = {item.id: item for item in wardrobe_items}
    for seg in segments:
        if seg["type"] == "item":
            item = item_lookup.get(seg["item_id"])
            if item:
                seg["item"] = {
                    "id": item.id, "category": item.category, "texture": item.texture,
                    "season": item.season, "image": item.image.url if item.image else None,
                    "processed_image": item.processed_image.url if item.processed_image else None,
                }

    return reply_text, segments
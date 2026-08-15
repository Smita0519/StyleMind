# wardrobe/chatbot.py
import os
import re
from google import genai
from .models import WardrobeItem, Outfit, ChatMessage
from src.recommend.recommend import get_recommendations
from .weather import resolve_temperature
from .serializers import WardrobeItemSerializer

DEFAULT_TEMP_C = 22  # mild fallback, same default the Recommendations page's slider starts at

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """You are the AI Stylist inside StyleMind, a friendly and knowledgeable personal fashion assistant.

You have normal conversations when the user just wants to chat, but your specialty is fashion advice.

When giving fashion advice, ground your reasoning in the structured wardrobe data you're given. Each wardrobe item includes:
- category (one of 10 clothing categories)
- texture (one of 7 fabric/texture types)
- season (one of 4 seasons the item suits)
- dominant_colors (the item's top 3 hex color codes)

Use color theory when reasoning about which colors pair well. Consider season and weather. Factor in the user's preference history to personalize suggestions.

When you mention a SPECIFIC item from the wardrobe list by name, write it inline as [[item:ID]] using that item's real id from the list — for example "your [[item:14]] would pair nicely with..." This is the ONLY way to reference an item — never write the id any other way, such as "(ID 14)", "(id: 14)", "item #14", or "item 14" in plain text. Those forms will NOT show the user a photo, only the [[item:ID]] marker does. Do not invent ids that aren't in the wardrobe list provided.If a "Suggested outfit match" is given in the context, it is the SINGLE TOP PICK from StyleMind's real recommendation engine (KNN pairing + color-harmony scoring) — the exact same #1 result the Recommendations page itself would show for these conditions. This is the ONLY outfit you may present in your reply:
- Reference exactly those items via their ids, and explain why this particular combination works (colors, weather, occasion).
- Present it as your one recommendation, not as "an option" or "one idea" — never frame it as though there are other choices to browse, and never list a second combination alongside it, even if other wardrobe items would also seem to fit.
- If the user asks for another option, a different look, or something bolder/safer, explain that you're showing their current top pick and they can generate more choices on the Recommendations page — don't invent a second combination yourself.
- If "Suggested outfit match" starts with "NONE FOUND", no valid combination exists in the wardrobe at all for this occasion/weather — say so honestly, in your own words.
- If it starts with "EXHAUSTED", the engine's entire ranked list for this occasion/weather has already been shown earlier in this conversation. As an absolute last resort, you may suggest individual wardrobe items yourself — but you MUST explicitly tell the user these are no longer the engine's ranked recommendation, just your own pick from what's left, so they're never misled into thinking it's still an algorithm-backed suggestion.Keep responses conversational and concise — this is a chat panel, not an essay."""

# CHANGED — expanded Formal keywords to catch more real phrasing
INTENT_KEYWORDS = {
    "Formal": ["formal", "wedding", "interview", "office", "meeting", "gala", "presentation", "conference", "client", "boardroom", "work"],
    "Casual": ["casual", "weekend", "hangout", "everyday", "chill"],
    "Picnic": ["picnic", "park", "outdoor", "brunch"],
    "Travel": ["travel", "trip", "vacation", "flight", "airport"],
}
SEASON_TEMP_MAP = {
    "winter": 5, "cold": 5, "fall": 18, "autumn": 18,
    "spring": 20, "summer": 32, "hot": 32, "warm": 28,
}
# NEW — lets a user ask the chatbot for a bolder pick, same as the
# Recommendations page's Safe/Bold toggle, instead of always hardcoding "safe"
STYLE_KEYWORDS = {"bold": "bold", "daring": "bold", "adventurous": "bold", "safe": "safe", "simple": "safe", "classic": "safe"}

# NEW — detects "I don't like this, show me another" style follow-ups,
# so we can advance through the SAME ranked list the recommendation
# engine already computed, rather than letting Gemini invent something new
REJECT_KEYWORDS = [
    "don't want", "dont want", "don't like", "dont like", "not a fan",
    "something else", "different one", "another option", "not this",
    "anything else", "show me another", "suggest something else",
]

def is_rejection(message):
    lower = message.lower()
    return any(kw in lower for kw in REJECT_KEYWORDS)

def detect_intent(message):
    lower = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return intent
    return None


def detect_temp_c(message):
    # Matches a number followed by ANY common way someone might state a
    # temperature: "20°C", "20 °c", "20C", "20 degree", "20 degrees",
    # "20 degree celsius", "9 degree celcius" (common typo — [cs] covers
    # it), "20 deg C", etc. Requires SOME explicit temperature marker
    # right after the number — a bare number like "20 people" or "I'm 20"
    # is intentionally NOT matched, to avoid false positives.
    match = re.search(
        r"(-?\d{1,3})\s*(?:°\s*c?|deg(?:ree)?s?\.?\s*(?:cel[cs]ius)?\s*c?|cel[cs]ius|c\b)",
        message.lower(),
    )
    if match:
        return float(match.group(1))

    lower = message.lower()
    for word, temp in SEASON_TEMP_MAP.items():
        if word in lower:
            return temp
    return None


def detect_style_preference(message):
    lower = message.lower()
    for kw, style in STYLE_KEYWORDS.items():
        if kw in lower:
            return style
    return "safe"  # sensible default when nothing is mentioned


def parse_segments(reply_text):
    """Splits Gemini's raw reply on [[item:ID]] markers into the
    {type, text/item_id} segment list the frontend expects."""
    parts = re.split(r"\[\[item:(\d+)\]\]", reply_text)
    segments = []
    for i, part in enumerate(parts):
        if i % 2 == 0:
            if part:
                segments.append({"type": "text", "text": part})
        else:
            segments.append({"type": "item", "item_id": int(part)})
    return segments


def get_stylist_reply(user, message, session=None, lat=None, lon=None):
   # ===================== CHANGE START =====================
    # CHANGED — was a hand-built minimal dict (id/category/texture/season/
    # dominant_colors only), missing fields like season_confidence that
    # filtering.py actually reads. That gap made the chatbot's filtering
    # behave stricter than the real engine on the Recommendations page,
    # even for the exact same temperature/intent — sometimes finding
    # ZERO matches when the web version correctly found several. Now
    # reuses the SAME serializer views.py's recommend() uses, so both
    # paths get identical input, guaranteed.
    wardrobe_items = list(WardrobeItem.objects.filter(owner=user).order_by("id"))
    wardrobe_context = [WardrobeItemSerializer(item).data for item in wardrobe_items]
    # ===================== CHANGE END =====================

    preference_history = [
        {"occasion": o.occasion, "liked": True}
        for o in Outfit.objects.filter(owner=user)
    ]

    try:
        temp_c, weather_info = resolve_temperature(lat=lat, lon=lon, manual_temp=None)
        # CHANGED — round() only for the DISPLAYED text (e.g. "20°C"
        # instead of "20.3°C"). temp_c itself stays the precise float,
        # since that's what get_recommendations() below uses for actual
        # weather-bucket scoring — only the human-facing string is rounded.
        display_temp = round(temp_c)
        weather_desc = f"{display_temp}°C, {weather_info['description']} in {weather_info['location_name']}" if weather_info else f"{display_temp}°C"
    except ValueError:
        detected = detect_temp_c(message)
        if detected is not None:
            temp_c = detected
            weather_desc = f"{temp_c}°C (mentioned in your message)"
        else:
            temp_c = None
            weather_desc = None

    # ===================== CHANGE START =====================
    # CHANGED — figures out WHICH position in the ranked list to show:
    # - A freshly named occasion always starts back at #1 (index 0)
    # - A rejection ("something else") with no new occasion mentioned
    #   advances to the NEXT position in the SAME ranked list from last time
    # - Anything else (general chat) doesn't touch the recommendation
    #   engine at all
    # ===================== CHANGE START =====================
    detected_intent = detect_intent(message)
    style_preference = detect_style_preference(message)
    rejecting = is_rejection(message)

    intent = None
    temp_for_lookup = temp_c  # temp_c = whatever was resolved fresh this message (GPS/typed/detected), possibly None
    outfit_index = 0

    if detected_intent:
        intent = detected_intent
        # Only reset to the #1 pick if this is genuinely a NEW context —
        # a different occasion, or the temperature meaningfully changed
        # (>2°C). Restating the exact same occasion/weather mid-conversation
        # continues from wherever the conversation already was instead of
        # discarding a rejection the user already made.
        same_context = (
            session and session.last_intent == intent and temp_for_lookup is not None
            and session.last_temp_c is not None and abs(temp_for_lookup - session.last_temp_c) <= 2
        )
        outfit_index = (session.last_outfit_index or 0) if same_context else 0
    elif rejecting and session and session.last_intent:
        intent = session.last_intent
        outfit_index = (session.last_outfit_index or 0) + 1
        # FIX — the actual bug: a follow-up like "something else" has no
        # temperature of its own. Previously temp_c stayed None here,
        # which skipped the recommendation lookup entirely. Now it falls
        # back to whatever temperature the session already established.
        if temp_for_lookup is None:
            temp_for_lookup = session.last_temp_c

    recommended_outfit = "not applicable — no occasion/temperature context for this message"
    used_default_temp = False
    # ===================== CHANGE START =====================
    # NEW — occasion is known but temperature genuinely couldn't be
    # resolved (no location on, nothing typed/detected). Rather than
    # silently skipping grounding, fall back to a mild default so the
    # engine still runs — but flag it so Gemini is told to be upfront
    # about the assumption instead of pretending it's the real weather.
    if intent and temp_for_lookup is None:
        temp_for_lookup = DEFAULT_TEMP_C
        used_default_temp = True
    # ===================== CHANGE END =====================
    if intent and temp_for_lookup is not None:
        try:
            results = get_recommendations(wardrobe_context, temp_c=temp_for_lookup, intent=intent, top_k=1, style_preference=style_preference)
            if not results:
                recommended_outfit = (
                    "NONE FOUND. Tell the user warmly and briefly that nothing in their current "
                    "wardrobe quite comes together for this occasion/weather, and casually mention "
                    "the kind of item that might round it out — keep it conversational, vary your "
                    "phrasing, don't invent a combination that doesn't actually exist."
                )
            elif outfit_index < len(results):
                recommended_outfit = results[outfit_index]
            else:
                recommended_outfit = (
                    "EXHAUSTED. The recommendation engine's full ranked list for this occasion/"
                    "weather has already been shown across this conversation. As an absolute "
                    "last resort ONLY, you may now mention individual items directly from the "
                    "wardrobe list yourself — but you MUST clearly tell the user these are no "
                    "longer the engine's ranked picks, just your own suggestion from what's left "
                    "in their closet."
                )
            # NEW — tells Gemini to disclose the assumed temperature,
            # rather than presenting it as if it were the real weather
            if used_default_temp and isinstance(recommended_outfit, dict):
                recommended_outfit = {**recommended_outfit, "_note_to_ai": (
                    f"No real temperature was available, so a default of {DEFAULT_TEMP_C}°C was assumed for "
                    "this pick. Mention this briefly and naturally (e.g. suggest turning on location or "
                    "stating a temperature for a more accurate recommendation) — don't present this as if "
                    "it's confirmed real weather."
                )}

            if session:
                session.last_intent = intent
                session.last_outfit_index = outfit_index
                session.last_temp_c = temp_for_lookup
                session.save(update_fields=["last_intent", "last_outfit_index", "last_temp_c"])
        except Exception:
            recommended_outfit = "not applicable — recommendation engine error"
    # ===================== CHANGE END =====================

    recent = ChatMessage.objects.filter(owner=user, session=session).order_by("-created_at")[:10]
    history_text = "\n".join(f"{m.role}: {m.text}" for m in reversed(list(recent)))

    weather_line = (
        f"- Weather: {weather_desc}"
        if weather_desc
        else "- Weather: not provided — do not assume or guess a temperature; only factor in weather if the user mentions it themselves."
    )

    prompt = f"""Conversation so far:
{history_text}

Current context:
{weather_line}
- Wardrobe: {wardrobe_context}
- Preference history: {preference_history}
- Style preference detected: {style_preference}
- Suggested outfit match: {recommended_outfit}

User message: {message}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT},
    )
    reply_text = response.text
    segments = parse_segments(reply_text)

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
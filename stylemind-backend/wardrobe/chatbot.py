# wardrobe/chatbot.py
import os
import re
import random 
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

Whenever you state a temperature in your reply, always write it as "X°C" (the degree symbol, immediately followed by C, no space) — never spell it out as "X degrees" or "X degrees Celsius", even if the user phrased their own message that way.

When you mention a SPECIFIC item from the wardrobe list by name, write it inline as [[item:ID]] using that item's real id from the list — for example "your [[item:14]] would pair nicely with..." This is the ONLY way to reference an item — never write the id any other way, such as "(ID 14)", "(id: 14)", "item #14", or "item 14" in plain text. Those forms will NOT show the user a photo, only the [[item:ID]] marker does. Do not invent ids that aren't in the wardrobe list provided.If a "Suggested outfit match" is given in the context, it is a FIXED, PRE-COMPUTED result from StyleMind's real recommendation engine (KNN pairing + color-harmony scoring) — the exact same result the Recommendations page itself would show for these conditions. This is the ONLY outfit you may present in your reply, REGARDLESS of how short, vague, or casual the user's message is (e.g. "something else", "another one", "different") — a short message is still asking for a real recommendation, not permission to improvise:
- You MUST use the exact item ids given in "Suggested outfit match" — never substitute a different id you think might fit better, even if it seems like a more interesting or varied choice. The ids are not suggestions for you to reconsider; they are the answer.
- Reference exactly those items via their ids, and explain why this particular combination works (colors, weather, occasion).
- Present it as your one recommendation, not as "an option" or "one idea" — never frame it as though there are other choices to browse, and never list a second combination alongside it, even if other wardrobe items would also seem to fit.
- If any piece in "Suggested outfit match" (top, bottom, or jacket) has "off_season": True, or the outfit's own "off_season" field is True, mention this naturally and briefly — e.g. "heads up, this doesn't perfectly match the current season, but it's the best match your wardrobe has right now." Don't hide this, and don't make it sound alarming — just an honest, casual heads-up, the same way the Recommendations page shows an off-season badge.
- If "Suggested outfit match" includes a "match_percent" value, casually mention it somewhere in your reply (e.g. "a 92% match for this weather") — don't make it the focus, just a natural detail alongside the color/weather reasoning.

Keep responses conversational and concise — this is a chat panel, not an essay."""

# Expanded Formal keywords to catch more real phrasing
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
# Lets a user ask the chatbot for a bolder pick, same as the
# Recommendations page's Safe/Bold toggle, instead of always hardcoding "safe"
STYLE_KEYWORDS = {"bold": "bold", "daring": "bold", "adventurous": "bold", "safe": "safe", "simple": "safe", "classic": "safe"}

# Detects "I don't like this, show me another" style follow-ups,
# so we can advance through the SAME ranked list the recommendation
# engine already computed, rather than letting Gemini invent something new
REJECT_KEYWORDS = [
    "don't want", "dont want", "don't like", "dont like", "not a fan",
    "something else", "different one", "another option", "not this",
    "anything else", "show me another", "suggest something else",
    "give something else", "another outfit", "next outfit", "different outfit",
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
    """Returns the explicitly detected style, or None if nothing in the
    message indicates one."""
    lower = message.lower()
    for kw, style in STYLE_KEYWORDS.items():
        if kw in lower:
            return style
    return None


# "something bold"/"make it safer" with no occasion or rejection phrase in
# it. Without this, a message like this fell through both the
# detected_intent and is_rejection checks below, never triggering the
# real recommendation engine at all — letting Gemini freelance a full
# outfit combination on its own, ungrounded.
def is_style_only_followup(message, detected_intent, rejecting):
    return bool(detect_style_preference(message)) and not detected_intent and not rejecting


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
    # Was a hand-built minimal dict (id/category/texture/season/
    # dominant_colors only), missing fields like season_confidence that
    # filtering.py actually reads. Now reuses the SAME serializer
    # views.py's recommend() uses, so both paths get identical input.
    wardrobe_items = list(WardrobeItem.objects.filter(owner=user).order_by("id"))
    wardrobe_context = [WardrobeItemSerializer(item).data for item in wardrobe_items]
    item_lookup = {item.id: item for item in wardrobe_items}  # MOVED up — also needed below now, not just at the end for segment parsing

    preference_history = [
        {"occasion": o.occasion, "liked": True}
        for o in Outfit.objects.filter(owner=user)
    ]

    try:
        temp_c, weather_info = resolve_temperature(lat=lat, lon=lon, manual_temp=None)
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

    # FIX: these two lines were previously indented inside the `except ValueError:`
    # block above, so `detected_intent` was never assigned when resolve_temperature()
    # succeeded (e.g. location turned on) — causing an UnboundLocalError as soon as
    # `if detected_intent:` ran below. Now runs unconditionally, in both cases.
    detected_intent = detect_intent(message)
    rejecting = is_rejection(message)

    detected_style = detect_style_preference(message)
    style_preference = detected_style or (session.last_style_preference if session else None) or "safe"

    # ===================== CHANGE START =====================
    # REWRITTEN — no longer steps through the ranked list in strict order
    # (0, then 1, then 2...). Still calls the SAME get_recommendations()
    # used by the Recommendations page and freezes the SAME list onto the
    # session — grounding is unchanged. "Show me another" now picks a
    # RANDOM entry from that frozen list instead of always advancing by
    # exactly +1, only avoiding an immediate repeat of whatever was just
    # shown. No promise of any particular order or of ever running "out"
    # of options — with 2+ outfits in the list, there's always a valid
    # different pick.
    intent = None
    temp_for_lookup = temp_c
    outfit_index = 0
    recompute = False

    if detected_intent:
        intent = detected_intent
        # Restating the occasion alone should not drop an already-known
        # temperature — falls back to the session's last one, same as the
        # other two branches below already did.
        if temp_for_lookup is None and session:
            temp_for_lookup = session.last_temp_c

        same_context = (
            session and session.last_intent == intent and temp_for_lookup is not None
            and session.last_temp_c is not None and abs(temp_for_lookup - session.last_temp_c) <= 2
            and session.last_style_preference == style_preference
            and session.last_recommendation_list
        )
        if same_context:
            outfit_index = session.last_outfit_index or 0
        else:
            outfit_index = 0
            recompute = True  # new occasion, new temperature, or new style — the old frozen list no longer applies

    elif rejecting and session and session.last_intent and session.last_recommendation_list:
        intent = session.last_intent
        if temp_for_lookup is None:
            temp_for_lookup = session.last_temp_c
        # recompute stays False — reuses the frozen list, no engine call.
        pool_len = len(session.last_recommendation_list)
        if pool_len <= 1:
            outfit_index = 0  # nothing else to switch to
        else:
            previous_index = session.last_outfit_index or 0
            outfit_index = random.choice([i for i in range(pool_len) if i != previous_index])

    elif is_style_only_followup(message, detected_intent, rejecting) and session and session.last_intent:
        intent = session.last_intent
        outfit_index = 0
        recompute = True  # style genuinely changes the ranking — the old frozen list was ranked under a different style
        if temp_for_lookup is None:
            temp_for_lookup = session.last_temp_c
    # ===================== CHANGE END =====================

    recommended_outfit = "Not applicable. No occasion or temperature context is available."
    used_default_temp = False
    if intent and temp_for_lookup is None:
        temp_for_lookup = DEFAULT_TEMP_C
        used_default_temp = True

    if intent and temp_for_lookup is not None:
        try:
            # ===================== CHANGE START =====================
            # THE actual fix — this is now the ONLY place get_recommendations()
            # is ever called. Its result is immediately frozen into a
            # compact, JSON-safe list on the session, so every later
            # follow-up reads from this exact snapshot instead of
            # recomputing (which was the root cause of the out-of-order
            # 1st → 4th → 5th behavior — every message was silently
            # re-running the engine from scratch).
            if recompute or not session or not session.last_recommendation_list:
                results = get_recommendations(wardrobe_context, temp_c=temp_for_lookup, intent=intent, top_k=1, style_preference=style_preference)
                compact_list = []
                for r in results:
                    compact_list.append({
                        "top_id": r.get("top", {}).get("id") if r.get("top") else None,
                        "bottom_id": r.get("bottom", {}).get("id") if r.get("bottom") else None,
                        "jacket_id": r.get("jacket", {}).get("id") if r.get("jacket") else None,
                        "final_score": float(r.get("final_score", 0)),
                        "off_season": bool(r.get("off_season", False)),
                    })
                if session:
                    session.last_recommendation_list = compact_list
            else:
                compact_list = session.last_recommendation_list
            # ===================== CHANGE END =====================

            if not compact_list:
                recommended_outfit = (
                    "NONE FOUND. Tell the user warmly and briefly that nothing in their current "
                    "wardrobe quite comes together for this occasion/weather, and casually mention "
                    "the kind of item that might round it out — keep it conversational, vary your "
                    "phrasing, don't invent a combination that doesn't actually exist."
                )
            else:
                # ===================== CHANGE START =====================
                # outfit_index is always a valid position in compact_list
                # now (guaranteed by the random-selection logic above), so
                # the old "run past the end of the list -> EXHAUSTED" branch
                # is no longer reachable and has been removed.
                entry = compact_list[outfit_index]
                top = item_lookup.get(entry["top_id"]) if entry.get("top_id") else None
                bottom = item_lookup.get(entry["bottom_id"]) if entry.get("bottom_id") else None
                jacket = item_lookup.get(entry["jacket_id"]) if entry.get("jacket_id") else None
                recommended_outfit = {
                    "top": WardrobeItemSerializer(top).data if top else None,
                    "bottom": WardrobeItemSerializer(bottom).data if bottom else None,
                    "jacket": WardrobeItemSerializer(jacket).data if jacket else None,
                    # NOTE: assumes entry["final_score"] is a 0-1 similarity score from
                    # get_recommendations(). If it's already on a 0-100 scale, drop the *100.
                    "match_percent": round(entry["final_score"] * 100),
                    "off_season": entry["off_season"],
                }
                # ===================== CHANGE END =====================

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
                session.last_style_preference = style_preference
                session.save(update_fields=[
                    "last_intent", "last_outfit_index", "last_temp_c",
                    "last_style_preference", "last_recommendation_list",
                ])
        except Exception:
            recommended_outfit = "Not applicable. Recommendation engine error."

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

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"system_instruction": SYSTEM_PROMPT},
        )
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            raise Exception("The AI Stylist has hit its daily usage limit. Please try again later.")
        raise

    reply_text = response.text
    segments = parse_segments(reply_text)

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
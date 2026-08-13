"""
StyleMind — deterministic wardrobe filtering.
Filters wardrobe items by weather + intent BEFORE KNN runs.
"""

TOP_HALF = {"Shirt", "Top", "Warmwear"}
BOTTOM_HALF = {"Formal_Pant", "Pants", "Shorts", "Skirt"}
OUTERWEAR = {"Blazer", "Jacket"}
FULL_BODY = {"Dress"}

# Jacket/Blazer removed from these lists — outerwear is now a universal
# optional suggestion (weather-gated only), not tied to any specific intent.
INTENT_CATEGORY_MAP = {
    "Formal": {"Formal_Pant", "Shirt"},
    "Casual": {"Top", "Warmwear", "Shirt", "Pants", "Shorts"},
    "Picnic": {"Dress", "Top", "Skirt", "Shorts"},
    "Travel": {"Top", "Warmwear", "Pants"},
}
VALID_INTENTS = set(INTENT_CATEGORY_MAP.keys())


def get_weather_bucket(temp_c):
    if temp_c >= 25:
        return "summer"
    elif temp_c <= 15:
        return "winter"
    else:
        return "fall"


# Below this confidence, we don't fully trust the season label for hard
# filtering — the item is treated as "all-season" so a shaky guess can't
# silently exclude an otherwise valid match. It can still be down-ranked
# later in recommend.py based on how confident the label actually was.
SEASON_CONFIDENCE_THRESHOLD = 0.5


def passes_weather_filter(item, weather_bucket):
    if item.get("season_confidence", 1.0) < SEASON_CONFIDENCE_THRESHOLD:
        return True  # unreliable label — don't hard-filter on it
    return item["season"] == weather_bucket or item["season"] == "all-season"


def passes_intent_filter(item, intent):
    return item["category"] in INTENT_CATEGORY_MAP[intent]


def filter_wardrobe(wardrobe, temp_c, intent):
    """Weather + intent filter — for the main top/bottom/dress items."""
    if intent not in VALID_INTENTS:
        raise ValueError(f"intent must be one of {VALID_INTENTS}")
    bucket = get_weather_bucket(temp_c)
    return [
        item for item in wardrobe
        if passes_weather_filter(item, bucket) and passes_intent_filter(item, intent)
    ]


def filter_by_weather_only(wardrobe, temp_c):
    """Weather filter only, no intent restriction — used for outerwear
    (Blazer/Jacket), since a jacket suggestion should be available
    regardless of occasion, as long as it fits the weather."""
    bucket = get_weather_bucket(temp_c)
    return [item for item in wardrobe if passes_weather_filter(item, bucket)]

# When a needed category has zero items for the current season, we don't
# want to return no recommendations at all — we fall back to the closest
# season instead (e.g. a fall-weight formal pant in winter beats nothing).
# Order matters: first entry is tried first.
SEASON_FALLBACK_ORDER = {
    "winter": ["fall", "summer"],
    "summer": ["fall", "winter"],
    "fall": ["summer", "winter"],
}


def filter_wardrobe_with_fallback(wardrobe, temp_c, intent):
    """
    Same as filter_wardrobe, but if a category the intent needs comes back
    with zero items after normal filtering, retries that category alone
    against progressively less-ideal seasons (SEASON_FALLBACK_ORDER) rather
    than leaving the user with no recommendations at all.

    Items brought in via fallback are marked with season_fallback=True so
    the caller (or frontend) can distinguish them from a true seasonal match.
    """
    bucket = get_weather_bucket(temp_c)
    needed_categories = INTENT_CATEGORY_MAP[intent]

    result = filter_wardrobe(wardrobe, temp_c, intent)

    present_categories = {item["category"] for item in result}
    missing_categories = needed_categories - present_categories

    for category in missing_categories:
        for fallback_bucket in SEASON_FALLBACK_ORDER.get(bucket, []):
            fallback_items = [
                dict(item, season_fallback=True)
                for item in wardrobe
                if item["category"] == category and item["season"] == fallback_bucket
            ]
            if fallback_items:
                result.extend(fallback_items)
                break  # stop at the first fallback season that has items

    return result
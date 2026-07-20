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


def passes_weather_filter(item, weather_bucket):
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
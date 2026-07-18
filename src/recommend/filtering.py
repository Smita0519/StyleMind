"""
StyleMind — deterministic wardrobe filtering.
Filters wardrobe items by weather + intent BEFORE KNN runs.
"""

TOP_HALF = {"Shirt", "Top", "Warmwear"}
BOTTOM_HALF = {"Formal_Pant", "Pants", "Shorts", "Skirt"}
OUTERWEAR = {"Blazer", "Jacket"}
FULL_BODY = {"Dress"}

INTENT_CATEGORY_MAP = {
    "Formal": {"Blazer", "Formal_Pant", "Shirt"},
    "Casual": {"Top", "Pants", "Jacket", "Skirt", "Warmwear", "Shorts"},
    "Picnic": {"Shorts", "Top", "Skirt", "Dress"},
    "Travel": {"Pants", "Top", "Jacket", "Warmwear"},
}
VALID_INTENTS = set(INTENT_CATEGORY_MAP.keys())


def get_weather_bucket(temp_c):
    if temp_c > 25:
        return "summer"
    elif temp_c < 15:
        return "winter"
    else:
        return "fall"


def passes_weather_filter(item, weather_bucket):
    return item["season"] == weather_bucket or item["season"] == "all-season"


def passes_intent_filter(item, intent):
    return item["category"] in INTENT_CATEGORY_MAP[intent]


def filter_wardrobe(wardrobe, temp_c, intent):
    if intent not in VALID_INTENTS:
        raise ValueError(f"intent must be one of {VALID_INTENTS}")
    bucket = get_weather_bucket(temp_c)
    return [
        item for item in wardrobe
        if passes_weather_filter(item, bucket) and passes_intent_filter(item, intent)
    ]
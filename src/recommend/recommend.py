"""
StyleMind — final recommendation entry point.

Pipeline: filter wardrobe by weather+intent -> KNN pairs tops+bottoms
-> score each pair by color harmony -> combine with KNN similarity
-> return ranked outfit pairings.
"""

from src.recommend.filtering import filter_wardrobe
from src.recommend.knn import pair_top_and_bottom
from src.recommend.color_harmony import score_item_pair

KNN_WEIGHT = 0.6
COLOR_WEIGHT = 0.4


def knn_distance_to_similarity(distance):
    return 1.0 / (1.0 + distance)


def get_recommendations(wardrobe, temp_c, intent, top_k=3, knn_pool_size=5):
    """
    Main entry point.

    wardrobe: list of item dicts (each with category, season_probs,
              dominant_colors, etc. — as saved when the user uploaded them).
    temp_c:   current temperature in Celsius.
    intent:   one of "Formal", "Casual", "Picnic", "Travel".
    top_k:    how many final ranked outfit pairings to return.
    knn_pool_size: how many nearest-neighbor bottom candidates KNN
                   considers per top, before color harmony re-ranks them.

    Returns a list of dicts, sorted best-first:
      {"top": item, "bottom": item, "knn_similarity": float,
       "color_score": float, "final_score": float}
    """
    filtered = filter_wardrobe(wardrobe, temp_c, intent)
    pairings = pair_top_and_bottom(filtered, k=knn_pool_size)

    scored = []
    for pairing in pairings:
        top = pairing["top"]
        for bottom, distance in pairing["matches"]:
            knn_sim = knn_distance_to_similarity(distance)
            color_score = score_item_pair(top["dominant_colors"], bottom["dominant_colors"])
            final_score = KNN_WEIGHT * knn_sim + COLOR_WEIGHT * color_score

            scored.append({
                "top": top,
                "bottom": bottom,
                "knn_similarity": round(knn_sim, 4),
                "color_score": color_score,
                "final_score": round(final_score, 4),
            })

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored[:top_k]
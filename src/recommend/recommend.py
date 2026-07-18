from src.recommend.filtering import filter_wardrobe
from src.recommend.knn import pair_top_and_bottom, get_dresses, get_jackets
from src.recommend.color_harmony import score_item_pair

KNN_WEIGHT = 0.6
COLOR_WEIGHT = 0.4


def knn_distance_to_similarity(distance):
    return 1.0 / (1.0 + distance)


def find_best_jacket(outfit_colors, jackets):
    """Picks the jacket whose colors harmonize best with the outfit.
    Returns (jacket_item, score) or (None, None) if no jackets available."""
    if not jackets:
        return None, None
    best_jacket, best_score = None, -1
    for jacket in jackets:
        score = score_item_pair(outfit_colors, jacket["dominant_colors"])
        if score > best_score:
            best_jacket, best_score = jacket, score
    return best_jacket, round(best_score, 4)


def get_recommendations(wardrobe, temp_c, intent, top_k=3, knn_pool_size=5):
    filtered = filter_wardrobe(wardrobe, temp_c, intent)
    jackets = get_jackets(filtered)

    scored = []

    # Top + Bottom pairings (unchanged logic, now with optional jacket)
    pairings = pair_top_and_bottom(filtered, k=knn_pool_size)
    for pairing in pairings:
        top = pairing["top"]
        for bottom, distance in pairing["matches"]:
            knn_sim = knn_distance_to_similarity(distance)
            color_score = score_item_pair(top["dominant_colors"], bottom["dominant_colors"])
            final_score = KNN_WEIGHT * knn_sim + COLOR_WEIGHT * color_score

            combined_colors = top["dominant_colors"] + bottom["dominant_colors"]
            jacket, jacket_score = find_best_jacket(combined_colors, jackets)

            scored.append({
                "type": "top_bottom",
                "top": top,
                "bottom": bottom,
                "jacket": jacket,
                "jacket_color_score": jacket_score,
                "knn_similarity": round(knn_sim, 4),
                "color_score": color_score,
                "final_score": round(final_score, 4),
            })

    # Dress — standalone, no bottom, optional jacket
    for dress in get_dresses(filtered):
        jacket, jacket_score = find_best_jacket(dress["dominant_colors"], jackets)
        scored.append({
            "type": "dress",
            "top": None,
            "bottom": dress,
            "jacket": jacket,
            "jacket_color_score": jacket_score,
            "knn_similarity": None,
            "color_score": None,
            "final_score": 1.0,  # no KNN pairing to score; dress is complete on its own
        })

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored[:top_k]
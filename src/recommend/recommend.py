from src.recommend.filtering import filter_wardrobe
from src.recommend.knn import pair_top_and_bottom, get_dresses, get_jackets
from src.recommend.color_harmony import score_item_pair
from src.recommend.filtering import filter_by_weather_only

KNN_WEIGHT = 0.6
COLOR_WEIGHT = 0.4


def knn_distance_to_similarity(distance):
    return 1.0 / (1.0 + distance)


def find_best_jacket(outfit_colors, jackets, style="safe"):
    if not jackets:
        return None, None
    best_jacket, best_score = None, -1
    for jacket in jackets:
        score = score_item_pair(outfit_colors, jacket["dominant_colors"], style=style)
        if score > best_score:
            best_jacket, best_score = jacket, score
    return best_jacket, round(best_score, 4)


def get_recommendations(wardrobe, temp_c, intent, top_k=3, knn_pool_size=5, style_preference="safe"):
    filtered = filter_wardrobe(wardrobe, temp_c, intent)
    outerwear_pool = filter_by_weather_only(wardrobe, temp_c)
    jackets = get_jackets(outerwear_pool)

    scored = []

    pairings = pair_top_and_bottom(filtered, k=knn_pool_size)
    for pairing in pairings:
        top = pairing["top"]
        for bottom, distance in pairing["matches"]:
            knn_sim = knn_distance_to_similarity(distance)
            color_score = score_item_pair(top["dominant_colors"], bottom["dominant_colors"], style=style_preference)
            final_score = KNN_WEIGHT * knn_sim + COLOR_WEIGHT * color_score

            combined_colors = top["dominant_colors"] + bottom["dominant_colors"]
            jacket, jacket_score = find_best_jacket(combined_colors, jackets, style=style_preference)

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

    for dress in get_dresses(filtered):
        jacket, jacket_score = find_best_jacket(dress["dominant_colors"], jackets, style=style_preference)
        scored.append({
            "type": "dress",
            "top": None,
            "bottom": dress,
            "jacket": jacket,
            "jacket_color_score": jacket_score,
            "knn_similarity": None,
            "color_score": None,
            "final_score": 1.0,
        })

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored[:top_k]
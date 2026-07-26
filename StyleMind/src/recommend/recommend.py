from src.recommend.filtering import filter_wardrobe
from src.recommend.knn import pair_top_and_bottom, get_dresses, get_outerwear
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


def get_recommendations(wardrobe, temp_c, intent, top_k=3, knn_pool_size=5,
                         style_preference="safe", max_repeats_per_top=1):
    filtered = filter_wardrobe(wardrobe, temp_c, intent)
    outerwear_pool = filter_by_weather_only(wardrobe, temp_c)
    jackets = get_outerwear(outerwear_pool)
    if intent == "Formal":
        jackets = [j for j in jackets if j["category"] == "Blazer"]
    else:  # Casual, Picnic, Travel
        jackets = [j for j in jackets if j["category"] == "Jacket"]

    if temp_c >= 25:   # NEW: no outerwear suggested in summer heat
        jackets = []

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
                "type": "top_bottom", "top": top, "bottom": bottom, "jacket": jacket,
                "jacket_color_score": jacket_score, "knn_similarity": round(knn_sim, 4),
                "color_score": color_score, "final_score": round(final_score, 4),
            })

    for dress in get_dresses(filtered):
        jacket, jacket_score = find_best_jacket(dress["dominant_colors"], jackets, style=style_preference)
        scored.append({
            "type": "dress", "top": None, "bottom": dress, "jacket": jacket,
            "jacket_color_score": jacket_score, "knn_similarity": None,
            "color_score": None, "final_score": 1.0,
        })

    scored.sort(key=lambda x: x["final_score"], reverse=True)
    
    # greedy diversity pass: cap repeats of the same top item and same jacket
    top_counts = {}
    jacket_counts = {}
    diverse = []
    used_combos = set()

    for r in scored:
        top_id = r["top"]["id"] if r["top"] else r["bottom"]["id"]
        jacket_id = r["jacket"]["id"] if r["jacket"] else None
        combo = (top_id, r["bottom"]["id"], jacket_id)

        if top_counts.get(top_id, 0) >= max_repeats_per_top:
            continue
        if jacket_id is not None and jacket_counts.get(jacket_id, 0) >= max_repeats_per_top:
            continue

        diverse.append(r)
        used_combos.add(combo)
        top_counts[top_id] = top_counts.get(top_id, 0) + 1
        if jacket_id is not None:
            jacket_counts[jacket_id] = jacket_counts.get(jacket_id, 0) + 1

        if len(diverse) >= top_k:
            break

    # backfill: not enough distinct items to fill top_k, so allow repeats
    # now, but never show the exact same outfit (top+bottom+jacket) twice
    if len(diverse) < top_k:
        for r in scored:
            if len(diverse) >= top_k:
                break
            top_id = r["top"]["id"] if r["top"] else r["bottom"]["id"]
            jacket_id = r["jacket"]["id"] if r["jacket"] else None
            combo = (top_id, r["bottom"]["id"], jacket_id)
            if combo in used_combos:
                continue
            diverse.append(r)
            used_combos.add(combo)

    return diverse


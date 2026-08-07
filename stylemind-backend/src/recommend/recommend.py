import random
from src.recommend.filtering import filter_wardrobe_with_fallback
from src.recommend.knn import pair_top_and_bottom, get_dresses, get_outerwear
from src.recommend.color_harmony import score_item_pair
from src.recommend.filtering import filter_by_weather_only

KNN_WEIGHT = 0.6
COLOR_WEIGHT = 0.4

# How close two jacket scores need to be to count as "tied," so multiple
# similar-toned jackets take turns instead of one always winning.
JACKET_TIE_MARGIN = 0.05

# Small penalty applied to final_score when an outfit includes a
# season_fallback item (e.g. a fall-weight pant used in winter because
# nothing winter-specific was available). Keeps fallback outfits
# competitive but not favored over a true seasonal match.
SEASON_FALLBACK_PENALTY = 0.08


def knn_distance_to_similarity(distance):
    return 1.0 / (1.0 + distance)


def has_fallback_item(*items):
    """True if any of the given garments (top, bottom, dress, jacket) was
    brought in via season fallback rather than a true seasonal match."""
    return any(item is not None and item.get("season_fallback") for item in items)


def find_best_jacket(garment_colors_list, jackets, style="safe", seed_key=None):
    """
    garment_colors_list: a list of "dominant_colors" lists, one per garment
    already in the outfit — e.g. [top["dominant_colors"], bottom["dominant_colors"]]
    for a top+bottom outfit, or just [dress["dominant_colors"]] for a dress.

    The jacket is scored against EVERY garment separately and averaged, so a
    jacket that matches the top but clashes with the bottom doesn't win just
    because the bottom was ignored.

    Any jacket within JACKET_TIE_MARGIN of the best score is treated as
    "equally good." Among that tied group, the pick is deterministic per
    outfit: seed_key (e.g. the outfit's item IDs) seeds a local random
    generator, so the SAME outfit always resolves to the SAME jacket on
    repeat calls, while DIFFERENT outfits still draw from different jackets
    in the tie group — avoiding both "reran and got a different answer"
    and a single jacket dominating every recommendation.
    """
    if not jackets:
        return None, None

    scored_jackets = []
    for jacket in jackets:
        per_garment_scores = [
            score_item_pair(colors, jacket["dominant_colors"], style=style)
            for colors in garment_colors_list
        ]
        avg_score = sum(per_garment_scores) / len(per_garment_scores)
        scored_jackets.append((jacket, avg_score))

    best_score = max(score for _, score in scored_jackets)
    near_best = [(j, s) for j, s in scored_jackets if s >= best_score - JACKET_TIE_MARGIN]

    rng = random.Random(str(seed_key))  # str cast — random.Random rejects raw tuples
    jacket, score = rng.choice(near_best)
    return jacket, round(score, 4)


def get_recommendations(wardrobe, temp_c, intent, top_k=3, knn_pool_size=5,
                         style_preference="safe", max_repeats_per_item=1,
                         browse_pool_size=15):
    """
    browse_pool_size: total number of distinct ranked outfits to compute
    (>= top_k). The caller shows the first top_k as the initial view, and
    can page further into the returned list for "browse more" without a
    second scoring pass.
    """
    filtered = filter_wardrobe_with_fallback(wardrobe, temp_c, intent)
    outerwear_pool = filter_by_weather_only(wardrobe, temp_c)
    jackets = get_outerwear(outerwear_pool)
    if intent == "Formal":
        jackets = [j for j in jackets if j["category"] == "Blazer"]
    else:  # Casual, Picnic, Travel
        jackets = [j for j in jackets if j["category"] == "Jacket"]

    if temp_c >= 25 and intent != "Formal":
        jackets = []

    scored = []
    pairings = pair_top_and_bottom(filtered, k=knn_pool_size)
    for pairing in pairings:
        top = pairing["top"]
        for bottom, distance in pairing["matches"]:
            knn_sim = knn_distance_to_similarity(distance)
            color_score = score_item_pair(top["dominant_colors"], bottom["dominant_colors"], style=style_preference)
            final_score = KNN_WEIGHT * knn_sim + COLOR_WEIGHT * color_score
            if has_fallback_item(top, bottom):
                final_score -= SEASON_FALLBACK_PENALTY
            jacket, jacket_score = find_best_jacket(
                [top["dominant_colors"], bottom["dominant_colors"]], jackets,
                style=style_preference, seed_key=(top["id"], bottom["id"])
            )
            scored.append({
                "type": "top_bottom", "top": top, "bottom": bottom, "jacket": jacket,
                "jacket_color_score": jacket_score, "knn_similarity": round(knn_sim, 4),
                "color_score": color_score, "final_score": round(final_score, 4),
            })

    for dress in get_dresses(filtered):
        jacket, jacket_score = find_best_jacket([dress["dominant_colors"]], jackets, style=style_preference, seed_key=(dress["id"],))
        dress_final_score = 1.0
        if has_fallback_item(dress):
            dress_final_score -= SEASON_FALLBACK_PENALTY
        scored.append({
            "type": "dress", "top": None, "bottom": dress, "jacket": jacket,
            "jacket_color_score": jacket_score, "knn_similarity": None,
            "color_score": None, "final_score": dress_final_score,
        })

    scored.sort(key=lambda x: x["final_score"], reverse=True)

    # greedy diversity pass: cap repeats of the same top, same bottom, and
    # same jacket, up to browse_pool_size (not just top_k) so "browse more"
    # has real distinct outfits to page through, not reshuffled duplicates.
    pool_size = max(top_k, browse_pool_size)
    top_counts = {}
    bottom_counts = {}
    jacket_counts = {}
    diverse = []
    used_combos = set()

    for r in scored:
        top_id = r["top"]["id"] if r["top"] else r["bottom"]["id"]
        bottom_id = r["bottom"]["id"]
        jacket_id = r["jacket"]["id"] if r["jacket"] else None
        combo = (top_id, bottom_id, jacket_id)

        if top_counts.get(top_id, 0) >= max_repeats_per_item:
            continue
        if bottom_counts.get(bottom_id, 0) >= max_repeats_per_item:
            continue
        if jacket_id is not None and jacket_counts.get(jacket_id, 0) >= max_repeats_per_item:
            continue

        diverse.append(r)
        used_combos.add(combo)
        top_counts[top_id] = top_counts.get(top_id, 0) + 1
        bottom_counts[bottom_id] = bottom_counts.get(bottom_id, 0) + 1
        if jacket_id is not None:
            jacket_counts[jacket_id] = jacket_counts.get(jacket_id, 0) + 1

        if len(diverse) >= pool_size:
            break

    # backfill: not enough distinct items to fill the pool, so allow repeats
    # now, but bound them with a looser cap (2x the normal limit) so no
    # single item can dominate backfilled results, and never show the exact
    # same outfit (top+bottom+jacket) twice
    if len(diverse) < pool_size:
        backfill_cap = max_repeats_per_item * 2
        for r in scored:
            if len(diverse) >= pool_size:
                break
            top_id = r["top"]["id"] if r["top"] else r["bottom"]["id"]
            bottom_id = r["bottom"]["id"]
            jacket_id = r["jacket"]["id"] if r["jacket"] else None
            combo = (top_id, bottom_id, jacket_id)
            if combo in used_combos:
                continue
            if top_counts.get(top_id, 0) >= backfill_cap:
                continue
            if bottom_counts.get(bottom_id, 0) >= backfill_cap:
                continue
            if jacket_id is not None and jacket_counts.get(jacket_id, 0) >= backfill_cap:
                continue

            diverse.append(r)
            used_combos.add(combo)
            top_counts[top_id] = top_counts.get(top_id, 0) + 1
            bottom_counts[bottom_id] = bottom_counts.get(bottom_id, 0) + 1
            if jacket_id is not None:
                jacket_counts[jacket_id] = jacket_counts.get(jacket_id, 0) + 1

    return diverse
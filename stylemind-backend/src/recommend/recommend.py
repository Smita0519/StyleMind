import random
from src.recommend.filtering import (
    filter_wardrobe, filter_wardrobe_with_fallback, get_weather_bucket, get_season_tier
)
from src.recommend.knn import pair_top_and_bottom, get_dresses, get_outerwear
from src.recommend.color_harmony import score_item_pair
from src.recommend.filtering import filter_by_weather_only

KNN_WEIGHT = 0.6
COLOR_WEIGHT = 0.4

# How close two jacket scores need to be to count as "tied," so multiple
# similar-toned jackets take turns instead of one always winning.
JACKET_TIE_MARGIN = 0.05

# Penalty applied to final_score based on how well an item's season fits
# the current weather bucket. Tier 0 (exact match) = no penalty.
# Tier 1 (all-season / adjacent season, e.g. fall for winter) = small
# penalty. Tier 2 (the wrong season, e.g. summer for winter) = larger
# penalty — this is what should show the off-season badge.
TIER_PENALTY = {0: 0.0, 1: 0.05, 2: 0.15}


def season_penalty(item, weather_bucket):
    if item is None:
        return 0.0
    tier = get_season_tier(item.get("season"), weather_bucket)
    return TIER_PENALTY.get(tier, TIER_PENALTY[2])


def is_off_season(item, weather_bucket):
    return item is not None and get_season_tier(item.get("season"), weather_bucket) == 2


# ===================== CHANGE START =====================
# NEW — off-season fallback items should only ever be shown when the
# wardrobe genuinely can't produce enough TRUE seasonal outfits on its
# own. Previously, filter_wardrobe_with_fallback() pulled in a fallback
# item the moment a single category (e.g. "Shirt") had zero seasonal
# items, even if plenty of other true-season outfits existed overall —
# so an off-season pick could show up in the results even with a dozen
# good seasonal options already available. Now: we first score using
# ONLY true-seasonal items, and only reach into the fallback pool to top
# up the list if that leaves fewer than this many distinct outfits.
MIN_TRUE_SEASON_OUTFITS = 5
# ===================== CHANGE END =====================


def knn_distance_to_similarity(distance):
    return 1.0 / (1.0 + distance)

def find_best_jacket(garment_colors_list, jackets, weather_bucket, style="safe", seed_key=None):
    if not jackets:
        return None, None

    scored_jackets = []
    for jacket in jackets:
        per_garment_scores = [
            score_item_pair(colors, jacket["dominant_colors"], style=style)
            for colors in garment_colors_list
        ]
        avg_score = sum(per_garment_scores) / len(per_garment_scores)
        avg_score -= season_penalty(jacket, weather_bucket)
        scored_jackets.append((jacket, avg_score))

    best_score = max(score for _, score in scored_jackets)
    near_best = [(j, s) for j, s in scored_jackets if s >= best_score - JACKET_TIE_MARGIN]

    rng = random.Random(str(seed_key))
    jacket, score = rng.choice(near_best)
    return jacket, round(score, 4)


def score_candidates(filtered, jackets, style_preference, knn_pool_size, weather_bucket):
    scored = []
    pairings = pair_top_and_bottom(filtered, k=knn_pool_size)
    for pairing in pairings:
        top = pairing["top"]
        for bottom, distance in pairing["matches"]:
            knn_sim = knn_distance_to_similarity(distance)
            color_score = score_item_pair(top["dominant_colors"], bottom["dominant_colors"], style=style_preference)
            final_score = KNN_WEIGHT * knn_sim + COLOR_WEIGHT * color_score
            final_score -= season_penalty(top, weather_bucket)
            final_score -= season_penalty(bottom, weather_bucket)
            jacket, jacket_score = find_best_jacket(
                [top["dominant_colors"], bottom["dominant_colors"]], jackets, weather_bucket,
                style=style_preference, seed_key=(top["id"], bottom["id"])
            )
            if jacket is not None:
                final_score -= season_penalty(jacket, weather_bucket)

            # NEW — stamp off_season directly onto each piece dict (not just
            # the outfit as a whole), so the frontend can badge individual
            # items regardless of whether they got here via the fallback pass
            # or via the low-confidence "uncertain" pass-through in filtering.py.
            top = dict(top, off_season=is_off_season(top, weather_bucket))
            bottom = dict(bottom, off_season=is_off_season(bottom, weather_bucket))
            if jacket is not None:
                jacket = dict(jacket, off_season=is_off_season(jacket, weather_bucket))

            scored.append({
                "type": "top_bottom", "top": top, "bottom": bottom, "jacket": jacket,
                "jacket_color_score": jacket_score, "knn_similarity": round(knn_sim, 4),
                "color_score": color_score, "final_score": round(final_score, 4),
                "off_season": top["off_season"] or bottom["off_season"]
                    or (jacket["off_season"] if jacket is not None else False),
            })

    for dress in get_dresses(filtered):
        jacket, jacket_score = find_best_jacket([dress["dominant_colors"]], jackets, weather_bucket, style=style_preference, seed_key=(dress["id"],))
        dress_final_score = 1.0
        dress_final_score -= season_penalty(dress, weather_bucket)
        if jacket is not None:
            dress_final_score -= season_penalty(jacket, weather_bucket)

        # NEW — stamp off_season on the dress (and jacket) themselves, same as
        # top/bottom above, so the per-piece badge works for dress outfits too.
        dress = dict(dress, off_season=is_off_season(dress, weather_bucket))
        if jacket is not None:
            jacket = dict(jacket, off_season=is_off_season(jacket, weather_bucket))

        scored.append({
            "type": "dress", "top": None, "bottom": dress, "jacket": jacket,
            "jacket_color_score": jacket_score, "knn_similarity": None,
            "color_score": None, "final_score": dress_final_score,
            "off_season": dress["off_season"] or (jacket["off_season"] if jacket is not None else False),
        })
    return scored

def outfit_combo(r):
    """Identity tuple for an outfit — used to dedupe across the true-season
    and fallback passes, and within the diversity pass below."""
    top_id = r["top"]["id"] if r["top"] else r["bottom"]["id"]
    bottom_id = r["bottom"]["id"]
    jacket_id = r["jacket"]["id"] if r["jacket"] else None
    return (top_id, bottom_id, jacket_id)


def diversify(scored, pool_size, max_repeats_per_item, exclude_combos=None):
    """
    Takes an already-sorted (descending final_score) scored list and
    greedily builds a diverse pool: caps repeats of the same top, same
    bottom, and same jacket, up to pool_size, with a looser backfill pass
    if there aren't enough distinct items to fill it.

    exclude_combos: combos to skip entirely (e.g. outfits already included
    from a prior pass), so merging true-season + fallback results never
    double-lists the same outfit.
    """
    exclude_combos = exclude_combos or set()
    top_counts = {}
    bottom_counts = {}
    jacket_counts = {}
    diverse = []
    used_combos = set()

    for r in scored:
        combo = outfit_combo(r)
        if combo in exclude_combos:
            continue
        top_id, bottom_id, jacket_id = combo

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
            combo = outfit_combo(r)
            if combo in exclude_combos or combo in used_combos:
                continue
            top_id, bottom_id, jacket_id = combo
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


def get_recommendations(wardrobe, temp_c, intent, top_k=3, knn_pool_size=5,
                         style_preference="safe", max_repeats_per_item=1,
                         browse_pool_size=15):
    """
    browse_pool_size: total number of distinct ranked outfits to compute
    (>= top_k). The caller shows the first top_k as the initial view, and
    can page further into the returned list for "browse more" without a
    second scoring pass.
    """
    outerwear_pool = filter_by_weather_only(wardrobe, temp_c)
    jackets = get_outerwear(outerwear_pool)
    bucket = get_weather_bucket(temp_c) 
    if intent == "Formal":
        jackets = [j for j in jackets if j["category"] == "Blazer"]
    else:  # Casual, Picnic, Travel
        jackets = [j for j in jackets if j["category"] == "Jacket"]

    if temp_c >= 25 and intent != "Formal":
        jackets = []

    pool_size = max(top_k, browse_pool_size)

    # ===================== CHANGE START =====================
    # Pass 1 — TRUE seasonal items only, no fallback. This is what gets
    # shown whenever the wardrobe can support it.
    filtered_true = filter_wardrobe(wardrobe, temp_c, intent)
    scored_true = score_candidates(filtered_true, jackets, style_preference, knn_pool_size, bucket)
    scored_true.sort(key=lambda x: x["final_score"], reverse=True)
    diverse = diversify(scored_true, pool_size, max_repeats_per_item)

    # Pass 2 — only if the true-seasonal pool couldn't fill out even
    # MIN_TRUE_SEASON_OUTFITS distinct outfits, reach into the fallback
    # pool (off-season items) to top up the list. True-seasonal outfits
    # always come first; fallback outfits only fill remaining slots.
    if len(diverse) < MIN_TRUE_SEASON_OUTFITS:
        filtered_fallback = filter_wardrobe_with_fallback(wardrobe, temp_c, intent)
        scored_fallback = score_candidates(filtered_fallback, jackets, style_preference, knn_pool_size, bucket)
        scored_fallback.sort(key=lambda x: x["final_score"], reverse=True)

        already_included = {outfit_combo(r) for r in diverse}
        remaining_slots = pool_size - len(diverse)
        topped_up = diversify(
            scored_fallback, remaining_slots, max_repeats_per_item,
            exclude_combos=already_included,
        )
        diverse.extend(topped_up)
    # ===================== CHANGE END =====================

    return diverse
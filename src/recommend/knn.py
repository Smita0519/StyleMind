"""
StyleMind — KNN-based candidate retrieval.

Builds a feature vector per item (10-dim category one-hot + 4-dim
season_probs) and finds the nearest-neighbor items for a given item,
restricted to compatible outfit slots (top-half vs bottom-half).
"""

import numpy as np
from sklearn.neighbors import NearestNeighbors

CATEGORIES = [
    "Blazer", "Dress", "Formal_Pant", "Jacket", "Pants",
    "Shirt", "Shorts", "Skirt", "Top", "Warmwear",
]
SEASONS = ["all-season", "fall", "summer", "winter"]

TOP_HALF = {"Shirt", "Top", "Warmwear"}
BOTTOM_HALF = {"Formal_Pant", "Pants", "Shorts", "Skirt"}


def build_feature_vector(item):
    """
    item: dict with 'category' (str) and 'season_probs' (dict of 4 floats).
    Returns a 14-dim numpy array: 10-dim category one-hot + 4-dim season_probs.
    """
    cat_vec = [1.0 if item["category"] == c else 0.0 for c in CATEGORIES]
    season_vec = [item["season_probs"][s] for s in SEASONS]
    return np.array(cat_vec + season_vec, dtype=np.float32)


def find_matches(target_item, candidate_pool, k=5):
    """
    target_item: the item to find matches FOR (e.g. a top).
    candidate_pool: list of items to search within (e.g. all bottoms).
    Returns the top-k closest items from candidate_pool, each as
    (item, distance), sorted nearest-first.

    Uses Euclidean distance on the 14-dim feature vector — since
    category is one-hot, items in the SAME category are always closer
    than items in different categories, and within same-category items,
    season_probs similarity breaks the tie.
    """
    if not candidate_pool:
        return []

    k = min(k, len(candidate_pool))
    vectors = np.array([build_feature_vector(item) for item in candidate_pool])

    nn = NearestNeighbors(n_neighbors=k, metric="euclidean")
    nn.fit(vectors)

    target_vec = build_feature_vector(target_item).reshape(1, -1)
    distances, indices = nn.kneighbors(target_vec)

    return [(candidate_pool[i], float(d)) for i, d in zip(indices[0], distances[0])]


def pair_top_and_bottom(filtered_wardrobe, k=5):
    """
    Splits the filtered wardrobe into top-half and bottom-half items,
    then for each top, finds its k nearest bottom matches.

    Returns a list of dicts: {"top": item, "matches": [(bottom_item, distance), ...]}
    Dresses are skipped here since they're full-body (handled separately).
    """
    tops = [i for i in filtered_wardrobe if i["category"] in TOP_HALF]
    bottoms = [i for i in filtered_wardrobe if i["category"] in BOTTOM_HALF]

    pairings = []
    for top in tops:
        matches = find_matches(top, bottoms, k=k)
        pairings.append({"top": top, "matches": matches})
    return pairings
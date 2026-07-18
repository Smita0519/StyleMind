"""
StyleMind — visualize top recommendation pairings side by side.
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image
from src.recommend.recommend import get_recommendations

WARDROBE_JSON = "wardrobe.json"
IMAGE_FOLDER = r"G:\My Drive\StyleMind_wardrobe"
TEMP_C = 28
INTENT = "Picnic"  # one of: Formal, Casual, Picnic, Travel
TOP_K = 5


def load_img(filename):
    return Image.open(Path(IMAGE_FOLDER) / filename)


def visualize():
    with open(WARDROBE_JSON) as f:
        wardrobe = json.load(f)

    results = get_recommendations(wardrobe, temp_c=TEMP_C, intent=INTENT, top_k=TOP_K)

    if not results:
        print("No recommendations found — check filters (temp/intent) against your wardrobe categories.")
        return

    # Each row shows up to 3 panels: top (or blank), bottom/dress, jacket (or blank)
    fig, axes = plt.subplots(len(results), 3, figsize=(9, 3 * len(results)))
    if len(results) == 1:
        axes = [axes]

    for row, r in enumerate(results):
        # Panel 1: top (blank for standalone dress)
        if r["top"] is not None:
            axes[row][0].imshow(load_img(r["top"]["filename"]))
            axes[row][0].set_title(f"TOP: {r['top']['category']}")
        else:
            axes[row][0].set_title("(dress — no separate top)")
        axes[row][0].axis("off")

        # Panel 2: bottom (or the dress itself, for standalone entries)
        label = "DRESS" if r["type"] == "dress" else "BOTTOM"
        axes[row][1].imshow(load_img(r["bottom"]["filename"]))
        axes[row][1].set_title(f"{label}: {r['bottom']['category']}\nscore: {r['final_score']}")
        axes[row][1].axis("off")

        # Panel 3: optional jacket
        if r["jacket"] is not None:
            axes[row][2].imshow(load_img(r["jacket"]["filename"]))
            axes[row][2].set_title(f"+ JACKET\ncolor fit: {r['jacket_color_score']}")
        else:
            axes[row][2].set_title("(no jacket suggested)")
        axes[row][2].axis("off")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    visualize()
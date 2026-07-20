"""
StyleMind — visualize top recommendation pairings side by side.
Prompts the user for temperature and intent interactively.
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image
from src.recommend.recommend import get_recommendations

WARDROBE_JSON = "wardrobe.json"
IMAGE_FOLDER = "/content/drive/MyDrive/StyleMind_wardrobe"  # update path as needed
TOP_K = 5

VALID_INTENTS = {"Formal", "Casual", "Picnic", "Travel"}


def load_img(filename):
    return Image.open(Path(IMAGE_FOLDER) / filename)


def get_user_inputs():
    temp_c = float(input("Enter current temperature (°C): "))

    print("Choose intent: Formal / Casual / Picnic / Travel")
    intent = input("Enter intent: ").strip().capitalize()
    if intent not in VALID_INTENTS:
        raise ValueError(f"Invalid intent '{intent}'. Must be one of {VALID_INTENTS}")

    print("Choose style: Safe (neutral-friendly) / Bold (colorful contrast)")
    style = input("Enter style [safe/bold]: ").strip().lower()
    if style not in {"safe", "bold"}:
        style = "safe"  # default if left blank or mistyped

    return temp_c, intent, style


def visualize():
    with open(WARDROBE_JSON) as f:
        wardrobe = json.load(f)

    temp_c, intent, style = get_user_inputs()
    results = get_recommendations(wardrobe, temp_c=temp_c, intent=intent, top_k=TOP_K, style_preference=style)

    if not results:
        print("No recommendations found — check filters (temp/intent) against your wardrobe categories.")
        return

    fig, axes = plt.subplots(len(results), 3, figsize=(9, 3 * len(results)))
    if len(results) == 1:
        axes = [axes]

    fig.suptitle(f"Recommendations for {intent} at {temp_c}°C ({style} style)", fontsize=14)

    for row, r in enumerate(results):
        if r["top"] is not None:
            axes[row][0].imshow(load_img(r["top"]["filename"]))
            axes[row][0].set_title(f"TOP: {r['top']['category']}")
        else:
            axes[row][0].set_title("(dress — no separate top)")
        axes[row][0].axis("off")

        label = "DRESS" if r["type"] == "dress" else "BOTTOM"
        axes[row][1].imshow(load_img(r["bottom"]["filename"]))
        axes[row][1].set_title(f"{label}: {r['bottom']['category']}\nscore: {r['final_score']}")
        axes[row][1].axis("off")

        if r["jacket"] is not None:
            axes[row][2].imshow(load_img(r["jacket"]["filename"]))
            axes[row][2].set_title(f"+ JACKET\ncolor fit: {r['jacket_color_score']}")
        else:
            axes[row][2].set_title("(no jacket suggested)")
        axes[row][2].axis("off")

    plt.tight_layout()
    plt.savefig("/content/output.png", bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    visualize()
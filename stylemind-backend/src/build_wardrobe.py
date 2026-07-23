"""
StyleMind — build a wardrobe list from a folder of real images.

Runs predict() on every image in a folder, saves the results as a
wardrobe.json file (list of item dicts) ready to feed into
get_recommendations().
"""

import json
from pathlib import Path
from src.predict import predict

IMAGE_FOLDER = '/content/drive/MyDrive/StyleMind_wardrobe'   #for colab
# r"G:\My Drive\StyleMind_wardrobe" for vscode  
OUTPUT_FILE = "wardrobe.json"
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def build_wardrobe():
    folder = Path(IMAGE_FOLDER)
    if not folder.exists():
        raise FileNotFoundError(
            f"Folder '{IMAGE_FOLDER}' not found. Create it and add clothing photos."
        )

    image_paths = [p for p in folder.iterdir() if p.suffix.lower() in VALID_EXTS]
    if not image_paths:
        raise ValueError(f"No images found in '{IMAGE_FOLDER}'.")

    wardrobe = []
    for i, path in enumerate(image_paths, start=1):
        print(f"[{i}/{len(image_paths)}] Predicting {path.name}...")
        result = predict(str(path))
        result["id"] = i
        result["filename"] = path.name
        wardrobe.append(result)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(wardrobe, f, indent=2)

    print(f"\nSaved {len(wardrobe)} items to {OUTPUT_FILE}")
    return wardrobe


if __name__ == "__main__":
    build_wardrobe()
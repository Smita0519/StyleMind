import json
from pathlib import Path
from src.predict import predict

IMAGE_FOLDER = r"H:\My Drive\StyleMind_wardrobe"
OUTPUT_FILE = "wardrobe.json"
PROCESSED_FOLDER = Path("processed_images")   # NEW: local folder for bg-removed thumbnails
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

    PROCESSED_FOLDER.mkdir(exist_ok=True)   # NEW

    wardrobe = []
    for i, path in enumerate(image_paths, start=1):
        print(f"[{i}/{len(image_paths)}] Predicting {path.name}...")
        result, seg = predict(str(path), return_segmentation=True)   # CHANGED
        result["id"] = i
        result["filename"] = path.name
        wardrobe.append(result)

        seg["final"].save(PROCESSED_FOLDER / path.name)   # NEW: save bg-removed thumbnail

    with open(OUTPUT_FILE, "w") as f:
        json.dump(wardrobe, f, indent=2)

    print(f"\nSaved {len(wardrobe)} items to {OUTPUT_FILE}")
    print(f"Saved background-removed thumbnails to {PROCESSED_FOLDER}/")
    return wardrobe


if __name__ == "__main__":
    build_wardrobe()
"""
Step 4 — YOLO-seg preprocessing: background removal, crop, letterbox resize.

Per image: run YOLO-seg -> take the largest detected mask -> replace
background with white -> crop to the garment's bounding box -> letterbox
resize to 224x224 (single JPEG save, LANCZOS resampling, per the
single-encode rule — never resize/save/reopen/resize/save again).

Falls back to the original (flattened) image if mask detection fails,
and logs every fallback rather than crashing.
"""

import csv
import os
from pathlib import Path

import numpy as np
from PIL import Image

from config import (
    FALLBACK_LOG_PATH, PROCESSED_DIR, PROCESSED_MANIFEST_PATH,
    CATEGORIES, TARGET_SIZE,
)


def letterbox_resize(img, target_size=TARGET_SIZE, fill_color=(255, 255, 255)):
    w, h = img.size
    scale = target_size / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", (target_size, target_size), fill_color)
    paste_x = (target_size - new_w) // 2
    paste_y = (target_size - new_h) // 2
    canvas.paste(img_resized, (paste_x, paste_y))
    return canvas


def preprocess_dataset(manifest_rows, yolo_model, conf_threshold=0.25):
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    for category in CATEGORIES:
        os.makedirs(os.path.join(PROCESSED_DIR, category), exist_ok=True)

    fallback_log = []
    processed_manifest = []

    for i, row in enumerate(manifest_rows):
        fpath, category = row["filepath"], row["category"]
        out_name = f"{Path(fpath).stem}.jpg"
        out_path = os.path.join(PROCESSED_DIR, category, out_name)

        try:
            img = Image.open(fpath).convert("RGB")

            results = yolo_model(np.array(img), conf=conf_threshold, verbose=False)
            result = results[0]

            if result.masks is None or len(result.masks.data) == 0:
                fallback_log.append({"filepath": fpath, "reason": "no mask detected"})
                final_img = img
            else:
                mask_data = result.masks.data.cpu().numpy()
                areas = [m.sum() for m in mask_data]
                largest_idx = int(np.argmax(areas))
                mask = mask_data[largest_idx]

                mask_resized = np.array(
                    Image.fromarray((mask * 255).astype(np.uint8)).resize(img.size)
                )
                mask_bool = mask_resized > 127

                img_arr = np.array(img)
                white_arr = np.full_like(img_arr, 255)
                masked_arr = np.where(mask_bool[..., None], img_arr, white_arr)
                masked_img = Image.fromarray(masked_arr.astype(np.uint8))

                ys, xs = np.where(mask_bool)
                if len(xs) == 0 or len(ys) == 0:
                    fallback_log.append({"filepath": fpath, "reason": "empty mask after resize"})
                    final_img = img
                else:
                    x0, x1 = xs.min(), xs.max()
                    y0, y1 = ys.min(), ys.max()
                    final_img = masked_img.crop((x0, y0, x1 + 1, y1 + 1))

            final_img = letterbox_resize(final_img, TARGET_SIZE)
            final_img.save(out_path, "JPEG", quality=95)
            processed_manifest.append({"filepath": out_path, "category": category})

        except Exception as e:
            fallback_log.append({"filepath": fpath, "reason": f"error: {e}"})
            continue

        if (i + 1) % 200 == 0:
            print(f"Processed {i + 1}/{len(manifest_rows)}...")

    with open(PROCESSED_MANIFEST_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filepath", "category"])
        writer.writeheader()
        writer.writerows(processed_manifest)

    if fallback_log:
        with open(FALLBACK_LOG_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["filepath", "reason"])
            writer.writeheader()
            writer.writerows(fallback_log)
        print(f"\n{len(fallback_log)} images fell back to uncropped (see {FALLBACK_LOG_PATH})")

    print(f"\nPreprocessing done: {len(processed_manifest)} images -> {PROCESSED_DIR}")
    print(f"Processed manifest saved to {PROCESSED_MANIFEST_PATH}")
    return processed_manifest


if __name__ == "__main__":
    from config import MANIFEST_PATH
    from step3_yolo_setup import verify_class_list

    with open(MANIFEST_PATH) as f:
        manifest_rows = list(csv.DictReader(f))

    yolo_model = verify_class_list()
    preprocess_dataset(manifest_rows, yolo_model)

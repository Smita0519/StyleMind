"""
Step 1 — Convert every raw image to JPG.

Walks RAW_DATA_DIR/<category>/, flattens any transparency onto white
(avoiding alpha-channel bugs downstream), and saves into
JPG_DATA_DIR/<category>/ at near-lossless quality. Original files are
left untouched. Failures are logged, never crash the run.
"""

import csv
import os
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from config import (
    CATEGORIES, CONVERSION_LOG_PATH, JPG_DATA_DIR, JPG_QUALITY,
    RAW_DATA_DIR, VALID_EXTENSIONS,
)


def convert_to_jpg():
    failures = []
    total_converted = 0

    for category in CATEGORIES:
        src_dir = Path(RAW_DATA_DIR) / category
        dst_dir = Path(JPG_DATA_DIR) / category
        dst_dir.mkdir(parents=True, exist_ok=True)

        if not src_dir.exists():
            print(f"Folder not found, skipping: {src_dir}")
            continue

        count = 0
        for fpath in sorted(src_dir.iterdir()):
            if fpath.suffix.lower() not in VALID_EXTENSIONS:
                continue

            out_path = dst_dir / f"{fpath.stem}.jpg"

            try:
                img = Image.open(fpath)

                # Flatten transparency onto white
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    img = img.convert("RGBA")
                    white_bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                    img = Image.alpha_composite(white_bg, img).convert("RGB")
                else:
                    img = img.convert("RGB")

                # Single-encode rule: one save, no repeated lossy re-saves
                img.save(out_path, "JPEG", quality=JPG_QUALITY, subsampling=0)
                count += 1
                total_converted += 1

            except (UnidentifiedImageError, OSError) as e:
                failures.append({"filepath": str(fpath), "reason": str(e)})

        print(f"{category:15}: {count} images converted")

    if failures:
        os.makedirs(os.path.dirname(CONVERSION_LOG_PATH), exist_ok=True)
        with open(CONVERSION_LOG_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["filepath", "reason"])
            writer.writeheader()
            writer.writerows(failures)
        print(f"\n{len(failures)} files failed to convert, logged to {CONVERSION_LOG_PATH}")

    print(f"\nConversion done: {total_converted} images -> {JPG_DATA_DIR}")
    return total_converted, failures


if __name__ == "__main__":
    convert_to_jpg()

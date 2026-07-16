"""
Step 2 — Build the dataset manifest.

Scans JPG_DATA_DIR/<category>/ and records every valid image as
(filepath, category) into manifest.csv. Corrupt/unreadable files are
skipped and logged rather than crashing the run.
"""

import csv
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from config import CATEGORIES, JPG_DATA_DIR, MANIFEST_FAILED_LOG, MANIFEST_PATH


def build_manifest():
    rows = []
    failures = []

    for category in CATEGORIES:
        cat_dir = Path(JPG_DATA_DIR) / category
        if not cat_dir.exists():
            print(f"Folder not found, skipping: {cat_dir}")
            continue

        count = 0
        for fpath in sorted(cat_dir.iterdir()):
            if fpath.suffix.lower() != ".jpg":
                continue
            try:
                with Image.open(fpath) as img:
                    img.verify()
                rows.append({"filepath": str(fpath), "category": category})
                count += 1
            except (UnidentifiedImageError, OSError) as e:
                failures.append({"filepath": str(fpath), "reason": str(e)})

        print(f"{category:15}: {count} valid images")

    with open(MANIFEST_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filepath", "category"])
        writer.writeheader()
        writer.writerows(rows)

    if failures:
        with open(MANIFEST_FAILED_LOG, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["filepath", "reason"])
            writer.writeheader()
            writer.writerows(failures)
        print(f"\n{len(failures)} corrupt/unreadable files logged to {MANIFEST_FAILED_LOG}")

    print(f"\nManifest built: {len(rows)} images -> {MANIFEST_PATH}")
    return rows


if __name__ == "__main__":
    build_manifest()

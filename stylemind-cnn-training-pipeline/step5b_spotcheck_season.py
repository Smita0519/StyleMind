"""
Step 5b - Manual spot-check of season labels via contact sheets.

RUN THIS AFTER step5_clip_labeling.py, BEFORE step6 (the train/val/test
split). Purely diagnostic - writes image grids to disk, does not modify
any manifest or label.

Season is the fuzziest of the three heads by nature ('fall' vs
'all-season' have genuine semantic overlap - confirmed in the original
evaluation's confusion matrix, not a labeling bug). Before committing to
a full retrain, it's worth a 5-minute eyeball check that the new
ensembled prompts are producing sane labels, rather than discovering a
systematic mislabeling issue only after a multi-hour training run.

For each season class (summer / winter / fall / all-season), this
samples SPOTCHECK_SAMPLES_PER_CLASS images and tiles them into a grid
image saved to SPOTCHECK_DIR/<season>.jpg for a quick visual scan.
"""

import csv
import random

from PIL import Image, ImageDraw, ImageFont

from config import CLIP_LABELED_MANIFEST_PATH, SPOTCHECK_DIR, SPOTCHECK_SAMPLES_PER_CLASS

THUMB_SIZE = 150
GRID_COLS = 5


def make_contact_sheet(image_paths, label_text, out_path):
    n = len(image_paths)
    rows = (n + GRID_COLS - 1) // GRID_COLS
    sheet_w = GRID_COLS * THUMB_SIZE
    sheet_h = rows * THUMB_SIZE + 40  # header strip for the label

    sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text((10, 10), f"season = {label_text}  ({n} samples)", fill=(0, 0, 0))

    for i, img_path in enumerate(image_paths):
        try:
            thumb = Image.open(img_path).convert("RGB").resize((THUMB_SIZE, THUMB_SIZE))
        except Exception:
            thumb = Image.new("RGB", (THUMB_SIZE, THUMB_SIZE), (200, 200, 200))
        col = i % GRID_COLS
        row = i // GRID_COLS
        x = col * THUMB_SIZE
        y = 40 + row * THUMB_SIZE
        sheet.paste(thumb, (x, y))

    sheet.save(out_path, "JPEG", quality=90)


def spotcheck():
    import os

    os.makedirs(SPOTCHECK_DIR, exist_ok=True)

    with open(CLIP_LABELED_MANIFEST_PATH) as f:
        rows = list(csv.DictReader(f))

    by_season = {}
    for row in rows:
        by_season.setdefault(row["season"], []).append(row["filepath"])

    random.seed(42)
    print("Season class counts in labeled manifest:")
    for season, paths in sorted(by_season.items()):
        print(f"  {season:12}: {len(paths)}")

    for season, paths in by_season.items():
        sample = random.sample(paths, min(SPOTCHECK_SAMPLES_PER_CLASS, len(paths)))
        out_path = f"{SPOTCHECK_DIR}/{season}.jpg"
        make_contact_sheet(sample, season, out_path)
        print(f"Wrote {out_path} ({len(sample)} images)")

    print(f"\nOpen the contact sheets in {SPOTCHECK_DIR}/ and eyeball each one - "
          "does 'winter' actually look heavy/cold, does 'fall' look distinct from "
          "'all-season', etc. This is a judgment call, not a pass/fail check.")


if __name__ == "__main__":
    spotcheck()

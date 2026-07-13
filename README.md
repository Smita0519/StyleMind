# StyleMind — Garment Classification Module

This module handles garment **category**, **texture**, and **season** classification from a single clothing photo, feeding into the broader pipeline (color harmony, compatibility engine, contextual recommendations).

## What's Done

- **Dataset switched** from DeepFashion to the [Clothing Dataset (Full, High Res)](https://www.kaggle.com/datasets/agrigorev/clothing-dataset-full) (Alexey Grigorev, CC0), after identifying DeepFashion's multi-garment-per-image labeling noise as a core accuracy blocker.
- **9-class taxonomy**: shirt, blazer, pants, shorts, skirt, top, dress, warm-wear, jacket (mapped from Grigorev's ~20 raw labels.
- **Texture and season labels** generated via CLIP zero-shot inference (no ground truth existed for these attributes), with a manual **season override** applied for categories where garment type itself strongly implies season (e.g. `warm-wear` → winter, `shorts` → summer).
- **Model**: MobileNetV2 backbone (ImageNet pretrained) with three separate linear heads — `category_head`, `texture_head`, `season_head` — trained sequentially (freezing prior heads at each stage).
- **Results** (validation accuracy):
  | Head | Val Acc | Note |
  |---|---|---|
  | Category | ~88% | Strong — main signal, big improvement over DeepFashion's 63.5% |
  | Texture | ~72% | Learning CLIP's own zero-shot guesses, not human ground truth |
  | Season | ~80–82% | Partly inflated — 5/9 categories have season hardcoded by override, not learned |
- **Local demo pipeline** (`demo.py`): loads trained checkpoint + label classes, opens a native file picker, predicts category/texture/season for selected images, displays results side-by-side, loops until the user exits.

## Current Problems

1. **Thin categories**: `blazer` (109 images) and `warm-wear` (100 images) are under the ~300-image minimum for reliable fine-tuning — accuracy is expected to be weaker here specifically.
2. **Severe season class imbalance** for categories left un-overridden: e.g. `jacket`-summer had only 2 images, `pants`-winter had 1, `shirt`-winter had 1 — season head performance for these combos is unreliable despite the overall accuracy number looking fine.
3. **Missing categories entirely**: `jacket` may need supplementing depending on inspection.
4. **Texture head accuracy ceiling**: since texture labels come from CLIP zero-shot rather than human annotation, the model is learning to mimic CLIP's judgments — accuracy can't meaningfully exceed CLIP's own reliability on this data.
5. **No Google Drive integration**: training artifacts (dataset, checkpoints) currently live on Colab's local disk, which is wiped on every disconnect — requires manual re-download of checkpoints before each session ends.

## Planned Solutions

- **Teammates are actively collecting additional images** targeting the thin categories (`blazer`, `warm-wear`, `skirt`) and — where feasible — the rare season/category combos (`jacket`-summer, `pants`-winter, `shirt`-winter), to be merged into the training set before the next retrain.
- **Supplementary datasets** under consideration for `jacket` (e.g. images.cv Jacket dataset, ~457 images), pending inspection of counts.
- **Retraining plan**: merge new images into `images.csv`-equivalent format with an identity category mapping, re-run CLIP labeling only on the new rows (not the full set, to save compute), then retrain all three heads sequentially on the combined dataset.
- **Checkpoint versioning**: each retrain will overwrite `checkpoints/` in this repo with an updated commit (e.g. "Retrain with expanded dataset — added blazer/warm-wear/skirt images"), preserving prior versions in git history for comparison if needed.

## Repo Structure

```
stylemind_demo/
├── checkpoints/
│   ├── stylemind_full.pt       # trained model weights
│   └── label_classes.json      # category/texture/season label mappings
├── demo.py                     # local inference + demo script
└── requirements.txt
```

## Running the Demo

```bash
pip install -r requirements.txt
python demo.py
```

Opens a file picker to select image(s), displays predictions (category, texture, season with confidence scores) side-by-side, and asks whether to test more images before exiting.
# StyleMind — Garment Classification Module

This module handles garment **category**, **texture**, and **season**
classification from a single clothing photo, feeding into the broader
StyleMind pipeline (color harmony, compatibility engine, contextual
outfit recommendations).

## What's Done

- **10-class category taxonomy**: Blazer, Dress, Formal_Pant, Jacket,
  Pants, Shirt, Shorts, Skirt, Top, Warmwear — derived directly from
  folder-labeled source images (no relabeling needed for this head).
- **Texture (7 classes)** and **season (3 classes + a fallback outcome)**
  labels generated via CLIP zero-shot inference, since no ground truth
  existed for either attribute. A manual season override is applied for
  3 categories where garment type itself strongly implies season
  (Warmwear/Jacket → winter, Shorts → summer); the rest are labeled by
  CLIP's image–text similarity, with low-confidence cases falling back
  to `all-season` rather than forcing a guess.
- **Preprocessing pipeline**: raw images → JPG conversion → YOLO-seg
  (DeepFashion2 checkpoint) background removal, crop, letterbox resize
  to 224×224 — done before CLIP labeling so background clutter doesn't
  bias texture/season predictions.
- **Model**: MobileNetV2 backbone (ImageNet pretrained, frozen) with
  three separate classification heads — category, texture, season —
  trained **jointly** on a shared trunk (single training run, not
  sequential per-head training).
- **Results (test-set accuracy, held out from every tuning decision):**

  | Head | Test Acc | Macro F1 | Note |
  |---|---|---|---|
  | Category | 87.7% | 0.878 | Strong — main signal, all 10 classes learned directly |
  | Texture | 78.1% | 0.585 | Learning CLIP's own zero-shot judgments, not human ground truth — accuracy is bounded by CLIP's reliability on this data, not just model capacity |
  | Season | 75.1% | 0.687 | Partly aided by 3/10 categories having season hardcoded by rule, not learned |

- **Local demo pipeline** (`src/demo.py`): loads the trained checkpoint +
  label maps, opens a native file picker, predicts category/texture/season
  for the selected image, displays results side-by-side with confidence
  scores, and loops — asking whether to test another image — until the
  user chooses to exit.

## Current Problems

- **Thin/weak classes in texture**: `pleated` has only 8 examples in the
  test set and the lowest F1 of any class (0.14–0.36 depending on
  version) — support this small makes the metric noisy regardless of
  true model quality. `embroidered` also underperforms (F1 ~0.34–0.39),
  plausibly because it reads as visually close to `solid` at 224×224.
- **Season class imbalance / ambiguity**: `all-season` is a fallback
  outcome (triggered when CLIP's top-1 vs top-2 confidence gap is too
  small to trust a specific season) rather than a directly learned
  category, and it's consistently the weakest season class (F1 ~0.35–0.43).
  This reflects genuine semantic overlap between `all-season`, `fall`,
  and `summer` in CLIP's embedding space — confirmed via the confusion
  matrix — not a labeling bug.
- **Season accuracy is partly inflated**: 3 of 10 categories
  (Warmwear, Jacket, Shorts) have season hardcoded by rule rather than
  learned from CLIP or the model itself, so the blended 75.1% overstates
  how well season is actually being *learned* on the harder, rule-free
  categories.
- **Texture accuracy ceiling**: since texture labels come from CLIP
  zero-shot rather than human annotation, the model is learning to mimic
  CLIP's judgments on this dataset — it can't meaningfully exceed CLIP's
  own reliability here, only match it.
- **Checkpoint/dataset distribution**: training artifacts
  (`best_model_phase1.keras`, dataset, intermediate manifests) currently
  live on Google Drive from the Colab training runs — not yet synced or
  versioned in this repo. The model file itself may also need Git LFS if
  it exceeds GitHub's plain-push size limits.

## Planned Solutions

- Revisit CLIP prompt phrasing for `pleated`/`embroidered` before
  assuming more data alone will fix them — a similar phrasing-imbalance
  issue previously caused `winter` to structurally lose to `all-season`
  regardless of the actual image, and was fixed by rewording prompts
  rather than collecting more images.
- A manual QA pass specifically on season labels sitting near the
  confidence-margin boundary, since that boundary is what decides
  `all-season` vs. a specific season.
- Set up Git LFS for checkpoint versioning, so future retrains can be
  tracked in git history (e.g. "Retrain with rebalanced texture prompts")
  instead of manual copy-over before each session.
- Revisit whether class-weighted loss should be reconsidered for texture
  specifically — an earlier soft-weighted retrain improved texture macro
  F1 (0.599 vs. 0.585) at the cost of majority-class (`solid`) recall;
  which tradeoff is right depends on the real-world class distribution
  the deployed app will actually see.

*(This section reflects known issues as of the current model version —
update it whenever a fix ships or a new gap is found.)*

## Repo Structure

```
stylemind/
├── models/
│   ├── best_model_phase1.keras   # trained model weights
│   └── label_maps.json           # category/texture/season label mappings
├── src/
│   ├── predict.py                # reusable inference module
│   └── demo.py                   # local inference + demo script
├── pipeline/                     # training/preprocessing code (how the model was built)
│   ├── config.py
│   ├── step1_convert_to_jpg.py … step10_evaluate.py
│   ├── experiments/               # rejected approaches, kept for transparency
│   └── requirements-training.txt
├── requirements.txt               # inference-only deps
└── outputs/                       # optional saved demo results (gitignored)
```

## Running the Demo

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
python src/demo.py
```

Opens a file picker to select an image, displays predictions (category,
texture, season with confidence scores) side-by-side, and asks whether
to test another image before exiting.

See `pipeline/` for the full training/preprocessing methodology and
`pipeline/requirements-training.txt` for its separate dependencies.

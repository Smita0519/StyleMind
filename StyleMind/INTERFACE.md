# StyleMind — Classification → Recommendation Interface

This documents the contract between the **garment classification module**
(`src/predict.py`) and whatever consumes it — currently the planned
**recommendation system**. If you're building on top of this module,
this is what you can rely on.

## The function

```python
from src.predict import predict

result = predict("path/to/image.jpg")
```

- **Input**: a filesystem path (string) to a single image — `.jpg`,
  `.png`, `.webp`, `.bmp`, or anything Pillow can open.
- **Output**: a dict, always with exactly these 6 keys.
- **Side effects**: none — read-only, no writes, no caching to disk.
- **First call is slow** (~seconds — model load), later calls are fast.
  `predict()` internally lazy-loads the model once via `load_model()`;
  you don't need to call `load_model()` yourself, but you can if you
  want to control exactly when the load cost happens (e.g. at app
  startup instead of on the first user request).

## Output schema

```python
{
    'category': 'Jacket',            # str — one of 10 fixed classes
    'category_confidence': 0.94,     # float, 0.0-1.0
    'texture': 'solid',              # str — one of 7 fixed classes
    'texture_confidence': 0.81,      # float, 0.0-1.0
    'season': 'winter',              # str — one of 4 possible values
    'season_confidence': 0.88,       # float, 0.0-1.0
    'dominant_colors': ['#1a1a2e', '#4a4a5e', '#c9c9d1'],  # 3 hex strings, most dominant first
    'mask_found': True,              # bool — whether YOLO-seg detected a garment mask
}
```

`predict()` also accepts `return_segmentation=True`, which additionally
returns a second dict (`seg`) with the intermediate segmentation output
(`final`, `mask_overlay`, `foreground_pixels`, `mask_found`) — useful if
you want to show or debug the background-removal step, not needed for
plain classification use.

**`dominant_colors`** — 3 hex color strings extracted via K-Means on the
garment's masked foreground pixels (background excluded), ordered by
cluster size (most dominant first). If `mask_found` is `False` (YOLO
didn't detect a garment), colors are extracted from the whole image
instead, including background — treat colors as less reliable in that
case.

**`mask_found`** — `False` means YOLO-seg didn't detect a garment in the
image and the pipeline fell back to the original (uncropped) image, same
fallback behavior used during training preprocessing. When `False`,
treat `dominant_colors` with extra caution — background pixels weren't
excluded.

**Category** (10 classes):
`Blazer, Dress, Formal_Pant, Jacket, Pants, Shirt, Shorts, Skirt, Top, Warmwear`

**Texture** (7 classes):
`solid, striped, floral, graphic, embroidered, pleated, checkered`

**Season** (up to 4 values returned — see caveat below):
`summer, winter, fall, all-season`

The exact class lists and their index order are also available at
runtime from `models/label_maps.json` — read that directly if you need
the canonical list rather than hardcoding it, in case a future retrain
changes class counts.

## Confidence caveats — please read before using these downstream

The three heads are **not equally reliable**, and the recommendation
system should weight them accordingly rather than treating all three
confidences the same:

| Head | Test accuracy | Macro F1 | Reliability note |
|---|---|---|---|
| Category | 87.7% | 0.878 | Learned from real category labels — the most trustworthy signal |
| Texture | 78.1% | 0.585 | Labels came from CLIP zero-shot, not human ground truth — accuracy is bounded by CLIP's own reliability on this dataset, not just model skill |
| Season | 75.1% | 0.687 | 3 of 10 categories have season hardcoded by rule (Warmwear/Jacket→winter, Shorts→summer) rather than predicted — for those categories, `season_confidence` will be near-fixed, not a genuine model confidence signal |

**Practical implications for scoring/ranking logic:**
- `pleated` and `embroidered` texture predictions are the least reliable
  of the 7 classes (lowest per-class F1) — if the recommendation system
  does anything texture-sensitive (e.g. matching patterns), treat a
  `pleated`/`embroidered` prediction with more skepticism than `solid`
  or `striped`.
- `all-season` is a **fallback outcome**, not a directly-learned class —
  it fires when the underlying CLIP labeling process couldn't
  confidently pick a specific season. It's the least reliable season
  value and overlaps semantically with `fall`/`summer`. Don't treat it
  as equivalent in certainty to `summer`/`winter`/`fall`.
- Consider a confidence floor (e.g. don't act on texture predictions
  below some threshold) rather than always trusting argmax — this
  hasn't been tuned/decided yet, so use your judgment on the recommendation
  side for now.

## What this module does NOT provide yet

- **Batch prediction** — `predict()` only takes one image path at a
  time. If the recommendation system needs to score many images at
  once, either loop over `predict()` calls or ask for a batch-capable
  version to be added to `src/predict.py` (straightforward to add, not
  done yet since the demo only ever needed one image at a time).
- **A stable public API/service** — right now this is a Python module,
  imported directly (`from src.predict import predict`). If the
  recommendation system runs as a separate service/process rather than
  in the same Python process, this would need to be wrapped behind an
  API (e.g. a small Flask/FastAPI endpoint) rather than imported directly.

## Example: using it in downstream scoring logic

```python
from src.predict import predict

result = predict("uploads/user_photo.jpg")

# Naive example — treat low-confidence texture as "unknown" rather
# than trusting it outright
TEXTURE_CONFIDENCE_FLOOR = 0.5
texture = result['texture'] if result['texture_confidence'] >= TEXTURE_CONFIDENCE_FLOOR else 'unknown'

# Season 'all-season' should probably be treated as "no strong seasonal
# constraint" in scoring, not as its own hard category
season = result['season']
is_season_flexible = (season == 'all-season')
```

## Questions to resolve together before building on this

- What confidence floor (if any) should the recommendation system use
  per head?
- Should `all-season` items be scored as compatible with every season
  query, or treated as a weaker/neutral signal?
- Should `dominant_colors` be trusted the same way when `mask_found` is
  `False` (background-included fallback), or discounted/flagged
  downstream?

# StyleMind — Recommendation Pipeline (KNN + Color Harmony)

Status as of this document: core pipeline complete and tested end-to-end
on real wardrobe photos. Built on the `recommend-engine` git branch.

## What This Module Does

Given a user's wardrobe (already classified via `predict()` — category,
texture, season, dominant colors), the recommendation pipeline suggests
outfit pairings suited to the current weather and occasion.

Pipeline order:

```
filter_wardrobe()  →  pair_top_and_bottom() / get_dresses() / get_jackets()
    (weather +           (KNN nearest-neighbor
     intent rules)        matching on category +
                           season features)
                                    ↓
                         score_item_pair()
                         (color-wheel harmony
                          scoring)
                                    ↓
                         get_recommendations()
                         (weighted final ranking:
                          60% KNN similarity +
                          40% color score)
```

## Folder Structure

```
src/
├── predict.py              # classification (unchanged, pre-existing)
├── build_wardrobe.py       # NEW — batch-runs predict() over a photo folder, saves wardrobe.json
├── visualize_recommendations.py  # NEW — shows ranked outfit pairings as images
└── recommend/
    ├── __init__.py
    ├── filtering.py         # weather + intent filtering (deterministic rules)
    ├── knn.py                # feature vectors, KNN pairing, dress/jacket selection
    ├── color_harmony.py      # hue-based color pairing score
    └── recommend.py          # combines everything into final ranked output
```

## What Has Been Done

### 1. `predict.py` — one small addition
Added a `season_probs` key to `predict()`'s output: the full 4-class season
softmax (`{"summer": 0.14, "winter": 0.001, ...}`), not just the top-1 label.
Needed so KNN can compare season *distributions* between items, not just a
single hard label — gives more accurate matching for borderline items
(e.g. "mostly fall, a little summer" vs. "purely fall").

### 2. `filtering.py` — deterministic weather + intent filter
Runs before KNN. Two rules combined:
- **Weather rule**: current temperature (°C) is bucketed into
  summer / fall / winter; an item passes if its predicted season matches
  the bucket, or if predicted as `all-season`.
- **Intent rule**: each occasion (`Formal`, `Casual`, `Picnic`, `Travel`)
  maps to an allowed set of categories — e.g. `Shirt` is Formal-only,
  `Top` is the Casual equivalent.

### 3. `knn.py` — feature vectors + nearest-neighbor pairing
- Builds a 14-dimensional feature vector per item: 10-dim category
  one-hot + 4-dim `season_probs`.
- `pair_top_and_bottom()`: for every top-half item, finds its k
  nearest bottom-half items by Euclidean distance on the feature vector.
- `get_dresses()` / `get_jackets()`: pulls out full-body items (Dress)
  and outerwear (Blazer/Jacket) for separate handling (see below).

### 4. `color_harmony.py` — color-wheel compatibility scoring
- Converts hex colors to HSL, compares hues using classic color-theory
  relationships: analogous (~0–30°), triadic (~120°), complementary
  (~180°).
- **Neutrals (black/white/grey) are special-cased**: detected via low
  saturation or extreme lightness, and automatically scored as
  compatible with anything (0.9), since hue-distance math is meaningless
  for colors with no real hue.
- Returns a 0–1 score, used as a soft signal (not a hard filter — see
  Problem 3 below).

### 5. `recommend.py` — final combiner
- Merges KNN similarity (`1 / (1 + distance)`, converted so higher =
  better) with the color harmony score: `final_score = 0.6 * knn_sim +
  0.4 * color_score`.
- Handles three outfit types:
  - **Top + Bottom** pairings (the main case)
  - **Dress**, standalone — never paired with a bottom, always a
    complete outfit on its own (`final_score = 1.0`, no KNN distance to
    compute against)
  - **Jacket**, optional add-on to *any* outfit (including dresses) —
    best-matching jacket picked by color harmony against the outfit's
    combined colors; jacket fit is shown but does **not** affect the
    outfit's ranking score, so a bad jacket match never drags down an
    otherwise-good outfit.

### 6. Testing utilities
- `build_wardrobe.py`: runs `predict()` over every image in a folder,
  saves results (+ `id`, `filename`) as `wardrobe.json`.
- `visualize_recommendations.py`: loads `wardrobe.json`, calls
  `get_recommendations()`, displays the top-k results as image panels
  (top / bottom-or-dress / optional jacket) with category labels and
  scores — same visual style as the classifier's own demo.

Tested end-to-end on a real wardrobe of 51 photos (own photos +
supplementary images), synced from Google Drive via Drive for Desktop.

## Problems Faced & Solutions Chosen

| Problem | Solution |
|---|---|
| `season_probs` didn't exist — `predict()` only returned the top-1 season label, losing nuance needed for accurate KNN matching | Added `season_probs` as a new output key (backward-compatible — no existing code broke) |
| Confidence floor (should low-confidence predictions be excluded?) — flagged as an open question in `INTERFACE.md` | Left unfiltered for now: hard-filtering by confidence risks emptying a small wardrobe entirely. Confidence is available in the data if needed later, but isn't used as a cutoff yet |
| Should color harmony be a hard filter or a soft score? | Chose **soft score**, combined with KNN via weighted average (60/40). A hard filter risks zero recommendations when a wardrobe is small; a score still surfaces the best available option even if imperfect |
| Neutrals (black/white/grey) break hue-distance math (no real hue) | Detected via saturation/lightness thresholds, auto-scored as compatible with anything rather than run through hue comparison |
| Original proposal mentioned validating against the **Polyvore dataset** | Deliberately **not** used for now. Polyvore's category taxonomy and stylistic diversity (editorial photography, layered outfits, categories outside our 10 trained classes) don't match our classifier's training distribution — risks the same taxonomy-mismatch problem encountered with DeepFashion earlier. Instead, validation is done qualitatively on our own labeled wardrobe, which stays within the model's trained distribution. This is a documented, deliberate scope decision, not an oversight |
| Windows environment friction during setup: missing modules installed only partially (`pip install -r requirements.txt` silently incomplete), `ModuleNotFoundError: No module named 'src'` when running scripts directly, disk space errors during install, path backslash escaping in one-liners | Standardized on running scripts as modules (`python -m src.xxx`) from the project root so package imports resolve correctly; used `--no-cache-dir` during installs to avoid filling disk space; used raw strings (`r"..."`) for Windows paths |
| Local `test_wardrobe` folder vs. Drive-synced photos | Connected via Google Drive for Desktop (already installed) — pointed `IMAGE_FOLDER` in `build_wardrobe.py` / `visualize_recommendations.py` directly at the synced Drive folder path, no API/auth code needed |

## What Still Needs to Be Done

- **Dress + Jacket implementation just added, not yet visually confirmed** — `visualize_recommendations.py` was just updated to show 3-panel rows (top/bottom-or-dress/jacket); needs a test run to confirm dresses and jacket suggestions display correctly.
- **Dress ranking behavior needs review** — standalone dresses currently get a flat `final_score = 1.0`, which could cause them to dominate top-k results whenever available. Worth testing with a wardrobe containing dresses to see if this needs adjusting (e.g. a small score penalty, or separate ranking buckets per outfit type).
- **Jacket score is currently cosmetic** — shown to the user but not factored into `final_score`. Decide if this is the desired final behavior or if a small weighted contribution should be added.
- **No confidence-based weighting yet** — low-confidence predictions (especially `season`, and the rule-hardcoded seasons for Warmwear/Jacket/Shorts) are treated the same as high-confidence ones. Could be added as a soft ranking factor later.
- **Polyvore decision needs to be written up formally** in the project report, framed as an intentional scope adjustment (see table above for the reasoning to draw from).
- **OpenWeather API integration** — temperature is currently a manually-passed parameter (`temp_c=20`); real weather API integration is a planned follow-up, not yet started.
- **No persistent storage / database** — wardrobe data currently lives in a local `wardrobe.json` file generated per test run. Fine for demoing the pipeline; would need real storage (even lightweight, e.g. per-user JSON, or a proper database) for a multi-session or multi-user product.
- **Report/documentation polish** — this pipeline needs to be described in report language (the existing `INTERFACE.md`/`README.md` style) for the final submission, distinct from this working-notes document.
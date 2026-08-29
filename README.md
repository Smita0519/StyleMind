# StyleMind

An AI-powered outfit recommendation system. Upload photos of your wardrobe, and StyleMind classifies each garment, extracts its dominant colors, and recommends complete outfits based on weather, occasion, and color harmony.

## Architecture

# StyleMind

An AI-powered outfit recommendation system. Upload photos of your wardrobe, and StyleMind classifies each garment, extracts its dominant colors, and recommends complete outfits based on weather, occasion, and color harmony.

## Architecture

**1. Garment Classification (CNN)**
- MobileNetV2 backbone, 224×224 input, three prediction heads trained jointly (not sequentially — Phase 1 is a single multi-head training run):
  - **Category** (10 classes: Blazer, Dress, Formal_Pant, Jacket, Pants, Shirt, Shorts, Skirt, Top, Warmwear)
  - **Pattern** (7 classes: checkered, embroidered, floral, graphic, pleated, solid, striped) — internally still referred to as the "texture" head in the training pipeline code (column names, output layer name), since renaming it there would require retraining; "Pattern" is the correct user-facing term, since this head classifies print/pattern, not fabric texture
  - **Season** (4 classes: summer, winter, fall, all-season)
- Preprocessing: YOLO-seg (`deepfashion2_yolov8s-seg.pt`) for background removal/cropping only — not classification
- Labels for pattern and season are CLIP-generated (zero-shot, `ViT-L-14`/`laion2b_s32b_b82k`) via a prompt-ensemble + confidence-margin fallback, not hand-annotated
- Test accuracy (with test-time augmentation): Category 89.7%, Pattern 77.0%, Season 66.2%
- Pattern's minority classes are notably weaker than the majority `solid` class — `embroidered` (30% F1, 24 test images) and `pleated` (37% F1, 55 test images) lag well behind `solid` (87% F1, 409 of 639 test images) — the same class-imbalance pattern later identified and partially addressed for season
- A season class-imbalance issue was identified (winter has ~4x fewer training images than summer) and addressed with a class-weighted loss variant; this improved winter recall by +9.4 points (40.6% → 50.0%) at a small cost to winter precision and overall aggregate accuracy. The unweighted model is the one currently shipped; the weighted version is kept as a documented comparison (see `notebooks/cnn-training-pipeline/` training logs)
- Backbone fine-tuning (unfreezing MobileNetV2's top layers) was also tried and rejected — it overfit almost immediately given the dataset size (~3000 training images after the split) and made season accuracy slightly worse
- Dominant colors extracted via K-Means on the alpha-masked foreground (top 3 hex colors per item)
- Training pipeline in `notebooks/cnn-training-pipeline/` — actively maintained, not just archived; latest retrain was run via a Colab-prep + GPU-training split (data prep on Colab's free GPU tier, training on a local/Colab GPU)


**2. Recommendation Engine**
Pipeline: `filter → KNN → color harmony → weighted ranking`

- **Filtering** (`filtering.py`): deterministic pre-filter on weather + user intent, before any scoring
  - Weather: item passes if its predicted season matches the live-temperature bucket, or its season is all-season. Thresholds: ≥25°C summer, ≤15°C winter, else fall
  - Intent tags (Formal, Casual, Picnic, Travel/Comfort) each map to an include-list of categories; jackets/blazers are a universal optional suggestion (not gated by intent), and are excluded entirely above 25°C
- **KNN** (`knn.py`): pairs valid top-half + bottom-half items (Dress counts as both on its own) using a 14-dim feature vector — 10-dim category one-hot + 4-dim season softmax probabilities — via Euclidean distance. K=5, tuned for wardrobes of 20-100 items
- **Color Harmony** (`color_harmony.py`): converts K-Means hex colors to HSL, scores pairs against Complementary (~180°, weight 0.92), Analogous (30-60°, weight 0.85), and Triadic (~120°, weight 0.78) schemas, using each item's primary dominant color. A `style_preference` toggle ("safe" vs "bold") controls how much neutral-color pairings are favored vs. penalized
- **Final ranking** (`recommend.py`): 60% KNN similarity + 40% color score, with a greedy diversity pass to cap repeat appearances of the same top/jacket in the top-K results before backfilling with repeats if needed

**3. Backend**
- Django + JWT auth (`rest_framework_simplejwt`) — signup, login, per-user wardrobe
- PostgreSQL (local via pgAdmin)
- ML inference (`predict.py`) called as a direct Python import within Django — run together locally for now (external hosting deferred; see Deployment Notes)
- Live weather via OpenWeather API (integration in progress — currently accepts manual `temp_c` input as a fallback/mock)

## Folder Structure

```
StyleMind/
├── stylemind-backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/                     # Django settings, urls, wsgi/asgi
│   ├── wardrobe/                   # Django app: auth, uploads, endpoints
│   ├── src/
│   │   ├── predict.py              # classification + color extraction
│   │   ├── build_wardrobe.py       # batch-runs predict() over a photo folder → wardrobe.json
│   │   ├── visualize_recommendations.py
│   │   └── recommend/
│   │       ├── filtering.py
│   │       ├── knn.py
│   │       ├── color_harmony.py
│   │       └── recommend.py
│   └── models/                     # trained artifacts (best_model_phase1.keras, label_maps.json, YOLO checkpoint)
├──  stylemind-cnn-training-pipeline/      # archived: dataset prep → training → evaluation (training complete)
└── README.md
```

## Setup

```bash
cd stylemind-backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# configure DB credentials in config/settings.py or .env
python manage.py migrate
python manage.py runserver
npm run dev
```
## Create .env files
**Backend `.env`:**
```
WEATHERAPI_KEY=your-weatherapi-com-key
GEMINI_API_KEY=your-gemini-api-key
DB_PASSWORD=your-database-password
```

**Frontend `.env`:**
```
VITE_BACKEND_URL=http://localhost:8000
```


Model artifacts (`models/`) must sit as a sibling of `src/` — `predict.py` resolves paths relative to that.

## Deployment Notes

Free-tier hosting was investigated and hit real constraints:
- Hugging Face Spaces no longer offers free CPU compute for Gradio/Docker (Static Spaces only, or ZeroGPU with a narrow limit)
- Render's free tier (512MB RAM) is too small for TensorFlow + YOLO

**Current approach:** Django + `predict()` run together on a local machine for demos/defense. **Planned for the full build:** Google Cloud Run as the actual free-tier external host, once there's time to migrate.

## Known Gaps / Backlog

- Real-time OpenWeather API call (currently manual temperature input)
- Explicit jacket/blazer include/exclude toggle for the user
- "Browse more options" — surface the full scored list beyond top-K
- Rain/precipitation-aware nudge (text + icon)
- Texture/pattern compatibility scoring (deprioritized — texture head predicts pattern, not fabric)

## Commands
```bash
cd stylemind-backend
python src/build_wardrobe.py
python src\demo.py
python -m src.build_wardrobe
python -m src.visualize_recommendations
```
# StyleMind

An AI-powered outfit recommendation system. Upload photos of your wardrobe, and StyleMind classifies each garment, extracts its dominant colors, and recommends complete outfits based on weather, occasion, and color harmony. Includes an AI stylist chatbot and a virtual try-on feature.

## Architecture

**1. Garment Classification (CNN)**
- MobileNetV2 backbone, 224×224 input, three prediction heads trained sequentially:
  - **Category** (10 classes: Blazer, Dress, Formal_Pant, Jacket, Pants, Shirt, Shorts, Skirt, Top, Warmwear)
  - **Texture/pattern** (7 classes: checkered, embroidered, floral, graphic, pleated, solid, striped)
  - **Season** (4 classes: summer, winter, fall, all-season) — hardcoded by rule for Warmwear/Jacket/Shorts rather than model-predicted
- Preprocessing: YOLO-seg (`deepfashion2_yolov8s-seg.pt`) for background removal/cropping only — not classification
- Test accuracy: Category 87.7%, Texture 78.1%, Season 75.1%
- Dominant colors extracted via K-Means on the alpha-masked foreground (top 3 hex colors per item)
- Training pipeline archived in `stylemind-cnn-training-pipeline/` (dataset prep through evaluation — training is complete; reference material, not actively run)

**2. Recommendation Engine**
Pipeline: `filter → KNN → color harmony → weighted ranking`

- **Filtering** (`filtering.py`): deterministic pre-filter on weather + user intent, before any scoring
  - Weather: item passes if its predicted season matches the live-temperature bucket, or its season is all-season. Thresholds: ≥25°C summer, ≤15°C winter, else fall
  - Intent tags (Formal, Casual, Picnic, Travel/Comfort) each map to an include-list of categories; jackets/blazers are a universal optional suggestion (not gated by intent), and jackets are excluded above 25°C (blazers stay available for Formal even in summer heat)
- **KNN** (`knn.py`): pairs valid top-half + bottom-half items (Dress counts as both on its own) using a 14-dim feature vector — 10-dim category one-hot + 4-dim season softmax probabilities — via Euclidean distance. K=5, tuned for wardrobes of 20–100 items
- **Color Harmony** (`color_harmony.py`): converts K-Means hex colors to HSL, scores pairs against Monochromatic (~0–15°), Analogous (30–60°), Triadic (~120°), and Complementary (~180°) schemas, using each item's primary dominant color. A `style_preference` toggle ("safe" vs "bold") controls how neutral-color pairings and hue schemas are weighted
- **Final ranking** (`recommend.py`): 60% KNN similarity + 40% color score, with a diversity pass to cap repeat appearances of the same items across the ranked pool, and a "browse more" pagination option beyond the initial top-K

**3. Backend**
- Django + JWT auth (`rest_framework_simplejwt`) — signup, login, per-user wardrobe
- PostgreSQL (local via pgAdmin)
- ML inference (`predict.py`) called as a direct Python import within Django, with wardrobe photo processing run in a background thread so uploads return immediately while the frontend polls for completion
- Live weather via WeatherAPI.com, resolved from browser geolocation (falls back to manual `temp_c` input)
- Full REST API: auth, profile (`/api/me/`), wardrobe CRUD + favoriting + duplicate-photo detection, recommendations, saved outfits, AI stylist chat (Gemini-backed), virtual try-on, and a health-check endpoint

**4. Frontend**
- React (Vite) + React Router
- Tailwind CSS v4 (`@theme` tokens in `index.css` for design system colors/fonts)
- Mobile responsive throughout via Tailwind breakpoints
- Screens: Login/Signup, Home, Wardrobe (grid + filters + upload + favorites), AI Stylist Chatbot (dedicated page + floating widget), Try-On, Saved Outfits, Profile

**5. Virtual Try-On**
- OOTDiffusion, run via a Colab notebook (GPU required) exposing a temporary Gradio URL that the backend calls

## Folder Structure

```
StyleMind-main/
├── stylemind-backend/
│   ├── manage.py
│   ├── wardrobe.json
│   ├── .env
│   ├── media/                      # uploaded + processed images (gitignored)
│   ├── models/                     # trained artifacts (best_model_phase1.keras, label_maps.json, YOLO checkpoint)
│   ├── src/
│   │   ├── predict.py              # classification + color extraction
│   │   ├── build_wardrobe.py       # batch-runs predict() over a photo folder → wardrobe.json
│   │   ├── visualize_recommendations.py
│   │   └── recommend/
│   │       ├── filtering.py
│   │       ├── knn.py
│   │       ├── color_harmony.py
│   │       └── recommend.py
│   ├── stylemind_backend/          # Django settings, urls, wsgi/asgi
│   └── wardrobe/                   # Django app: auth, uploads, endpoints, models, serializers
├── stylemind-cnn-training-pipeline/  # archived: dataset prep → training → evaluation (training complete)
├── stylemind-frontend/
│   ├── src/
│   │   ├── components/             # Navbar, WardrobeCard, UploadModal, ChatBubble, ChatSidebar, etc.
│   │   ├── pages/                  # Login, Signup, Home, Wardrobe, Chatbot, TryOn, Outfits
│   │   ├── mock/                   # legacy placeholder data, being phased out as real endpoints land
│   │   └── lib/
│   │       └── api.js              # every backend call goes through here
│   └── .env
├── Tryon/
│   └── tryon.ipynb                 # OOTDiffusion try-on notebook (Colab/GPU only)
├── requirements.txt
└── README.md
```

## Setup

**Backend:**
```bash
cd stylemind-backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r ../requirements.txt
```

**Download model checkpoints** (not tracked in git — see `.gitignore`):
1. Download `models.zip`: `https://drive.google.com/file/d/1nDlLfOy-kLAcAHpiCGPlxSrApgWhnK_3/view?usp=drive_link`
2. Extract directly into a folder named `stylemind-backend/models/` (create it if it doesn't exist — the zip itself is flat, so don't just unzip into `stylemind-backend/` directly)
   → should result in:
   ```
   stylemind-backend/models/best_model_phase1.keras
   stylemind-backend/models/deepfashion2_yolov8s-seg.pt
   stylemind-backend/models/label_maps.json
   ```

```bash
# configure DB credentials in stylemind_backend/settings.py or .env
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd stylemind-frontend
npm install
npm run dev
```
`node_modules/` is gitignored — always `npm install` fresh after cloning.

**Try-On (optional, only needed to test virtual try-on locally):**
See "Virtual Try-On Setup" below.

## Environment Variables

**Backend `.env`:**
```
WEATHERAPI_KEY=your-weatherapi-com-key
GEMINI_API_KEY=your-gemini-api-key
DB_PASSWORD=your-database-password
OOTD_SPACE_URL=your-colab-gradio-url   # see Virtual Try-On Setup
```

**Frontend `.env`:**
```
VITE_BACKEND_URL=http://localhost:8000
```

Model artifacts (`models/`) must sit as a sibling of `src/` — `predict.py` resolves paths relative to that.

## Virtual Try-On Setup

The try-on notebook (`Tryon/tryon.ipynb`) runs OOTDiffusion and **must be run in Google Colab** (needs a GPU) — it won't run locally.

1. Open `tryon.ipynb` in Google Colab (upload it or drag it in directly)
2. Switch to a GPU runtime: `Runtime → Change runtime type → GPU`
3. Run all cells top to bottom (`Runtime → Run all`). This installs dependencies, applies compatibility patches for `basicsr`/`diffusers`, and downloads model checkpoints — the first run takes a while.
4. The final cell launches Gradio with `share=True` and prints a public URL like `https://xxxxx.gradio.live`
5. Paste that URL into `OOTD_SPACE_URL` in `stylemind-backend/.env`, then restart the Django server to pick it up

⚠️ That URL is temporary — it expires when the Colab session ends and changes on every re-run. Don't commit a live URL; anyone testing try-on locally needs to run the notebook themselves and get their own URL.

If Colab updates a package and something breaks, check the patch cells near the top of the notebook before debugging the model code itself.

## Deployment Notes

Free-tier hosting was investigated and hit real constraints:
- Hugging Face Spaces no longer offers free CPU compute for Gradio/Docker (Static Spaces only, or ZeroGPU with a narrow limit)
- Render's free tier (512MB RAM) is too small for TensorFlow + YOLO

**Current approach:** the project is not deployed — Django, `predict()`, and the frontend all run locally for demos/defense.

## Commands
```bash
cd stylemind-backend
python src/build_wardrobe.py
python -m src.build_wardrobe
python -m src.visualize_recommendations
```
"""
StyleMind pipeline - shared configuration.

LOCAL GPU VERSION (v2). Previously this pipeline ran cell-for-cell in
Google Colab against Google Drive. It now runs as a plain local Python
project - no notebook, no Drive mount. Everything is relative to
PROJECT_ROOT below, which defaults to "wherever this repo folder lives."

Before running Step 1, drop the full raw dataset (the original merged
set + any newly added images, e.g. the extra Jacket/Pants batch) into
RAW_DATA_DIR/<category>/, matching the CATEGORIES list below. The full
pipeline (Steps 1-10) is meant to be re-run start to finish on the full
dataset, not incrementally - this matters especially for Step 5, since
the labeling logic changed (see below) and old and new labeling methods
must not be mixed in one dataset.
"""

import os

# --- Project root: everything lives under here ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(PROJECT_ROOT, "data")
OUTPUT_ROOT = os.path.join(PROJECT_ROOT, "outputs")

os.makedirs(DATA_ROOT, exist_ok=True)
os.makedirs(OUTPUT_ROOT, exist_ok=True)

# --- Step 1: raw -> jpg conversion ---
RAW_DATA_DIR = os.path.join(DATA_ROOT, "raw_dataset")
JPG_DATA_DIR = os.path.join(DATA_ROOT, "raw_dataset_jpg")
CONVERSION_LOG_PATH = os.path.join(OUTPUT_ROOT, "conversion_failures.csv")
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".gif"}
JPG_QUALITY = 95

CATEGORIES = [
    "Blazer", "Dress", "Formal_Pant", "Jacket", "Pants",
    "Shirt", "Shorts", "Skirt", "Top", "Warmwear",
]

# --- Step 2: manifest ---
MANIFEST_PATH = os.path.join(OUTPUT_ROOT, "manifest.csv")
MANIFEST_FAILED_LOG = os.path.join(OUTPUT_ROOT, "manifest_failures.csv")

# --- Step 3-4: YOLO-seg background removal ---
YOLO_CHECKPOINT = os.path.join(PROJECT_ROOT, "deepfashion2_yolov8s-seg.pt")
YOLO_HF_REPO_ID = "Bingsu/adetailer"
YOLO_HF_FILENAME = "deepfashion2_yolov8s-seg.pt"

PROCESSED_DIR = os.path.join(DATA_ROOT, "processed_dataset")
PROCESSED_MANIFEST_PATH = os.path.join(OUTPUT_ROOT, "manifest_processed.csv")
FALLBACK_LOG_PATH = os.path.join(OUTPUT_ROOT, "preprocessing_fallbacks.csv")
TARGET_SIZE = 224

# --- Step 5: CLIP zero-shot labeling (v2 - CLIP-only, no rule shortcuts) ---
CLIP_LABELED_MANIFEST_PATH = os.path.join(OUTPUT_ROOT, "manifest_labeled.csv")

# Bumped up from ViT-B-32 (the Colab-era choice, picked for speed on a
# shared/limited runtime). Labeling only runs once, not per training
# epoch, so on a dedicated local GPU there's no reason to keep the small
# model - a bigger CLIP gives materially better zero-shot label quality,
# which directly raises the ceiling on texture/season accuracy since
# those heads are only as good as their (CLIP-derived) labels.
CLIP_MODEL_NAME = "ViT-L-14"
CLIP_PRETRAINED = "laion2b_s32b_b82k"

TEXTURE_CLASSES = ["solid", "striped", "floral", "graphic", "embroidered", "pleated", "checkered"]
# 'all-season' is intentionally NOT a CLIP prompt class - it's a fallback
# outcome only, produced when the CLIP top-1/top-2 confidence gap is too
# small to trust a specific season (see label_image() in step5).
SEASON_CLASSES = ["summer", "winter", "fall"]

# --- Richer, ensembled prompts (v2) ---
# Each class now has several phrasings covering different cues (fabric
# weight, construction/finish, typical wearing context, weather
# association). step5 embeds each phrasing separately and averages them
# per class before comparing to the image - this "prompt ensembling" is
# a standard way to reduce CLIP zero-shot noise versus a single prompt
# string, and is the main lever for improving texture/season label
# quality (and therefore downstream head accuracy) without touching the
# CNN itself.
TEXTURE_PROMPTS = {
    "solid": [
        "a photo of a solid-colored garment with no pattern",
        "a plain garment in a single uniform color",
        "a clothing item with a flat, unprinted surface",
        "a garment with no visible pattern or print",
        "a minimalist plain-colored piece of clothing",
    ],
    "striped": [
        "a photo of a striped garment",
        "a clothing item with parallel stripes",
        "a garment featuring horizontal or vertical stripes",
        "a piece of clothing with a repeating line pattern",
        "a striped shirt or dress fabric pattern",
    ],
    "floral": [
        "a photo of a garment with a floral pattern",
        "a clothing item printed with flowers",
        "a garment featuring a flower or botanical print",
        "fabric with a floral or nature-inspired design",
        "a piece of clothing covered in flower patterns",
    ],
    "graphic": [
        "a photo of a garment with a graphic print design",
        "a clothing item with a bold printed graphic or logo",
        "a t-shirt or top with an illustrated design print",
        "a garment featuring text or artwork printed on the fabric",
        "a piece of clothing with a large decorative graphic print",
    ],
    "embroidered": [
        "a photo of a garment with embroidered detailing",
        "a clothing item with stitched embroidery patterns",
        "fabric featuring raised thread embroidery work",
        "a garment with decorative needlework or embroidered trim",
        "a piece of clothing with hand-stitched embroidered designs",
    ],
    "pleated": [
        "a photo of a pleated garment with folded fabric texture",
        "a clothing item with vertical pleats or fabric folds",
        "a garment featuring accordion-style pleating",
        "fabric with structured folds or creases sewn in",
        "a pleated skirt or dress with ridged fabric texture",
    ],
    "checkered": [
        "a photo of a checkered or plaid patterned garment",
        "a clothing item with a checkered grid pattern",
        "fabric featuring a plaid or tartan print",
        "a garment with a crisscross checked pattern",
        "a piece of clothing in gingham or plaid fabric",
    ],
}

SEASON_PROMPTS = {
    "summer": [
        "a photo of a lightweight summer clothing item",
        "a breathable garment made for hot weather",
        "a thin, airy piece of clothing worn in summer",
        "short-sleeved or sleeveless clothing suited for heat",
        "a garment made of light fabric worn on a hot sunny day",
    ],
    "winter": [
        "a photo of a heavy warm winter clothing item",
        "a thick insulated garment worn in cold weather",
        "a heavy coat or sweater made for freezing temperatures",
        "a bulky, warm piece of clothing with heavy fabric or lining",
        "a garment worn to stay warm during snow or cold winter days",
    ],
    "fall": [
        "a photo of a medium-weight fall or autumn clothing item",
        "a garment suited for cool, crisp autumn weather",
        "a light jacket or layering piece worn in fall",
        "clothing with moderate warmth for transitional weather",
        "a medium-thickness garment worn on a cool autumn day",
    ],
}

# Categories where season used to be assumed unambiguous and CLIP was
# skipped entirely (e.g. Jacket -> winter, Shorts -> summer). REMOVED in
# v2: every image now goes through CLIP for season, no shortcuts, per
# the decision to drop rule-based labeling. Kept here (commented, not
# used) only as a record of what v1 did.
# SEASON_RULES = {"Warmwear": "winter", "Jacket": "winter", "Shorts": "summer"}

# IMPORTANT: this value was calibrated for ViT-B-32's score distribution
# (std ~0.02) and will NOT necessarily transfer to ViT-L-14, which has a
# different embedding geometry and typical top1/top2 gap. Re-run
# step5_calibrate_season_margin.py FIRST on the new CLIP model and set
# this to whatever margin lands the fallback rate in a healthy ~20-40%
# range (same method used to originally tune 0.008), before running the
# real step5_clip_labeling.py pass.
SEASON_CONFIDENCE_MARGIN = 0.008  # PLACEHOLDER - recalibrate, see above

# --- Step 5b: season spot-check contact sheets ---
SPOTCHECK_DIR = os.path.join(OUTPUT_ROOT, "season_spotcheck")
SPOTCHECK_SAMPLES_PER_CLASS = 25

# --- Step 6: train/val/test split ---
MANIFEST_TRAIN_PATH = os.path.join(OUTPUT_ROOT, "manifest_train.csv")
MANIFEST_VAL_PATH = os.path.join(OUTPUT_ROOT, "manifest_val.csv")
MANIFEST_TEST_PATH = os.path.join(OUTPUT_ROOT, "manifest_test.csv")
SPLIT_RANDOM_SEED = 42
TRAIN_FRACTION = 0.70
VAL_FRACTION_OF_REMAINDER = 0.50  # remaining 30% split evenly -> 15% val / 15% test

# --- Step 7-9: model / training ---
IMG_SIZE = 224
BATCH_SIZE = 32
LABEL_MAPS_PATH = os.path.join(OUTPUT_ROOT, "label_maps.json")

CHECKPOINT_PATH_PHASE1 = os.path.join(OUTPUT_ROOT, "best_model_phase1.keras")
PHASE1_LEARNING_RATE = 1e-3
PHASE1_MAX_EPOCHS = 30
EARLY_STOP_PATIENCE = 5

# Label smoothing (v2): a gentler alternative to class-weighted loss,
# which was tried and rejected (it hurt solid-class recall). Smoothing
# softens the target distribution instead of reweighting classes -
# discourages overconfidence on majority classes without explicitly
# penalizing the model for predicting them, which should help texture/
# season macro F1 without repeating the solid-class recall regression.
LABEL_SMOOTHING = 0.1

# ReduceLROnPlateau (v2): lets the optimizer take smaller steps as
# training converges instead of stalling at a coarser optimum and
# hitting early stopping prematurely.
REDUCE_LR_FACTOR = 0.5
REDUCE_LR_PATIENCE = 2
REDUCE_LR_MIN_LR = 1e-6

# Per-head training history (v2): CSV log + PNG plot of per-head val
# accuracy over epochs, since EarlyStopping/ModelCheckpoint watch
# combined val_loss and can mask one head still improving while another
# has plateaued. This doesn't change training behavior - purely for
# visibility/diagnosis and defense slides.
HISTORY_LOG_PATH = os.path.join(OUTPUT_ROOT, "training_history.csv")
HISTORY_PLOT_PATH = os.path.join(OUTPUT_ROOT, "training_history.png")

# --- Step 10: evaluation outputs ---
CONFUSION_CATEGORY_PATH = os.path.join(OUTPUT_ROOT, "confusion_category.png")
CONFUSION_TEXTURE_PATH = os.path.join(OUTPUT_ROOT, "confusion_texture.png")
CONFUSION_SEASON_PATH = os.path.join(OUTPUT_ROOT, "confusion_season.png")

# Test-time augmentation (v2): average predictions across the original
# image plus a few cheap augmented views at eval time. Free accuracy on
# all three heads, purely at evaluation - no retraining risk, no change
# to what the model learned.
TTA_ENABLED = True

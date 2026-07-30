"""
StyleMind pipeline — shared configuration.

This whole pipeline (steps 1-10) was developed and run in Google Colab
with Google Drive mounted, since dataset prep needs a GPU (YOLO-seg, CLIP)
and the dataset itself lives on Drive. These scripts mirror the notebook
cell-for-cell but are split into one file per step for readability.

They are included here for review/reproducibility, not meant to be run
as a local one-shot pipeline — run each step's contents as a Colab cell
(or adapt DRIVE_BASE below if running against a locally mounted/synced
copy of the same folder structure).
"""

DRIVE_BASE = "/content/drive/MyDrive"
PROJECT_DIR = f"{DRIVE_BASE}/StyleMind_self"

# --- Step 1: raw -> jpg conversion ---
RAW_DATA_DIR = f"{DRIVE_BASE}/new_dataset"
JPG_DATA_DIR = f"{DRIVE_BASE}/new_dataset_jpg"
CONVERSION_LOG_PATH = f"{PROJECT_DIR}/conversion_failures.csv"
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".gif"}
JPG_QUALITY = 95

CATEGORIES = [
    "Blazer", "Dress", "Formal_Pant", "Jacket", "Pants",
    "Shirt", "Shorts", "Skirt", "Top", "Warmwear",
]

# --- Step 2: manifest ---
MANIFEST_PATH = f"{PROJECT_DIR}/manifest.csv"
MANIFEST_FAILED_LOG = f"{PROJECT_DIR}/manifest_failures.csv"

# --- Step 3-4: YOLO-seg background removal ---
YOLO_CHECKPOINT = f"{PROJECT_DIR}/deepfashion2_yolov8s-seg.pt"
YOLO_HF_REPO_ID = "Bingsu/adetailer"
YOLO_HF_FILENAME = "deepfashion2_yolov8s-seg.pt"

PROCESSED_DIR = f"{DRIVE_BASE}/processed_dataset"
PROCESSED_MANIFEST_PATH = f"{PROJECT_DIR}/manifest_processed.csv"
FALLBACK_LOG_PATH = f"{PROJECT_DIR}/preprocessing_fallbacks.csv"
TARGET_SIZE = 224

# --- Step 5: CLIP zero-shot labeling (final, calibrated version) ---
CLIP_LABELED_MANIFEST_PATH = f"{PROJECT_DIR}/manifest_labeled.csv"
CLIP_MODEL_NAME = "ViT-B-32"
CLIP_PRETRAINED = "laion2b_s34b_b79k"

TEXTURE_CLASSES = ["solid", "striped", "floral", "graphic", "embroidered", "pleated", "checkered"]
# 'all-season' is intentionally NOT a CLIP prompt class — it's a fallback
# outcome only, produced when the CLIP top-1/top-2 confidence gap is too
# small to trust a specific season (see label_image() in step5).
SEASON_CLASSES = ["summer", "winter", "fall"]

TEXTURE_PROMPTS = {
    "solid": "a photo of a solid-colored garment with no pattern",
    "striped": "a photo of a striped garment",
    "floral": "a photo of a garment with a floral pattern",
    "graphic": "a photo of a garment with a graphic print design",
    "embroidered": "a photo of a garment with embroidered detailing",
    "pleated": "a photo of a pleated garment with folded fabric texture",
    "checkered": "a photo of a checkered or plaid patterned garment",
}
SEASON_PROMPTS = {
    "summer": "a photo of a lightweight summer clothing item",
    "winter": "a photo of a heavy warm winter clothing item",
    "fall": "a photo of a medium-weight fall or autumn clothing item",
}

# Categories where season is unambiguous enough to skip CLIP entirely
SEASON_RULES = {
    "Warmwear": "winter",
    "Jacket": "winter",
    "Shorts": "summer",
}

# Recalibrated from an initial 0.03 after data showed the actual score
# spread has std ~0.02 — 0.03 was larger than a full standard deviation,
# causing 89% of images to hit the fallback. 0.008 was tuned to land in a
# healthy ~20-40% fallback range. See experiments notes in step5 docstring.
SEASON_CONFIDENCE_MARGIN = 0.008

# --- Step 6: train/val/test split ---
MANIFEST_TRAIN_PATH = f"{PROJECT_DIR}/manifest_train.csv"
MANIFEST_VAL_PATH = f"{PROJECT_DIR}/manifest_val.csv"
MANIFEST_TEST_PATH = f"{PROJECT_DIR}/manifest_test.csv"
SPLIT_RANDOM_SEED = 42
TRAIN_FRACTION = 0.70
VAL_FRACTION_OF_REMAINDER = 0.50  # remaining 30% split evenly -> 15% val / 15% test

# --- Step 7-9: model / training ---
IMG_SIZE = 224
BATCH_SIZE = 32
LABEL_MAPS_PATH = f"{PROJECT_DIR}/label_maps.json"

CHECKPOINT_PATH_PHASE1 = f"{PROJECT_DIR}/best_model_phase1.keras"
PHASE1_LEARNING_RATE = 1e-3
PHASE1_MAX_EPOCHS = 30
EARLY_STOP_PATIENCE = 5

# --- Step 10: evaluation outputs ---
CONFUSION_CATEGORY_PATH = f"{PROJECT_DIR}/confusion_category.png"
CONFUSION_TEXTURE_PATH = f"{PROJECT_DIR}/confusion_texture.png"
CONFUSION_SEASON_PATH = f"{PROJECT_DIR}/confusion_season.png"

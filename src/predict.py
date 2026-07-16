"""
StyleMind — core inference module.

Loads the trained 3-head MobileNetV2 model (category / texture / season)
and the label maps once, then exposes a single predict() function that
any script (demo, API, batch job) can import and reuse.

This module does NOT depend on Colab, tkinter, or matplotlib — it is
pure inference logic, safe to import into a backend service later.
"""

import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from PIL import Image

# ---------------------------------------------------------------------------
# Paths — resolved relative to this file so the project runs the same
# whether launched from the repo root or from inside src/.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "best_model_phase1.keras"
LABEL_MAP_PATH = PROJECT_ROOT / "models" / "label_maps.json"

IMG_SIZE = 224

_model = None
_idx_to_category = None
_idx_to_texture = None
_idx_to_season = None


def load_model():
    """
    Loads the model + label maps into module-level globals on first call.
    Safe to call repeatedly — subsequent calls are no-ops.
    """
    global _model, _idx_to_category, _idx_to_texture, _idx_to_season

    if _model is not None:
        return

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found at {MODEL_PATH}\n"
            f"Copy best_model_phase1.keras from Google Drive into the models/ folder."
        )
    if not LABEL_MAP_PATH.exists():
        raise FileNotFoundError(
            f"Label map not found at {LABEL_MAP_PATH}\n"
            f"Copy label_maps.json from Google Drive into the models/ folder."
        )

    print("Loading StyleMind model...")
    _model = tf.keras.models.load_model(MODEL_PATH, compile=False)

    with open(LABEL_MAP_PATH) as f:
        label_maps = json.load(f)

    _idx_to_category = {v: k for k, v in label_maps["category"].items()}
    _idx_to_texture = {v: k for k, v in label_maps["texture"].items()}
    _idx_to_season = {v: k for k, v in label_maps["season"].items()}

    print(
        f"Loaded. {len(_idx_to_category)} categories, "
        f"{len(_idx_to_texture)} textures, {len(_idx_to_season)} seasons."
    )


def predict(image_path):
    """
    Runs inference on a single image and returns a dict with category,
    texture, and season predictions plus their confidences.

    This is inference-only — no YOLO background removal, no CLIP labeling.
    It mirrors exactly the normalization used during training
    (resize to 224x224, divide by 255.0).
    """
    load_model()

    img = Image.open(image_path).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    img_array = np.expand_dims(np.array(img, dtype=np.float32), axis=0)
    img_array = img_array / 255.0  # match training normalization

    category_pred, texture_pred, season_pred = _model.predict(img_array, verbose=0)

    category_idx = int(np.argmax(category_pred[0]))
    texture_idx = int(np.argmax(texture_pred[0]))
    season_idx = int(np.argmax(season_pred[0]))

    return {
        "category": _idx_to_category[category_idx],
        "category_confidence": round(float(category_pred[0][category_idx]), 4),
        "texture": _idx_to_texture[texture_idx],
        "texture_confidence": round(float(texture_pred[0][texture_idx]), 4),
        "season": _idx_to_season[season_idx],
        "season_confidence": round(float(season_pred[0][season_idx]), 4),
    }

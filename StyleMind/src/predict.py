"""
StyleMind — core inference module.
 
Loads the trained 3-head MobileNetV2 model, the YOLO-seg background
removal checkpoint, and the label maps once, then exposes predict()
for any script (demo, API, batch job) to reuse.
 
As of this version, predict() performs the SAME preprocessing the
training pipeline used (YOLO-seg background removal -> crop -> letterbox
resize) rather than a plain resize. This matters: skipping segmentation
at inference time while training used it creates a train/inference
mismatch that silently hurts accuracy. It also extracts the garment's
dominant colors via K-Means on the masked foreground pixels, for
downstream color-harmony use in the recommendation system.
"""
 
import json
from pathlib import Path
 
import numpy as np
import tensorflow as tf
from PIL import Image
 
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "models" / "best_model_phase1.keras"
LABEL_MAP_PATH = PROJECT_ROOT / "models" / "label_maps.json"
YOLO_CHECKPOINT_PATH = PROJECT_ROOT / "models" / "deepfashion2_yolov8s-seg.pt"
 
IMG_SIZE = 224
YOLO_CONF_THRESHOLD = 0.25
NUM_DOMINANT_COLORS = 3
 
_model = None
_yolo_model = None
_idx_to_category = None
_idx_to_texture = None
_idx_to_season = None
 
 
def load_model():
    """
    Loads the classification model, YOLO-seg model, and label maps into
    module-level globals on first call. Safe to call repeatedly.
    """
    global _model, _yolo_model, _idx_to_category, _idx_to_texture, _idx_to_season
 
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
    if not YOLO_CHECKPOINT_PATH.exists():
        raise FileNotFoundError(
            f"YOLO-seg checkpoint not found at {YOLO_CHECKPOINT_PATH}\n"
            f"Download deepfashion2_yolov8s-seg.pt (see README setup step 1) "
            f"into the models/ folder."
        )
 
    print("Loading StyleMind model...")
    _model = tf.keras.models.load_model(MODEL_PATH, compile=False)
 
    print("Loading YOLO-seg background removal model...")
    from ultralytics import YOLO
    _yolo_model = YOLO(str(YOLO_CHECKPOINT_PATH))
 
    with open(LABEL_MAP_PATH) as f:
        label_maps = json.load(f)
 
    _idx_to_category = {v: k for k, v in label_maps["category"].items()}
    _idx_to_texture = {v: k for k, v in label_maps["texture"].items()}
    _idx_to_season = {v: k for k, v in label_maps["season"].items()}
 
    print(
        f"Loaded. {len(_idx_to_category)} categories, "
        f"{len(_idx_to_texture)} textures, {len(_idx_to_season)} seasons."
    )
 
 
def letterbox_resize(img, target_size=IMG_SIZE, fill_color=(255, 255, 255)):
    w, h = img.size
    scale = target_size / max(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    img_resized = img.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGB", (target_size, target_size), fill_color)
    canvas.paste(img_resized, ((target_size - new_w) // 2, (target_size - new_h) // 2))
    return canvas
 
 
def segment_and_remove_background(img_path):
    """
    Runs YOLO-seg on the image and returns everything downstream needs:
      - 'final': letterboxed, background-removed image (what the model sees)
      - 'mask_overlay': original image with the segmentation mask
        highlighted in green, for showing the segmentation step in a demo UI
      - 'foreground_pixels': raw RGB pixels under the mask, for color extraction
      - 'mask_found': whether YOLO detected a garment mask at all
 
    Falls back to the plain letterboxed original if no mask is detected
    -- exactly matching how the training preprocessing pipeline handled
    the same failure case (see pipeline/step4_yolo_preprocess.py).
    """
    load_model()
 
    img = Image.open(img_path).convert("RGB")
    results = _yolo_model(np.array(img), conf=YOLO_CONF_THRESHOLD, verbose=False)
    result = results[0]
 
    if result.masks is None or len(result.masks.data) == 0:
        return {
            "final": letterbox_resize(img),
            "mask_overlay": img,
            "foreground_pixels": np.array(img).reshape(-1, 3),
            "mask_found": False,
        }
 
    mask_data = result.masks.data.cpu().numpy()
    areas = [m.sum() for m in mask_data]
    largest_idx = int(np.argmax(areas))
    mask = mask_data[largest_idx]
 
    mask_resized = np.array(Image.fromarray((mask * 255).astype(np.uint8)).resize(img.size))
    mask_bool = mask_resized > 127
    img_arr = np.array(img)
 
    # Green-tinted overlay of the detected garment region, for display only
    tint = np.zeros_like(img_arr)
    tint[..., 1] = 255
    overlay_arr = np.where(
        mask_bool[..., None],
        (0.55 * img_arr + 0.45 * tint).astype(np.uint8),
        img_arr,
    )
    mask_overlay = Image.fromarray(overlay_arr)
 
    white_arr = np.full_like(img_arr, 255)
    masked_arr = np.where(mask_bool[..., None], img_arr, white_arr)
    masked_img = Image.fromarray(masked_arr.astype(np.uint8))
 
    ys, xs = np.where(mask_bool)
    if len(xs) == 0 or len(ys) == 0:
        return {
            "final": letterbox_resize(img),
            "mask_overlay": img,
            "foreground_pixels": img_arr.reshape(-1, 3),
            "mask_found": False,
        }
 
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    cropped = masked_img.crop((x0, y0, x1 + 1, y1 + 1))
 
    return {
        "final": letterbox_resize(cropped),
        "mask_overlay": mask_overlay,
        "foreground_pixels": img_arr[mask_bool],  # only garment pixels
        "mask_found": True,
    }
 
 
def _rgb_to_hex(rgb):
    r, g, b = [int(x) for x in rgb]
    return f"#{r:02x}{g:02x}{b:02x}"
 
 
def extract_dominant_colors(foreground_pixels, k=NUM_DOMINANT_COLORS):
    """K-Means on the masked garment foreground, most dominant cluster first."""
    from sklearn.cluster import KMeans
 
    pixels = np.asarray(foreground_pixels)
    if len(pixels) < k:
        # Not enough garment pixels to cluster meaningfully
        mean_color = pixels.mean(axis=0) if len(pixels) else np.array([200, 200, 200])
        return [_rgb_to_hex(mean_color)] * k
 
    if len(pixels) > 5000:
        sample_idx = np.random.choice(len(pixels), 5000, replace=False)
        pixels = pixels[sample_idx]
 
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=42).fit(pixels)
    centers = kmeans.cluster_centers_
    counts = np.bincount(kmeans.labels_)
    order = np.argsort(-counts)
    return [_rgb_to_hex(centers[i]) for i in order]
 
 
def predict(image_path, return_segmentation=False):
    """
    Runs full inference on a single image: YOLO-seg background removal ->
    3-head classification -> dominant color extraction.
 
    Returns a dict with category/texture/season predictions, confidences,
    dominant_colors, and mask_found. If return_segmentation=True, also
    returns the intermediate segmentation dict (used by the demo UI to
    show the original/mask/model-input panels) as a second return value.
    """
    load_model()
 
    seg = segment_and_remove_background(image_path)
    img_array = np.expand_dims(np.array(seg["final"], dtype=np.float32), axis=0)
    img_array = img_array / 255.0  # match training normalization
 
    category_pred, texture_pred, season_pred = _model.predict(img_array, verbose=0)
 
    category_idx = int(np.argmax(category_pred[0]))
    texture_idx = int(np.argmax(texture_pred[0]))
    season_idx = int(np.argmax(season_pred[0]))
 
    dominant_colors = extract_dominant_colors(seg["foreground_pixels"])
 
    result = {
        "category": _idx_to_category[category_idx],
        "category_confidence": round(float(category_pred[0][category_idx]), 4),
        "texture": _idx_to_texture[texture_idx],
        "texture_confidence": round(float(texture_pred[0][texture_idx]), 4),
        "season": _idx_to_season[season_idx],
        "season_confidence": round(float(season_pred[0][season_idx]), 4),
        "season_probs": {_idx_to_season[i]: round(float(p), 4) for i, p in enumerate(season_pred[0])},
        "dominant_colors": dominant_colors,
        "mask_found": seg["mask_found"],
    }
 
    if return_segmentation:
        return result, seg
    return result
 
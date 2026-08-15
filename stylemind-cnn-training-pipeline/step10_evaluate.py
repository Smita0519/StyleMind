"""
Step 10 - Final evaluation on the held-out test set.

The test set has been fully untouched since Step 6 - no training or
tuning decision has seen it - so this is the first genuinely unbiased
read on real-world performance. This is a single, one-time evaluation;
no hyperparameters should be adjusted based on these results, since that
would leak test-set information back into "training" indirectly.

v2 CHANGE: predictions now use test-time augmentation (TTA) when
TTA_ENABLED is set in config.py. Instead of one forward pass per test
image, predictions are averaged across the original image, a horizontal
flip, and a slight center-zoom - smoothing out single-view noise for a
small but real accuracy/F1 bump on all three heads. This only affects
evaluation, not training - the model and its weights are unchanged.

Reports produced:
  - Aggregate per-head loss/accuracy (model.evaluate, no TTA - this is
    the standard Keras metric using the exact same pipeline as training)
  - Per-class precision/recall/F1 (classification_report, using TTA
    predictions when enabled)
  - Confusion matrices (saved as PNGs) for category, texture, season

Reference (pre-v2, ViT-B-32 rule-based labels, no TTA/smoothing/LR
schedule) test-set results for comparison after this retrain:
  Category - 87.7% accuracy, macro F1 0.878
  Texture  - 78.1% accuracy, macro F1 0.585
  Season   - 75.1% accuracy, macro F1 0.687

Texture and season have historically had a lower ceiling than category
because their labels come from CLIP zero-shot labeling (Step 5), which
is noisier than the human-derived category labels - not a flaw in this
evaluation or the model architecture. Season's 'all-season' class in
particular reflects genuine semantic overlap with 'fall'/'summer'
(confirmed by the confusion matrix, not a labeling bug) - see the
step5b spot-check contact sheets for a visual sanity check of this.
"""

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix

from config import (
    CHECKPOINT_PATH_PHASE1, CONFUSION_CATEGORY_PATH, CONFUSION_SEASON_PATH,
    CONFUSION_TEXTURE_PATH, IMG_SIZE, TTA_ENABLED,
)

AUTOTUNE = tf.data.AUTOTUNE


def _load_image(filepath, img_size=IMG_SIZE):
    img = tf.io.read_file(filepath)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, [img_size, img_size])
    img = tf.cast(img, tf.float32) / 255.0
    return img


def _make_view_dataset(filepaths, view, img_size=IMG_SIZE, batch_size=32):
    """
    view: "original", "flip", or "zoom" (slight center-crop-and-resize,
    i.e. a mild zoom-in - cheap, safe augmentation that doesn't distort
    color/tone, which matters since season labels are partly color/tone
    driven and heavier augmentation could interfere with that signal).
    """
    def _load_and_view(fp):
        img = _load_image(fp, img_size)
        if view == "flip":
            img = tf.image.flip_left_right(img)
        elif view == "zoom":
            crop_frac = 0.9
            crop_size = int(img_size * crop_frac)
            img = tf.image.central_crop(img, crop_frac)
            img = tf.image.resize(img, [img_size, img_size])
        return img

    ds = tf.data.Dataset.from_tensor_slices(filepaths)
    ds = ds.map(_load_and_view, num_parallel_calls=AUTOTUNE)
    ds = ds.batch(batch_size)
    ds = ds.prefetch(AUTOTUNE)
    return ds


def tta_predict(model, filepaths, img_size=IMG_SIZE, batch_size=32, views=("original", "flip", "zoom")):
    """
    Runs model.predict once per view, averages the softmax outputs across
    views for each of the three heads. Returns the same structure as a
    plain model.predict() call: [category_probs, texture_probs, season_probs].
    """
    all_view_preds = []
    for view in views:
        ds = _make_view_dataset(filepaths, view, img_size, batch_size)
        preds = model.predict(ds, verbose=0)
        all_view_preds.append(preds)  # list of 3 arrays (category, texture, season)

    averaged = []
    for head_idx in range(3):
        head_preds_per_view = [view_preds[head_idx] for view_preds in all_view_preds]
        averaged.append(np.mean(head_preds_per_view, axis=0))
    return averaged


def evaluate_model(model, test_ds, test_df, category_to_idx, texture_to_idx, season_to_idx):
    # Explicitly reload the checkpoint to be certain we're evaluating the
    # right weights, not whatever happens to be in memory
    model.load_weights(CHECKPOINT_PATH_PHASE1)

    # Standard Keras aggregate metrics - same pipeline as training, no TTA,
    # for a clean apples-to-apples loss/accuracy number
    test_results = model.evaluate(test_ds, return_dict=True)
    print("=== Test Set Results (standard, no TTA) ===")
    for key, value in test_results.items():
        print(f"{key}: {value:.4f}")

    category_classes = sorted(category_to_idx, key=category_to_idx.get)
    texture_classes = sorted(texture_to_idx, key=texture_to_idx.get)
    season_classes = sorted(season_to_idx, key=season_to_idx.get)

    if TTA_ENABLED:
        print("\nRunning test-time augmentation (original + flip + zoom, averaged)...")
        y_pred = tta_predict(model, test_df["filepath"].values)
    else:
        y_pred = model.predict(test_ds)

    category_pred_idx = np.argmax(y_pred[0], axis=1)
    texture_pred_idx = np.argmax(y_pred[1], axis=1)
    season_pred_idx = np.argmax(y_pred[2], axis=1)

    category_true_idx = test_df["category"].map(category_to_idx).values
    texture_true_idx = test_df["texture"].map(texture_to_idx).values
    season_true_idx = test_df["season"].map(season_to_idx).values

    label = "with TTA" if TTA_ENABLED else "no TTA"

    print("\n" + "=" * 60)
    print(f"CATEGORY - per-class report ({label})")
    print("=" * 60)
    print(classification_report(category_true_idx, category_pred_idx, target_names=category_classes, digits=3))

    print("=" * 60)
    print(f"TEXTURE - per-class report ({label})")
    print("=" * 60)
    print(classification_report(texture_true_idx, texture_pred_idx, target_names=texture_classes, digits=3))

    print("=" * 60)
    print(f"SEASON - per-class report ({label})")
    print("=" * 60)
    print(classification_report(season_true_idx, season_pred_idx, target_names=season_classes, digits=3))

    _plot_confusion(category_true_idx, category_pred_idx, category_classes, "Category Confusion Matrix", CONFUSION_CATEGORY_PATH)
    _plot_confusion(texture_true_idx, texture_pred_idx, texture_classes, "Texture Confusion Matrix", CONFUSION_TEXTURE_PATH)
    _plot_confusion(season_true_idx, season_pred_idx, season_classes, "Season Confusion Matrix", CONFUSION_SEASON_PATH)

    return test_results


def _plot_confusion(y_true, y_pred, class_names, title, save_path):
    import matplotlib.pyplot as plt
    import seaborn as sns

    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(max(6, len(class_names) * 0.9), max(5, len(class_names) * 0.8)))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=class_names, yticklabels=class_names)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    import pandas as pd

    from config import MANIFEST_TEST_PATH
    from step7_build_tf_datasets import build_datasets
    from step9_train_phase1 import train_phase1

    # If you already have a trained model + datasets in memory, skip
    # train_phase1() and just call evaluate_model() directly.
    model, base_model, history, datasets, label_maps = train_phase1()
    _, _, test_ds = datasets
    category_to_idx, texture_to_idx, season_to_idx = label_maps
    test_df = pd.read_csv(MANIFEST_TEST_PATH)

    evaluate_model(model, test_ds, test_df, category_to_idx, texture_to_idx, season_to_idx)

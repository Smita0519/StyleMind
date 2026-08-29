"""
Step 10b - Final test-set evaluation of the shipped model (Phase 1).

Simplified from the earlier version: originally compared Phase 1 against
a season-weighted variant, but that variant was dropped (it improved
winter recall at the cost of overall season accuracy and added a second
model to maintain/explain for not enough benefit) - Phase 1 is the only
shipped model now. This just evaluates it cleanly and produces one
confusion matrix per head.

Note on naming: internally (column names in the manifest CSVs, the
model's output layer name, variables below) this head is still called
"texture" - that's what it was trained/saved as, and renaming it in
code would need touching the manifests and retraining. "Pattern" is
used in all printed output and plot titles here since that's the
correct user-facing term (this head classifies print/pattern, not
fabric texture).

Unlike step10_evaluate.py, this does NOT retrain anything - it builds a
bare (uncompiled) model architecture and loads pretrained weights
directly via model.load_weights(), which sidesteps needing to
deserialize the custom loss function the checkpoint was originally
compiled with (irrelevant for evaluation - we only need weights + a
metric to compute accuracy from, not the exact training-time loss).

Test-time augmentation (TTA) is used, matching config.py's TTA_ENABLED.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix

from config import CHECKPOINT_PATH_PHASE1, IMG_SIZE, MANIFEST_TEST_PATH, OUTPUT_ROOT, TTA_ENABLED
import os
from step7_build_tf_datasets import build_datasets
from step8_build_model import build_model

AUTOTUNE = tf.data.AUTOTUNE


def _load_image(filepath, img_size=IMG_SIZE):
    img = tf.io.read_file(filepath)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, [img_size, img_size])
    img = tf.cast(img, tf.float32) / 255.0
    return img


def _make_view_dataset(filepaths, view, img_size=IMG_SIZE, batch_size=32):
    def _load_and_view(fp):
        img = _load_image(fp, img_size)
        if view == "flip":
            img = tf.image.flip_left_right(img)
        elif view == "zoom":
            crop_frac = 0.9
            img = tf.image.central_crop(img, crop_frac)
            img = tf.image.resize(img, [img_size, img_size])
        return img

    ds = tf.data.Dataset.from_tensor_slices(filepaths)
    ds = ds.map(_load_and_view, num_parallel_calls=AUTOTUNE)
    ds = ds.batch(batch_size)
    ds = ds.prefetch(AUTOTUNE)
    return ds


def tta_predict(model, filepaths, views=("original", "flip", "zoom")):
    all_view_preds = []
    for view in views:
        ds = _make_view_dataset(filepaths, view)
        preds = model.predict(ds, verbose=0)
        all_view_preds.append(preds)

    averaged = []
    for head_idx in range(3):
        head_preds_per_view = [vp[head_idx] for vp in all_view_preds]
        averaged.append(np.mean(head_preds_per_view, axis=0))
    return averaged


def _plot_confusion(y_true, y_pred, class_names, head_name, save_path):
    import matplotlib.pyplot as plt
    import seaborn as sns

    cm = confusion_matrix(y_true, y_pred)
    n = len(class_names)
    plt.figure(figsize=(max(6, n * 0.9), max(5, n * 0.8)))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=class_names, yticklabels=class_names)
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title(f"{head_name} Confusion Matrix — Test Set")
    plt.tight_layout()
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.show()
    print(f"Saved -> {save_path}")


def evaluate_checkpoint(checkpoint_path, test_df, category_to_idx, texture_to_idx, season_to_idx):
    print("\n" + "#" * 70)
    print(f"# StyleMind CNN — Final Test-Set Evaluation  ({checkpoint_path})")
    print("#" * 70)

    model, _ = build_model(
        num_category=len(category_to_idx),
        num_texture=len(texture_to_idx),
        num_season=len(season_to_idx),
    )
    model.load_weights(checkpoint_path)

    if TTA_ENABLED:
        y_pred = tta_predict(model, test_df["filepath"].values)
    else:
        filepaths = test_df["filepath"].values
        ds = tf.data.Dataset.from_tensor_slices(filepaths).map(_load_image).batch(32).prefetch(AUTOTUNE)
        y_pred = model.predict(ds, verbose=0)

    category_pred_idx = np.argmax(y_pred[0], axis=1)
    pattern_pred_idx = np.argmax(y_pred[1], axis=1)
    season_pred_idx = np.argmax(y_pred[2], axis=1)

    category_true_idx = test_df["category"].map(category_to_idx).values
    pattern_true_idx = test_df["texture"].map(texture_to_idx).values
    season_true_idx = test_df["season"].map(season_to_idx).values

    overall_category_acc = (category_pred_idx == category_true_idx).mean()
    overall_pattern_acc = (pattern_pred_idx == pattern_true_idx).mean()
    overall_season_acc = (season_pred_idx == season_true_idx).mean()

    print(f"\nOverall test accuracy — category: {overall_category_acc:.4f}  "
          f"pattern: {overall_pattern_acc:.4f}  season: {overall_season_acc:.4f}")

    tta_label = "with TTA" if TTA_ENABLED else "no TTA"

    category_classes = sorted(category_to_idx, key=category_to_idx.get)
    pattern_classes = sorted(texture_to_idx, key=texture_to_idx.get)
    season_classes = sorted(season_to_idx, key=season_to_idx.get)

    print(f"\nCATEGORY - per-class report ({tta_label})")
    print(classification_report(
        category_true_idx, category_pred_idx, target_names=category_classes, digits=3,
    ))

    print(f"\nPATTERN - per-class report ({tta_label})")
    print(classification_report(
        pattern_true_idx, pattern_pred_idx, target_names=pattern_classes, digits=3,
    ))

    print(f"\nSEASON - per-class report ({tta_label})")
    print(classification_report(
        season_true_idx, season_pred_idx, target_names=season_classes, digits=3,
    ))

    _plot_confusion(category_true_idx, category_pred_idx, category_classes, "Category",
                     os.path.join(OUTPUT_ROOT, "confusion_category.png"))
    _plot_confusion(pattern_true_idx, pattern_pred_idx, pattern_classes, "Pattern",
                     os.path.join(OUTPUT_ROOT, "confusion_pattern.png"))
    _plot_confusion(season_true_idx, season_pred_idx, season_classes, "Season",
                     os.path.join(OUTPUT_ROOT, "confusion_season.png"))


def main():
    _, _, _, label_maps = build_datasets()
    category_to_idx, texture_to_idx, season_to_idx = label_maps
    test_df = pd.read_csv(MANIFEST_TEST_PATH)

    evaluate_checkpoint(CHECKPOINT_PATH_PHASE1, test_df, category_to_idx, texture_to_idx, season_to_idx)


if __name__ == "__main__":
    main()
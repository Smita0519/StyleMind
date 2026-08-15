"""
Step 10b - Compare two trained checkpoints on the held-out test set.

Built to answer one specific question: did season-weighted training
actually help winter (and other rare season classes), even though its
OVERALL season accuracy came in slightly below phase 1's? Aggregate
accuracy can hide a real per-class tradeoff (e.g. winter recall up,
summer accuracy down, roughly cancelling out) - this prints per-class
precision/recall/F1 for season specifically so that tradeoff is visible
instead of guessed at.

Unlike step10_evaluate.py, this does NOT retrain anything - it builds a
bare (uncompiled) model architecture and loads pretrained weights
directly via model.load_weights(), which sidesteps needing to
deserialize the custom loss functions each checkpoint was originally
compiled with (irrelevant for evaluation - we only need weights + a
metric to compute accuracy from, not the exact training-time loss).

Test-time augmentation (TTA) is used for both checkpoints, matching
config.py's TTA_ENABLED, so the comparison is apples-to-apples with
step10_evaluate.py's methodology.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import classification_report

from config import IMG_SIZE, MANIFEST_TEST_PATH, OUTPUT_ROOT, TTA_ENABLED
import os
from step7_build_tf_datasets import build_datasets
from step8_build_model import build_model

AUTOTUNE = tf.data.AUTOTUNE

CHECKPOINT_PHASE1 = os.path.join(OUTPUT_ROOT, "best_model_phase1.keras")
CHECKPOINT_SEASON_WEIGHTED = os.path.join(OUTPUT_ROOT, "best_model_season_weighted.keras")


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


def evaluate_checkpoint(checkpoint_path, label, test_df, category_to_idx, texture_to_idx, season_to_idx):
    print("\n" + "#" * 70)
    print(f"# {label}  ({checkpoint_path})")
    print("#" * 70)

    model, _ = build_model(
        num_category=len(category_to_idx),
        num_texture=len(texture_to_idx),
        num_season=len(season_to_idx),
    )
    model.load_weights(checkpoint_path)

    season_classes = sorted(season_to_idx, key=season_to_idx.get)

    if TTA_ENABLED:
        y_pred = tta_predict(model, test_df["filepath"].values)
    else:
        # build a plain eval dataset if TTA is off
        filepaths = test_df["filepath"].values
        ds = tf.data.Dataset.from_tensor_slices(filepaths).map(_load_image).batch(32).prefetch(AUTOTUNE)
        y_pred = model.predict(ds, verbose=0)

    season_pred_idx = np.argmax(y_pred[2], axis=1)
    season_true_idx = test_df["season"].map(season_to_idx).values

    overall_season_acc = (season_pred_idx == season_true_idx).mean()
    print(f"\nOverall season accuracy: {overall_season_acc:.4f}")

    print(f"\nSEASON - per-class report ({'with TTA' if TTA_ENABLED else 'no TTA'})")
    print(classification_report(
        season_true_idx, season_pred_idx, target_names=season_classes, digits=3,
    ))

    return season_true_idx, season_pred_idx, season_classes


def main():
    _, _, _, label_maps = build_datasets()
    category_to_idx, texture_to_idx, season_to_idx = label_maps
    test_df = pd.read_csv(MANIFEST_TEST_PATH)

    evaluate_checkpoint(CHECKPOINT_PHASE1, "PHASE 1 (frozen backbone, unweighted)",
                        test_df, category_to_idx, texture_to_idx, season_to_idx)

    evaluate_checkpoint(CHECKPOINT_SEASON_WEIGHTED, "SEASON-WEIGHTED (frozen backbone, winter upweighted)",
                        test_df, category_to_idx, texture_to_idx, season_to_idx)

    print("\n" + "=" * 70)
    print("Compare the two 'winter' rows above (precision/recall/F1) directly -")
    print("that's the number that tells you whether the weighting actually helped")
    print("the class it targeted, regardless of what overall season accuracy showed.")
    print("=" * 70)


if __name__ == "__main__":
    main()

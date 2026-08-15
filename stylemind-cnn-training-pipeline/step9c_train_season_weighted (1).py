"""
Step 9c - Continue from phase 1, this time weighting the season loss to
counter its class imbalance (winter: 471 vs summer: 1836 in the raw
dataset - roughly 4x).

Phase 2 (unfreezing the backbone) was tried and made things WORSE - it
overfit almost immediately (val_loss got worse every epoch after the
first). This script does NOT touch the backbone - it stays frozen, same
as phase 1 - and instead addresses the season head's actual bottleneck
directly: imbalanced training data, not model capacity.

Approach: per-class weights baked directly into the season loss function
(not passed via Keras's sample_weight/class_weight arguments - dict-
based sample_weight for multi-output models is fragile in Keras 3 and
threw a KeyError in practice). Category and texture losses are left
exactly as in phase 1; only the season loss internally multiplies each
example's crossentropy by an inverse-frequency weight for its true
class, so rare classes (winter, then fall) count for more during
training without touching Keras's fit()-level weighting machinery at
all.

Starts from best_model_phase1.keras (not phase2 - phase2 is not a good
base to build on) and continues training the head layers only, same as
phase 1's setup, just with the reweighted season loss and a modest
number of additional epochs.
"""

import csv
import os

import pandas as pd
import tensorflow as tf
from tensorflow.keras.callbacks import (
    CSVLogger, EarlyStopping, ModelCheckpoint, ReduceLROnPlateau,
)
from tensorflow.keras.models import load_model

from config import (
    CHECKPOINT_PATH_PHASE1, LABEL_SMOOTHING, MANIFEST_TRAIN_PATH,
    OUTPUT_ROOT, REDUCE_LR_FACTOR, REDUCE_LR_MIN_LR,
)
from step7_build_tf_datasets import build_datasets
from step8_build_model import _make_smoothed_sparse_loss

# --- Phase 1c specific config (kept here, not in config.py, since this
# is an optional extra pass rather than part of the core pipeline) ---
CHECKPOINT_PATH_SEASON_WEIGHTED = os.path.join(OUTPUT_ROOT, "best_model_season_weighted.keras")
HISTORY_LOG_PATH_SW = os.path.join(OUTPUT_ROOT, "training_history_season_weighted.csv")
HISTORY_PLOT_PATH_SW = os.path.join(OUTPUT_ROOT, "training_history_season_weighted.png")

CONTINUE_LEARNING_RATE = 1e-4  # a bit above phase 1's final 6.25e-5, below its start
MAX_EPOCHS = 15
EARLY_STOP_PATIENCE = 5


def compute_season_weights(train_df, season_to_idx):
    """
    Inverse-frequency weighting, normalized so the average weight is 1.0
    (keeps the overall loss scale comparable to phase 1 - only the
    relative balance between season classes shifts, not the total
    magnitude of the season loss term).
    """
    counts = train_df["season"].value_counts()
    n_classes = len(season_to_idx)
    total = len(train_df)

    raw_weights = {}
    for season, idx in season_to_idx.items():
        count = counts.get(season, 1)  # avoid div-by-zero for an unseen class
        raw_weights[idx] = total / (n_classes * count)

    mean_w = sum(raw_weights.values()) / len(raw_weights)
    normalized = {idx: w / mean_w for idx, w in raw_weights.items()}

    print("Season class weights (inverse-frequency, normalized to mean 1.0):")
    for season, idx in sorted(season_to_idx.items(), key=lambda kv: kv[1]):
        print(f"  {season:12s} (idx {idx}): count={counts.get(season, 0):4d}  weight={normalized[idx]:.3f}")

    return normalized


def _make_weighted_season_loss(num_classes, class_weights, label_smoothing=LABEL_SMOOTHING):
    """
    Same idea as step8's _make_smoothed_sparse_loss, but each example's
    crossentropy is additionally multiplied by an inverse-frequency
    weight looked up from its true class - computed once here as a
    constant tensor, gathered per-example at loss time. reduction="none"
    on the base loss is required to get per-example values to multiply
    before taking the mean ourselves.
    """
    cce = tf.keras.losses.CategoricalCrossentropy(
        label_smoothing=label_smoothing, reduction="none",
    )
    weights_tensor = tf.constant(
        [class_weights[i] for i in range(num_classes)], dtype=tf.float32,
    )

    def loss_fn(y_true, y_pred):
        y_true_int = tf.cast(y_true, tf.int32)
        y_true_onehot = tf.one_hot(y_true_int, depth=num_classes)
        per_example_loss = cce(y_true_onehot, y_pred)
        per_example_weight = tf.gather(weights_tensor, y_true_int)
        return tf.reduce_mean(per_example_loss * per_example_weight)

    return loss_fn


def _plot_history(csv_path, out_path):
    import matplotlib.pyplot as plt

    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    epochs = [int(r["epoch"]) for r in rows]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for head in ["category", "texture", "season"]:
        train_key = f"{head}_accuracy"
        val_key = f"val_{head}_accuracy"
        if train_key in rows[0]:
            axes[0].plot(epochs, [float(r[train_key]) for r in rows], label=f"{head} (train)")
        if val_key in rows[0]:
            axes[1].plot(epochs, [float(r[val_key]) for r in rows], label=f"{head} (val)")

    axes[0].set_title("Season-weighted - per-head training accuracy")
    axes[1].set_title("Season-weighted - per-head validation accuracy")
    for ax in axes:
        ax.set_xlabel("epoch")
        ax.set_ylabel("accuracy")
        ax.legend()
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=100)
    plt.show()
    print(f"Season-weighted training history plot saved -> {out_path}")


def train_season_weighted():
    # Standard (img, labels) datasets - identical to phase 1/phase 2, no
    # sample_weight plumbing. All the reweighting lives inside the season
    # loss function instead.
    train_ds, val_ds, test_ds, label_maps = build_datasets()
    category_to_idx, texture_to_idx, season_to_idx = label_maps

    train_df = pd.read_csv(MANIFEST_TRAIN_PATH)
    season_weights = compute_season_weights(train_df, season_to_idx)

    print(f"Loading phase 1 checkpoint from {CHECKPOINT_PATH_PHASE1} ...")
    model = load_model(
        CHECKPOINT_PATH_PHASE1,
        custom_objects={
            "loss_fn": _make_smoothed_sparse_loss(len(category_to_idx), LABEL_SMOOTHING),
        },
        compile=False,
    )

    # Keep the backbone frozen - phase 2 already showed unfreezing hurts
    # more than it helps on a dataset this size.
    base_model = model.layers[1]
    base_model.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=CONTINUE_LEARNING_RATE),
        loss={
            "category": _make_smoothed_sparse_loss(len(category_to_idx)),
            "texture": _make_smoothed_sparse_loss(len(texture_to_idx)),
            "season": _make_weighted_season_loss(len(season_to_idx), season_weights),
        },
        loss_weights={"category": 1.0, "texture": 1.0, "season": 1.0},
        metrics={"category": "accuracy", "texture": "accuracy", "season": "accuracy"},
    )
    model.summary()

    early_stop = EarlyStopping(monitor="val_loss", patience=EARLY_STOP_PATIENCE, restore_best_weights=True)
    checkpoint = ModelCheckpoint(filepath=CHECKPOINT_PATH_SEASON_WEIGHTED, monitor="val_loss", save_best_only=True)
    reduce_lr = ReduceLROnPlateau(
        monitor="val_loss", factor=REDUCE_LR_FACTOR, patience=2, min_lr=REDUCE_LR_MIN_LR, verbose=1,
    )
    csv_logger = CSVLogger(HISTORY_LOG_PATH_SW)

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=MAX_EPOCHS,
        callbacks=[early_stop, checkpoint, reduce_lr, csv_logger],
    )

    _plot_history(HISTORY_LOG_PATH_SW, HISTORY_PLOT_PATH_SW)

    print(f"\nSeason-weighted best model saved -> {CHECKPOINT_PATH_SEASON_WEIGHTED}")
    print("Compare its val_season_accuracy against phase 1's 70.9% before deciding which to keep.")
    print("Note: val_loss here is computed with the same weighted season loss as training, "
          "so early stopping/checkpointing is a bit skewed - val_season_ACCURACY (a plain "
          "correct/incorrect metric, unaffected by loss weighting) is the fair number to compare.")

    return model, history


if __name__ == "__main__":
    train_season_weighted()

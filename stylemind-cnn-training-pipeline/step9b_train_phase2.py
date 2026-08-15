"""
Step 9b - Phase 2: fine-tune the MobileNetV2 backbone.

Phase 1 (step9_train_phase1.py) trained with the backbone fully frozen -
only the head layers (412K of 2.67M params) were trainable. That's the
safe starting point for transfer learning, but it caps accuracy: the
backbone's ImageNet features never adapt to garment photos specifically.

This phase loads the phase 1 checkpoint, unfreezes the top N layers of
MobileNetV2, and continues training at a much lower learning rate. Low
LR matters here - fine-tuning a pretrained backbone with a normal LR
(1e-3, phase 1's rate) would wreck the pretrained weights with large
gradient updates before they've had a chance to adapt gently.

Saves to a SEPARATE checkpoint (best_model_phase2.keras) rather than
overwriting phase 1's file, so phase 1 remains a fallback if phase 2
doesn't actually improve things (fine-tuning can overfit on a dataset
this size if left too long, hence early stopping is kept tight here).
"""

import csv

from tensorflow.keras.callbacks import (
    CSVLogger, EarlyStopping, ModelCheckpoint, ReduceLROnPlateau,
)
from tensorflow.keras.models import load_model
import tensorflow as tf

from config import (
    CHECKPOINT_PATH_PHASE1, LABEL_SMOOTHING, REDUCE_LR_FACTOR,
    REDUCE_LR_MIN_LR, OUTPUT_ROOT,
)
import os
from step7_build_tf_datasets import build_datasets
from step8_build_model import _make_smoothed_sparse_loss

# --- Phase 2 specific config (kept here, not in config.py, since this
# is an optional extra phase rather than part of the core pipeline) ---
CHECKPOINT_PATH_PHASE2 = os.path.join(OUTPUT_ROOT, "best_model_phase2.keras")
HISTORY_LOG_PATH_PHASE2 = os.path.join(OUTPUT_ROOT, "training_history_phase2.csv")
HISTORY_PLOT_PATH_PHASE2 = os.path.join(OUTPUT_ROOT, "training_history_phase2.png")

PHASE2_LEARNING_RATE = 1e-5  # ~100x smaller than phase 1's 1e-3
PHASE2_MAX_EPOCHS = 15
PHASE2_EARLY_STOP_PATIENCE = 4  # tighter than phase 1's 5 - fine-tuning overfits faster
UNFREEZE_LAST_N_LAYERS = 40  # roughly the last few inverted-residual blocks


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

    axes[0].set_title("Phase 2 - per-head training accuracy")
    axes[1].set_title("Phase 2 - per-head validation accuracy")
    for ax in axes:
        ax.set_xlabel("epoch")
        ax.set_ylabel("accuracy")
        ax.legend()
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=100)
    plt.show()
    print(f"Phase 2 training history plot saved -> {out_path}")


def train_phase2():
    train_ds, val_ds, test_ds, label_maps = build_datasets()
    category_to_idx, texture_to_idx, season_to_idx = label_maps

    print(f"Loading phase 1 checkpoint from {CHECKPOINT_PATH_PHASE1} ...")
    # custom_objects needed because the sparse+label-smoothing loss wrapper
    # isn't a plain Keras built-in - Keras needs to know how to deserialize it.
    model = load_model(
        CHECKPOINT_PATH_PHASE1,
        custom_objects={
            "loss_fn": _make_smoothed_sparse_loss(len(category_to_idx), LABEL_SMOOTHING),
        },
        compile=False,
    )

    # The base MobileNetV2 is the first non-input layer in this model
    # (see step8_build_model.py: inputs -> base_model(inputs) -> ...).
    base_model = model.layers[1]
    base_model.trainable = True
    for layer in base_model.layers[:-UNFREEZE_LAST_N_LAYERS]:
        layer.trainable = False

    trainable_count = sum(1 for l in base_model.layers if l.trainable)
    print(f"Unfroze last {UNFREEZE_LAST_N_LAYERS} layers "
          f"({trainable_count}/{len(base_model.layers)} backbone layers now trainable).")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=PHASE2_LEARNING_RATE),
        loss={
            "category": _make_smoothed_sparse_loss(len(category_to_idx)),
            "texture": _make_smoothed_sparse_loss(len(texture_to_idx)),
            "season": _make_smoothed_sparse_loss(len(season_to_idx)),
        },
        loss_weights={"category": 1.0, "texture": 1.0, "season": 1.0},
        metrics={"category": "accuracy", "texture": "accuracy", "season": "accuracy"},
    )
    model.summary()

    early_stop = EarlyStopping(
        monitor="val_loss", patience=PHASE2_EARLY_STOP_PATIENCE, restore_best_weights=True,
    )
    checkpoint = ModelCheckpoint(
        filepath=CHECKPOINT_PATH_PHASE2, monitor="val_loss", save_best_only=True,
    )
    reduce_lr = ReduceLROnPlateau(
        monitor="val_loss",
        factor=REDUCE_LR_FACTOR,
        patience=2,
        min_lr=REDUCE_LR_MIN_LR,
        verbose=1,
    )
    csv_logger = CSVLogger(HISTORY_LOG_PATH_PHASE2)

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=PHASE2_MAX_EPOCHS,
        callbacks=[early_stop, checkpoint, reduce_lr, csv_logger],
    )

    _plot_history(HISTORY_LOG_PATH_PHASE2, HISTORY_PLOT_PATH_PHASE2)

    print(f"\nPhase 2 best model saved -> {CHECKPOINT_PATH_PHASE2}")
    print("Phase 1 checkpoint left untouched as a fallback if phase 2 didn't improve things.")

    return model, history, (train_ds, val_ds, test_ds), label_maps


if __name__ == "__main__":
    train_phase2()

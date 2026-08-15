"""
Step 9 - Train phase 1: frozen MobileNetV2 backbone, all three heads
trained jointly, FROM SCRATCH (no checkpoint reuse - the point of this
retrain is to see the effect of the dataset/labeling changes cleanly).

Callbacks:
  - EarlyStopping on val_loss (patience 5), best-weights restoration
  - ModelCheckpoint, saves only the best-so-far model
  - ReduceLROnPlateau (v2): halves the learning rate when val_loss
    plateaus for REDUCE_LR_PATIENCE epochs, down to a floor of
    REDUCE_LR_MIN_LR. Lets the optimizer take smaller steps as training
    converges instead of stalling at a coarser optimum and triggering
    early stopping prematurely.
  - CSVLogger + a post-training plot (v2): EarlyStopping/ModelCheckpoint
    both watch the *combined* val_loss across all three heads. If one
    head converges fast while another (e.g. season) is still improving,
    combined loss can look plateaued and stop training early without
    that being obvious. This doesn't change what's monitored for
    stopping - it just makes per-head val accuracy visible after the
    fact, in training_history.csv/.png, so you can see this if it
    happens and it's easy to show on a defense slide either way.
"""

import csv

from tensorflow.keras.callbacks import (
    CSVLogger, EarlyStopping, ModelCheckpoint, ReduceLROnPlateau,
)

from config import (
    CHECKPOINT_PATH_PHASE1, EARLY_STOP_PATIENCE, HISTORY_LOG_PATH,
    HISTORY_PLOT_PATH, PHASE1_MAX_EPOCHS, REDUCE_LR_FACTOR,
    REDUCE_LR_MIN_LR, REDUCE_LR_PATIENCE,
)
from step7_build_tf_datasets import build_datasets
from step8_build_model import build_model, compile_model


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

    axes[0].set_title("Per-head training accuracy")
    axes[1].set_title("Per-head validation accuracy")
    for ax in axes:
        ax.set_xlabel("epoch")
        ax.set_ylabel("accuracy")
        ax.legend()
        ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=100)
    plt.show()
    print(f"Training history plot saved -> {out_path}")


def train_phase1():
    train_ds, val_ds, test_ds, label_maps = build_datasets()
    category_to_idx, texture_to_idx, season_to_idx = label_maps

    model, base_model = build_model(
        num_category=len(category_to_idx),
        num_texture=len(texture_to_idx),
        num_season=len(season_to_idx),
    )
    compile_model(
        model,
        num_category=len(category_to_idx),
        num_texture=len(texture_to_idx),
        num_season=len(season_to_idx),
    )
    model.summary()

    early_stop = EarlyStopping(monitor="val_loss", patience=EARLY_STOP_PATIENCE, restore_best_weights=True)
    checkpoint = ModelCheckpoint(filepath=CHECKPOINT_PATH_PHASE1, monitor="val_loss", save_best_only=True)
    reduce_lr = ReduceLROnPlateau(
        monitor="val_loss",
        factor=REDUCE_LR_FACTOR,
        patience=REDUCE_LR_PATIENCE,
        min_lr=REDUCE_LR_MIN_LR,
        verbose=1,
    )
    csv_logger = CSVLogger(HISTORY_LOG_PATH)

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=PHASE1_MAX_EPOCHS,  # early stopping will likely cut this short
        callbacks=[early_stop, checkpoint, reduce_lr, csv_logger],
    )

    _plot_history(HISTORY_LOG_PATH, HISTORY_PLOT_PATH)

    return model, base_model, history, (train_ds, val_ds, test_ds), label_maps


if __name__ == "__main__":
    train_phase1()

"""
Step 9 — Train phase 1: frozen MobileNetV2 backbone, all three heads
trained jointly.

Early stopping on val_loss (patience 5) with best-weights restoration,
plus a ModelCheckpoint that only saves the best-so-far model — both are
Colab-disconnect resilience measures as well as standard anti-overfitting
practice.

This phase 1 checkpoint (best_model_phase1.keras) is the model that was
ultimately locked in as final — see experiments/ for why fine-tuning
(phase 2) and class-weighted retraining were tried and NOT adopted.
"""

from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

from config import CHECKPOINT_PATH_PHASE1, EARLY_STOP_PATIENCE, PHASE1_MAX_EPOCHS
from step7_build_tf_datasets import build_datasets
from step8_build_model import build_model, compile_model


def train_phase1():
    train_ds, val_ds, test_ds, label_maps = build_datasets()
    category_to_idx, texture_to_idx, season_to_idx = label_maps

    model, base_model = build_model(
        num_category=len(category_to_idx),
        num_texture=len(texture_to_idx),
        num_season=len(season_to_idx),
    )
    compile_model(model)
    model.summary()

    early_stop = EarlyStopping(monitor="val_loss", patience=EARLY_STOP_PATIENCE, restore_best_weights=True)
    checkpoint = ModelCheckpoint(filepath=CHECKPOINT_PATH_PHASE1, monitor="val_loss", save_best_only=True)

    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=PHASE1_MAX_EPOCHS,  # early stopping will likely cut this short
        callbacks=[early_stop, checkpoint],
    )

    return model, base_model, history, (train_ds, val_ds, test_ds), label_maps


if __name__ == "__main__":
    train_phase1()

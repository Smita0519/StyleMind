"""
EXPERIMENT — NOT part of the final pipeline. Kept for transparency.

Attempt: unfreeze the top of the MobileNetV2 backbone and fine-tune at a
low learning rate, to see if it could beat phase 1 (frozen backbone).

Result: it did not. EarlyStopping triggered after epoch 6/15, restoring
epoch 1's weights. Comparing phase 2's best epoch to phase 1's best:

  Head               Phase 1   Phase 2 (best epoch)
  Category val acc    0.869     0.885
  Texture val acc     0.776     0.774
  Season val acc      0.716     0.716
  Combined val_loss   1.682     1.727

Essentially a wash on accuracy but worse on combined val_loss, and every
epoch after that got progressively worse — a sign of fast overfitting
once the top layers were unfrozen, not genuine improvement. Likely
causes: FINE_TUNE_AT=100 unfroze too many params relative to the small
dataset (~2,800 training images), and/or the dataset was already close
to its practical ceiling under phase 1.

Decision: best_model_phase1.keras (frozen backbone) was kept as final;
this fine-tuning path was not pursued further.
"""

import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

from config import CHECKPOINT_PATH_PHASE1, EARLY_STOP_PATIENCE, PROJECT_DIR

CHECKPOINT_PATH_PHASE2 = f"{PROJECT_DIR}/best_model_phase2.keras"
FINE_TUNE_AT = 100  # MobileNetV2 has ~155 layers total
FINE_TUNE_LR = 1e-5
FINE_TUNE_EPOCHS = 15


def attempt_finetune(model, base_model, train_ds, val_ds):
    # Load best phase-1 weights first, in case this is a fresh runtime
    model.load_weights(CHECKPOINT_PATH_PHASE1)

    # Unfreeze the base model, but keep early generic feature extractors
    # (edges, textures, colors) frozen — only let high-level layers adapt
    base_model.trainable = True
    for layer in base_model.layers[:FINE_TUNE_AT]:
        layer.trainable = False

    # Much lower learning rate — critical, otherwise fine-tuning destroys
    # the pretrained weights instead of gently adapting them
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=FINE_TUNE_LR),
        loss={
            "category": "sparse_categorical_crossentropy",
            "texture": "sparse_categorical_crossentropy",
            "season": "sparse_categorical_crossentropy",
        },
        loss_weights={"category": 1.0, "texture": 1.0, "season": 1.0},
        metrics={"category": "accuracy", "texture": "accuracy", "season": "accuracy"},
    )
    model.summary()

    early_stop_ft = EarlyStopping(monitor="val_loss", patience=EARLY_STOP_PATIENCE, restore_best_weights=True)
    checkpoint_ft = ModelCheckpoint(filepath=CHECKPOINT_PATH_PHASE2, monitor="val_loss", save_best_only=True)

    history_finetune = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=FINE_TUNE_EPOCHS,
        callbacks=[early_stop_ft, checkpoint_ft],
    )
    return history_finetune

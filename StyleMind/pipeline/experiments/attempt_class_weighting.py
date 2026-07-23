"""
EXPERIMENT — NOT part of the final pipeline. Kept for transparency.

Attempt: correct texture/season class imbalance (e.g. 'solid' was 62% of
the test set, swallowing 'pleated'/'embroidered') using inverse-frequency
class weighting via a custom weighted sparse categorical cross-entropy.

Two rounds were tried:

  1. FULL inverse-frequency weights (e.g. pleated x5.91, solid x0.23) —
     overcorrected. Texture val accuracy dropped hard (77.4% -> ~59%) and
     didn't recover across epochs; solid recall collapsed.

     Root cause found along the way: reloading best_model_phase1.keras
     via load_weights() does NOT reset base_model.trainable — it was
     still True from the phase-2 fine-tuning attempt, so this run was
     quietly fine-tuning the backbone again at 10x the safe learning
     rate. Fixed by explicitly setting base_model.trainable = False
     before recompiling (see attempt_2_reweighted_soft below).

  2. SOFT weights (sqrt of the full weights, pulling in the extremes —
     5.91 -> ~2.4, 0.23 -> ~0.48) with the backbone correctly re-frozen.
     This produced the best macro-F1 texture result of any version
     (0.599 vs phase 1's 0.585), with pleated F1 more than doubling and
     solid recall mostly recovering.

Final decision: despite soft-weighting technically winning on macro-F1,
best_model_phase1.keras (unweighted) was still chosen as the FINAL model.
Reasoning: phase 1's solid recall (93.3%) far exceeds soft-weighting's
(78.6%) — meaning phase 1 misses far fewer of the majority class, which
matters most since the deployment/test distribution is itself solid-heavy.
Optimizing for macro-F1 (equal weight per class) doesn't match the actual
expected traffic distribution, so raw accuracy on the realistic
distribution was judged the more defensible choice for this project.

This module is included to show the exploration, not as something to run
as part of the pipeline.
"""

import numpy as np
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight

from config import CHECKPOINT_PATH_PHASE1, EARLY_STOP_PATIENCE, PROJECT_DIR

CHECKPOINT_PATH_WEIGHTED = f"{PROJECT_DIR}/best_model_weighted.keras"
CHECKPOINT_PATH_TEXTURE_SOFT = f"{PROJECT_DIR}/best_model_texture_soft.keras"
WEIGHTED_LR = 1e-4
WEIGHTED_EPOCHS = 15


def get_class_weights(train_df, col, class_to_idx):
    labels = train_df[col].map(class_to_idx).values
    classes = np.unique(labels)
    weights = compute_class_weight(class_weight="balanced", classes=classes, y=labels)
    return dict(zip(classes, weights))


def weighted_sparse_ce(class_weights_dict, num_classes):
    weight_vector = tf.constant(
        [class_weights_dict.get(i, 1.0) for i in range(num_classes)], dtype=tf.float32
    )

    def loss_fn(y_true, y_pred):
        y_true = tf.cast(y_true, tf.int32)
        sample_weights = tf.gather(weight_vector, y_true)
        base_loss = tf.keras.losses.sparse_categorical_crossentropy(y_true, y_pred)
        return base_loss * sample_weights

    return loss_fn


def attempt_2_reweighted_soft(model, base_model, train_ds, val_ds, train_df, texture_to_idx, season_to_idx):
    """The corrected, best-performing (but ultimately not adopted) attempt."""
    texture_classes = sorted(texture_to_idx, key=texture_to_idx.get)
    season_classes = sorted(season_to_idx, key=season_to_idx.get)

    texture_class_weights = get_class_weights(train_df, "texture", texture_to_idx)
    season_class_weights = get_class_weights(train_df, "season", season_to_idx)
    texture_class_weights_soft = {k: v ** 0.5 for k, v in texture_class_weights.items()}

    print("Texture weights (soft):", {texture_classes[k]: round(v, 2) for k, v in texture_class_weights_soft.items()})
    print("Season weights:", {season_classes[k]: round(v, 2) for k, v in season_class_weights.items()})

    model.load_weights(CHECKPOINT_PATH_PHASE1)
    base_model.trainable = False  # critical — must be re-frozen explicitly

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=WEIGHTED_LR),
        loss={
            "category": "sparse_categorical_crossentropy",  # left unweighted, it was fine
            "texture": weighted_sparse_ce(texture_class_weights_soft, len(texture_classes)),
            "season": weighted_sparse_ce(season_class_weights, len(season_classes)),
        },
        metrics={"category": "accuracy", "texture": "accuracy", "season": "accuracy"},
    )

    history_soft = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=WEIGHTED_EPOCHS,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(patience=EARLY_STOP_PATIENCE, restore_best_weights=True, monitor="val_loss"),
            tf.keras.callbacks.ModelCheckpoint(CHECKPOINT_PATH_TEXTURE_SOFT, save_best_only=True, monitor="val_loss"),
        ],
    )
    return history_soft

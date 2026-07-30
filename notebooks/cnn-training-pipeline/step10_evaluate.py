"""
Step 10 — Final evaluation on the held-out test set.

The test set has been fully untouched since Step 6 — no training or
tuning decision has seen it — so this is the first genuinely unbiased
read on real-world performance. This is a single, one-time evaluation;
no hyperparameters should be adjusted based on these results, since that
would leak test-set information back into "training" indirectly.

Reports produced:
  - Aggregate per-head loss/accuracy (model.evaluate)
  - Per-class precision/recall/F1 (classification_report)
  - Confusion matrices (saved as PNGs) for category, texture, season

Final locked test-set results (phase 1 model):
  Category — 87.7% accuracy, macro F1 0.878
  Texture  — 78.1% accuracy, macro F1 0.585
  Season   — 75.1% accuracy, macro F1 0.687

Texture and season have a lower ceiling than category because their
labels came from CLIP zero-shot labeling (Step 5), which is noisier than
the human-derived category labels — not a flaw in this evaluation or the
model architecture. Season's 'all-season' class in particular reflects
genuine semantic overlap with 'fall'/'summer', confirmed by the confusion
matrix, not a labeling bug.
"""

import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

from config import (
    CHECKPOINT_PATH_PHASE1, CONFUSION_CATEGORY_PATH, CONFUSION_SEASON_PATH,
    CONFUSION_TEXTURE_PATH,
)


def evaluate_model(model, test_ds, test_df, category_to_idx, texture_to_idx, season_to_idx):
    # Explicitly reload the checkpoint to be certain we're evaluating the
    # right weights, not whatever happens to be in memory
    model.load_weights(CHECKPOINT_PATH_PHASE1)

    test_results = model.evaluate(test_ds, return_dict=True)
    print("=== Test Set Results ===")
    for key, value in test_results.items():
        print(f"{key}: {value:.4f}")

    category_classes = sorted(category_to_idx, key=category_to_idx.get)
    texture_classes = sorted(texture_to_idx, key=texture_to_idx.get)
    season_classes = sorted(season_to_idx, key=season_to_idx.get)

    y_pred = model.predict(test_ds)
    category_pred_idx = np.argmax(y_pred[0], axis=1)
    texture_pred_idx = np.argmax(y_pred[1], axis=1)
    season_pred_idx = np.argmax(y_pred[2], axis=1)

    category_true_idx = test_df["category"].map(category_to_idx).values
    texture_true_idx = test_df["texture"].map(texture_to_idx).values
    season_true_idx = test_df["season"].map(season_to_idx).values

    print("\n" + "=" * 60)
    print("CATEGORY — per-class report")
    print("=" * 60)
    print(classification_report(category_true_idx, category_pred_idx, target_names=category_classes, digits=3))

    print("=" * 60)
    print("TEXTURE — per-class report")
    print("=" * 60)
    print(classification_report(texture_true_idx, texture_pred_idx, target_names=texture_classes, digits=3))

    print("=" * 60)
    print("SEASON — per-class report")
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

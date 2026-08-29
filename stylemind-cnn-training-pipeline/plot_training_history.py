"""
Rebuilds the training-vs-validation accuracy plot straight from
training_history.csv (saved automatically by step9_train_phase1.py
during training) - no retraining, just re-plotting from the logged
per-epoch numbers. Useful for getting a fresh copy, or a differently
styled version, without re-running the Colab training.

Produces two figures:
  - training_accuracy_by_head.png  : one line per head, train (solid)
    vs val (dashed), all three heads on one plot
  - training_loss.png              : overall train vs val loss

Reads config.py's OUTPUT_ROOT and HISTORY_LOG_PATH, so it picks up
whichever run's CSV is sitting there - no hardcoded path.
"""

import csv
import os

import matplotlib.pyplot as plt

from config import HISTORY_LOG_PATH, OUTPUT_ROOT

ACCURACY_PLOT_PATH = os.path.join(OUTPUT_ROOT, "training_accuracy_by_head.png")
LOSS_PLOT_PATH = os.path.join(OUTPUT_ROOT, "training_loss.png")

HEAD_DISPLAY_NAMES = {
    "category": "Category",
    "texture": "Pattern",  # display name only - CSV column is still "texture"
    "season": "Season",
}


def load_history(csv_path):
    with open(csv_path) as f:
        rows = list(csv.DictReader(f))
    epochs = [int(r["epoch"]) + 1 for r in rows]  # epoch column is 0-indexed in the CSV
    return epochs, rows


def plot_accuracy(epochs, rows, save_path):
    plt.figure(figsize=(9, 6))
    colors = {"category": "#1f77b4", "texture": "#ff7f0e", "season": "#2ca02c"}

    for head, display_name in HEAD_DISPLAY_NAMES.items():
        train_key = f"{head}_accuracy"
        val_key = f"val_{head}_accuracy"
        if train_key in rows[0]:
            plt.plot(epochs, [float(r[train_key]) for r in rows],
                      label=f"{display_name} (train)", color=colors[head], linestyle="-")
        if val_key in rows[0]:
            plt.plot(epochs, [float(r[val_key]) for r in rows],
                      label=f"{display_name} (val)", color=colors[head], linestyle="--")

    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title("Training vs Validation Accuracy per Head")
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.show()
    print(f"Saved -> {save_path}")


def plot_loss(epochs, rows, save_path):
    plt.figure(figsize=(9, 6))
    if "loss" in rows[0]:
        plt.plot(epochs, [float(r["loss"]) for r in rows], label="Train loss", color="#d62728")
    if "val_loss" in rows[0]:
        plt.plot(epochs, [float(r["val_loss"]) for r in rows], label="Val loss",
                  color="#d62728", linestyle="--")

    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Training vs Validation Loss (combined, all heads)")
    plt.legend(loc="upper right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.show()
    print(f"Saved -> {save_path}")


if __name__ == "__main__":
    epochs, rows = load_history(HISTORY_LOG_PATH)
    plot_accuracy(epochs, rows, ACCURACY_PLOT_PATH)
    plot_loss(epochs, rows, LOSS_PLOT_PATH)

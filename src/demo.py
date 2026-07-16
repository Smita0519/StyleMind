"""
StyleMind — interactive demo.

Pops up a native file picker so the user can select a clothing image,
runs it through the trained model, and displays the image side-by-side
with the category / texture / season predictions. After each prediction,
a popup asks whether to test another image or exit.

This script touches nothing else in the project — it only reads the
model files in models/ and images the user selects. Nothing is written
back to the project (only optionally to outputs/, see SAVE_RESULTS).

Run from the project root:
    python src/demo.py
"""

import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import matplotlib.pyplot as plt
from PIL import Image

# Allow running this file directly (python src/demo.py) as well as
# as a module (python -m src.demo)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from predict import predict, load_model  # noqa: E402

# Set to True to save each annotated result image into outputs/
SAVE_RESULTS = False
OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"

IMAGE_FILETYPES = [
    ("Image files", "*.jpg *.jpeg *.png *.webp *.bmp"),
    ("All files", "*.*"),
]


def pick_image(root):
    """Opens a native 'choose file' popup and returns the selected path (or '')."""
    return filedialog.askopenfilename(
        title="Select a clothing image to test",
        filetypes=IMAGE_FILETYPES,
    )


def show_result(image_path, result):
    """Displays the input image next to its predicted labels."""
    img = Image.open(image_path).convert("RGB")

    fig, (ax_img, ax_info) = plt.subplots(
        1, 2, figsize=(9, 5), gridspec_kw={"width_ratios": [1, 1]}
    )
    ax_img.imshow(img)
    ax_img.axis("off")
    ax_img.set_title("Input", fontsize=12)

    ax_info.axis("off")
    lines = [
        f"Category:  {result['category']}  ({result['category_confidence']:.0%})",
        f"Texture:   {result['texture']}  ({result['texture_confidence']:.0%})",
        f"Season:    {result['season']}  ({result['season_confidence']:.0%})",
    ]
    ax_info.text(
        0.0, 0.6, "\n\n".join(lines),
        fontsize=13, verticalalignment="center", family="monospace",
    )
    fig.suptitle(Path(image_path).name, fontsize=10, color="gray")
    plt.tight_layout()

    if SAVE_RESULTS:
        OUTPUTS_DIR.mkdir(exist_ok=True)
        out_path = OUTPUTS_DIR / f"result_{Path(image_path).stem}.png"
        plt.savefig(out_path, dpi=120, bbox_inches="tight")
        print(f"Saved: {out_path}")

    # Blocks until the user closes the plot window, then the loop continues
    plt.show()


def main():
    root = tk.Tk()
    root.withdraw()  # hide the empty main tkinter window, only popups show

    print("Loading model (first run only)...")
    load_model()

    while True:
        image_path = pick_image(root)

        if not image_path:
            # User hit "Cancel" on the file picker
            if messagebox.askyesno("StyleMind", "No image selected. Exit demo?"):
                break
            else:
                continue

        try:
            result = predict(image_path)
        except Exception as e:
            messagebox.showerror("StyleMind — Error", f"Could not process image:\n{e}")
            continue

        print(f"\n--- {Path(image_path).name} ---")
        print(
            f"Category: {result['category']} ({result['category_confidence']:.0%}) | "
            f"Texture: {result['texture']} ({result['texture_confidence']:.0%}) | "
            f"Season: {result['season']} ({result['season_confidence']:.0%})"
        )

        show_result(image_path, result)

        if not messagebox.askyesno("StyleMind", "Test another image?"):
            break

    print("Demo ended.")
    root.destroy()


if __name__ == "__main__":
    main()

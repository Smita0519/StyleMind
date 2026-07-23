"""
StyleMind — interactive demo.
 
Pops up a native file picker so the user can select a clothing image,
runs it through the full pipeline (YOLO-seg background removal ->
classification -> dominant color extraction), and displays four panels:
the original photo, the YOLO segmentation overlay, the exact 224x224
image the model saw, and the predictions + color swatches. After each
prediction, a popup asks whether to test another image or exit.
 
Run from the project root:
    python src/demo.py
"""
 
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
 
import matplotlib.pyplot as plt
from PIL import Image
 
sys.path.insert(0, str(Path(__file__).resolve().parent))
from predict import predict, load_model  # noqa: E402
 
SAVE_RESULTS = False
OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"
 
IMAGE_FILETYPES = [
    ("Image files", "*.jpg *.jpeg *.png *.webp *.bmp"),
    ("All files", "*.*"),
]
 
 
def pick_image(root):
    return filedialog.askopenfilename(
        title="Select a clothing image to test",
        filetypes=IMAGE_FILETYPES,
    )
 
 
def show_result(image_path, result, seg):
    """Displays original / segmentation / model-input / predictions+colors."""
    original = Image.open(image_path).convert("RGB")
 
    fig, axes = plt.subplots(
        1, 4, figsize=(16, 4.5), gridspec_kw={"width_ratios": [1, 1, 1, 1.1]}
    )
    ax_orig, ax_mask, ax_input, ax_info = axes
 
    ax_orig.imshow(original)
    ax_orig.axis("off")
    ax_orig.set_title("Original", fontsize=11)
 
    ax_mask.imshow(seg["mask_overlay"])
    ax_mask.axis("off")
    mask_title = "YOLO segmentation" if seg["mask_found"] else "YOLO: no mask (fallback)"
    ax_mask.set_title(mask_title, fontsize=11)
 
    ax_input.imshow(seg["final"])
    ax_input.axis("off")
    ax_input.set_title("Model input (224x224)", fontsize=11)
 
    ax_info.axis("off")
    lines = [
        f"Category:  {result['category']}  ({result['category_confidence']:.0%})",
        f"Texture:   {result['texture']}  ({result['texture_confidence']:.0%})",
        f"Season:    {result['season']}  ({result['season_confidence']:.0%})",
    ]
    ax_info.text(
        0.0, 0.85, "\n\n".join(lines),
        fontsize=12, verticalalignment="top", family="monospace",
        transform=ax_info.transAxes,
    )
 
    ax_info.text(
        0.0, 0.35, "Dominant colors:", fontsize=12,
        family="monospace", transform=ax_info.transAxes,
    )
    for i, hex_color in enumerate(result["dominant_colors"]):
        ax_info.add_patch(
            plt.Rectangle(
                (0.0 + i * 0.22, 0.15), 0.18, 0.15,
                transform=ax_info.transAxes,
                facecolor=hex_color, edgecolor="black",
            )
        )
        ax_info.text(
            0.0 + i * 0.22, 0.10, hex_color, fontsize=8,
            family="monospace", transform=ax_info.transAxes,
        )
 
    fig.suptitle(Path(image_path).name, fontsize=10, color="gray")
    plt.tight_layout()
 
    if SAVE_RESULTS:
        OUTPUTS_DIR.mkdir(exist_ok=True)
        out_path = OUTPUTS_DIR / f"result_{Path(image_path).stem}.png"
        plt.savefig(out_path, dpi=120, bbox_inches="tight")
        print(f"Saved: {out_path}")
 
    plt.show()
 
 
def main():
    root = tk.Tk()
    root.withdraw()
 
    print("Loading model (first run only)...")
    load_model()
 
    while True:
        image_path = pick_image(root)
 
        if not image_path:
            if messagebox.askyesno("StyleMind", "No image selected. Exit demo?"):
                break
            else:
                continue
 
        try:
            result, seg = predict(image_path, return_segmentation=True)
        except Exception as e:
            messagebox.showerror("StyleMind — Error", f"Could not process image:\n{e}")
            continue
 
        print(f"\n--- {Path(image_path).name} ---")
        print(
            f"Category: {result['category']} ({result['category_confidence']:.0%}) | "
            f"Texture: {result['texture']} ({result['texture_confidence']:.0%}) | "
            f"Season: {result['season']} ({result['season_confidence']:.0%}) | "
            f"Colors: {', '.join(result['dominant_colors'])}"
        )
        if not seg["mask_found"]:
            print("  (note: no garment mask detected, used original image as fallback)")
 
        show_result(image_path, result, seg)
 
        if not messagebox.askyesno("StyleMind", "Test another image?"):
            break
 
    print("Demo ended.")
    root.destroy()
 
 
if __name__ == "__main__":
    main()
 
"""
Step 5a - Calibrate SEASON_CONFIDENCE_MARGIN for the current CLIP model.

RUN THIS BEFORE step5_clip_labeling.py.

The margin that decides when season falls back to "all-season" (top1/top2
CLIP score gap too small to trust) is specific to whichever CLIP model
produced the scores - different models have different embedding
geometries and therefore different typical gap sizes. The original 0.008
was tuned for ViT-B-32 (gap std ~0.02); this config now uses ViT-L-14, so
that value is not guaranteed to still be correct.

This script runs the season prompt ensemble over a sample of the
processed dataset, computes the actual top1/top2 gap distribution, and
suggests a margin that lands the fallback rate in a healthy ~20-40% range
- the same target range used originally, found the same way.

It does NOT write any labels. It only prints stats and a recommendation.
After running this, manually set SEASON_CONFIDENCE_MARGIN in config.py to
the suggested value (or your own judgment call) before running
step5_clip_labeling.py for real.

Requires: pip install open_clip_torch torch
"""

import csv
import random

import numpy as np
import torch
from PIL import Image

from config import (
    CLIP_MODEL_NAME, CLIP_PRETRAINED, PROCESSED_MANIFEST_PATH, SEASON_PROMPTS,
)

SAMPLE_SIZE = 400  # enough for a stable distribution estimate without scanning everything
CANDIDATE_MARGINS = [0.002, 0.004, 0.006, 0.008, 0.010, 0.012, 0.015, 0.020, 0.025, 0.030]


def load_clip():
    import open_clip

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        CLIP_MODEL_NAME, pretrained=CLIP_PRETRAINED
    )
    clip_model = clip_model.to(device).eval()
    clip_tokenizer = open_clip.get_tokenizer(CLIP_MODEL_NAME)
    print(f"CLIP loaded on {device} ({CLIP_MODEL_NAME} / {CLIP_PRETRAINED})")
    return clip_model, clip_preprocess, clip_tokenizer, device


def get_ensembled_text_embeddings(prompts_dict, clip_model, clip_tokenizer, device):
    """Average multiple prompt phrasings per class into one embedding per class."""
    class_names = list(prompts_dict.keys())
    class_embeddings = []
    for class_name in class_names:
        phrasings = prompts_dict[class_name]
        tokens = clip_tokenizer(phrasings).to(device)
        with torch.no_grad():
            emb = clip_model.encode_text(tokens)
            emb = emb / emb.norm(dim=-1, keepdim=True)
            class_emb = emb.mean(dim=0)
            class_emb = class_emb / class_emb.norm()
        class_embeddings.append(class_emb)
    return class_names, torch.stack(class_embeddings)


def calibrate():
    clip_model, clip_preprocess, clip_tokenizer, device = load_clip()
    season_labels, season_embeddings = get_ensembled_text_embeddings(
        SEASON_PROMPTS, clip_model, clip_tokenizer, device
    )

    with open(PROCESSED_MANIFEST_PATH) as f:
        rows = list(csv.DictReader(f))

    random.seed(42)
    sample_rows = random.sample(rows, min(SAMPLE_SIZE, len(rows)))

    gaps = []
    for i, row in enumerate(sample_rows):
        img = clip_preprocess(Image.open(row["filepath"]).convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            img_emb = clip_model.encode_image(img)
            img_emb = img_emb / img_emb.norm(dim=-1, keepdim=True)
        sims = (img_emb @ season_embeddings.T).squeeze(0)
        sims_sorted, _ = sims.sort(descending=True)
        gap = (sims_sorted[0] - sims_sorted[1]).item()
        gaps.append(gap)
        if (i + 1) % 100 == 0:
            print(f"  ...{i + 1}/{len(sample_rows)}")

    gaps = np.array(gaps)
    print(f"\nSampled {len(gaps)} images.")
    print(f"Gap distribution: mean={gaps.mean():.4f}, std={gaps.std():.4f}, "
          f"min={gaps.min():.4f}, max={gaps.max():.4f}")

    print("\nMargin -> resulting fallback rate:")
    best_margin = None
    for margin in CANDIDATE_MARGINS:
        fallback_rate = (gaps < margin).mean()
        flag = ""
        if 0.20 <= fallback_rate <= 0.40:
            flag = "  <-- in healthy 20-40% range"
            if best_margin is None:
                best_margin = margin
        print(f"  {margin:.3f} -> {fallback_rate:.1%}{flag}")

    if best_margin is not None:
        print(f"\nSuggested SEASON_CONFIDENCE_MARGIN: {best_margin}")
        print("Set this in config.py before running step5_clip_labeling.py.")
    else:
        print("\nNo candidate margin landed in the 20-40% range - inspect the")
        print("distribution above and pick a margin manually, or widen")
        print("CANDIDATE_MARGINS in this script and re-run.")


if __name__ == "__main__":
    calibrate()

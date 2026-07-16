"""
Step 5 — CLIP zero-shot labeling for texture and season.

Runs on the YOLO-seg processed (clean, cropped) images from Step 4, not
raw photos — background clutter would otherwise bias the predictions.

This is the FINAL, calibrated version of the labeling logic after two
rounds of iteration (see notes below and experiments/ for the discarded
intermediate attempts):

  1. Texture (7 classes) is always a plain CLIP top-1 match.
  2. Season starts as a rule for categories where it's unambiguous
     (Warmwear/Jacket -> winter, Shorts -> summer), skipping CLIP entirely.
  3. For everything else, season is CLIP top-1 UNLESS the confidence gap
     between the top-1 and top-2 scores is below SEASON_CONFIDENCE_MARGIN,
     in which case it falls back to 'all-season' (a fallback outcome only —
     not itself a CLIP prompt class, see config.py for why).

Calibration history:
  - Margin started at 0.03, which caused 89% of images to hit the
    fallback — the score spread's actual std was only ~0.02, so 0.03 was
    larger than a full standard deviation.
  - Lowered to 0.008, landing at a healthy 23% fallback rate.
  - A 'fall' prompt investigation showed CLIP was structurally biased
    toward a generic 'all-season' prompt; removing 'all-season' as an
    explicit prompt (keeping it only as a fallback label) fixed this.

Requires: pip install open_clip_torch torch
"""

import csv

import torch
from PIL import Image

from config import (
    CLIP_LABELED_MANIFEST_PATH, CLIP_MODEL_NAME, CLIP_PRETRAINED,
    PROCESSED_MANIFEST_PATH, SEASON_CONFIDENCE_MARGIN, SEASON_PROMPTS,
    SEASON_RULES, TEXTURE_PROMPTS,
)


def load_clip():
    import open_clip

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        CLIP_MODEL_NAME, pretrained=CLIP_PRETRAINED
    )
    clip_model = clip_model.to(device).eval()
    clip_tokenizer = open_clip.get_tokenizer(CLIP_MODEL_NAME)
    print(f"CLIP loaded on {device}")
    return clip_model, clip_preprocess, clip_tokenizer, device


def get_text_embeddings(prompts_dict, clip_model, clip_tokenizer, device):
    labels = list(prompts_dict.keys())
    texts = list(prompts_dict.values())
    tokens = clip_tokenizer(texts).to(device)
    with torch.no_grad():
        embeddings = clip_model.encode_text(tokens)
        embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
    return labels, embeddings


def make_label_image_fn(clip_model, clip_preprocess, clip_tokenizer, device):
    texture_labels, texture_embeddings = get_text_embeddings(
        TEXTURE_PROMPTS, clip_model, clip_tokenizer, device
    )
    season_labels, season_embeddings = get_text_embeddings(
        SEASON_PROMPTS, clip_model, clip_tokenizer, device
    )

    def label_image(img_path, category):
        img = clip_preprocess(Image.open(img_path).convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            img_embedding = clip_model.encode_image(img)
            img_embedding = img_embedding / img_embedding.norm(dim=-1, keepdim=True)

        # Texture: always CLIP-based
        tex_sims = (img_embedding @ texture_embeddings.T).squeeze(0)
        tex_sims_sorted, tex_idx_sorted = tex_sims.sort(descending=True)
        texture_label = texture_labels[tex_idx_sorted[0].item()]
        texture_confidence = tex_sims_sorted[0].item()

        # Season: rule override, else CLIP with confidence-gap fallback
        if category in SEASON_RULES:
            season_label = SEASON_RULES[category]
            season_confidence = 1.0
            season_gap = None
            season_source = "rule"
        else:
            season_sims = (img_embedding @ season_embeddings.T).squeeze(0)
            season_sims_sorted, season_idx_sorted = season_sims.sort(descending=True)
            top1_score = season_sims_sorted[0].item()
            top2_score = season_sims_sorted[1].item()
            gap = top1_score - top2_score

            if gap < SEASON_CONFIDENCE_MARGIN:
                season_label = "all-season"
                season_source = "low_confidence_fallback"
            else:
                season_label = season_labels[season_idx_sorted[0].item()]
                season_source = "clip"
            season_confidence = top1_score
            season_gap = round(gap, 4)

        return {
            "texture": texture_label,
            "texture_confidence": round(texture_confidence, 4),
            "season": season_label,
            "season_confidence": round(season_confidence, 4),
            "season_gap": season_gap,
            "season_source": season_source,
        }

    return label_image


def run_labeling():
    clip_model, clip_preprocess, clip_tokenizer, device = load_clip()
    label_image = make_label_image_fn(clip_model, clip_preprocess, clip_tokenizer, device)

    with open(PROCESSED_MANIFEST_PATH) as f:
        processed_rows = list(csv.DictReader(f))

    labeled_rows = []
    for i, row in enumerate(processed_rows):
        labels = label_image(row["filepath"], row["category"])
        labeled_rows.append({**row, **labels})
        if (i + 1) % 200 == 0:
            print(f"Labeled {i + 1}/{len(processed_rows)}...")

    with open(CLIP_LABELED_MANIFEST_PATH, "w", newline="") as f:
        fieldnames = [
            "filepath", "category", "texture", "texture_confidence",
            "season", "season_confidence", "season_gap", "season_source",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(labeled_rows)

    print(f"\nLabeling done: {len(labeled_rows)} images -> {CLIP_LABELED_MANIFEST_PATH}")
    return labeled_rows


if __name__ == "__main__":
    run_labeling()

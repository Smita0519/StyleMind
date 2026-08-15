"""
Step 5 - CLIP zero-shot labeling for texture and season.

Runs on the YOLO-seg processed (clean, cropped) images from Step 4, not
raw photos - background clutter would otherwise bias the predictions.

v2 CHANGES from the original Colab version:

  1. Rule-based season shortcuts (Jacket/Warmwear -> winter, Shorts ->
     summer) are REMOVED. Every image, regardless of category, now goes
     through CLIP for season - no category ever skips it.
  2. Texture and season prompts are now ENSEMBLES: several phrasings per
     class (see config.py) are embedded separately and averaged into one
     class embedding, rather than one embedding per single prompt
     string. This is a standard technique to reduce CLIP zero-shot noise
     and should improve label quality on both heads.
  3. CLIP_MODEL_NAME/CLIP_PRETRAINED point at a larger model (see
     config.py) - only feasible now that this runs on a dedicated local
     GPU instead of Colab's shared/limited runtime.

Season still falls back to 'all-season' when the CLIP top-1/top-2
confidence gap is below SEASON_CONFIDENCE_MARGIN (kept deliberately -
this is a CLIP-driven uncertainty signal, not a rule/shortcut). Run
step5a_calibrate_season_margin.py FIRST and set that margin in config.py
for the current CLIP model before running this script for real.

Requires: pip install open_clip_torch torch
"""

import csv

import torch
from PIL import Image

from config import (
    CLIP_LABELED_MANIFEST_PATH, CLIP_MODEL_NAME, CLIP_PRETRAINED,
    PROCESSED_MANIFEST_PATH, SEASON_CONFIDENCE_MARGIN, SEASON_PROMPTS,
    TEXTURE_PROMPTS,
)


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
    """
    prompts_dict maps class_name -> list of prompt phrasings. Each
    phrasing is embedded separately, L2-normalized, averaged, then
    re-normalized - giving one robust embedding per class instead of
    relying on a single prompt string's idiosyncrasies.
    """
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


def make_label_image_fn(clip_model, clip_preprocess, clip_tokenizer, device):
    texture_labels, texture_embeddings = get_ensembled_text_embeddings(
        TEXTURE_PROMPTS, clip_model, clip_tokenizer, device
    )
    season_labels, season_embeddings = get_ensembled_text_embeddings(
        SEASON_PROMPTS, clip_model, clip_tokenizer, device
    )

    def label_image(img_path, category):
        img = clip_preprocess(Image.open(img_path).convert("RGB")).unsqueeze(0).to(device)
        with torch.no_grad():
            img_embedding = clip_model.encode_image(img)
            img_embedding = img_embedding / img_embedding.norm(dim=-1, keepdim=True)

        # Texture: CLIP top-1 against the ensembled class embeddings
        tex_sims = (img_embedding @ texture_embeddings.T).squeeze(0)
        tex_sims_sorted, tex_idx_sorted = tex_sims.sort(descending=True)
        texture_label = texture_labels[tex_idx_sorted[0].item()]
        texture_confidence = tex_sims_sorted[0].item()

        # Season: CLIP top-1 for every category (no rule shortcuts),
        # with confidence-gap fallback to 'all-season'
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

    fallback_count = sum(1 for r in labeled_rows if r["season_source"] == "low_confidence_fallback")
    fallback_rate = fallback_count / len(labeled_rows) if labeled_rows else 0
    print(f"\nLabeling done: {len(labeled_rows)} images -> {CLIP_LABELED_MANIFEST_PATH}")
    print(f"Season fallback rate: {fallback_rate:.1%} ({fallback_count}/{len(labeled_rows)})")
    if not (0.20 <= fallback_rate <= 0.40):
        print("NOTE: fallback rate is outside the healthy 20-40% range - consider "
              "re-running step5a_calibrate_season_margin.py and adjusting the margin.")

    return labeled_rows


if __name__ == "__main__":
    run_labeling()

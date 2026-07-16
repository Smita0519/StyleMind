"""
Step 3 — Download the YOLO-seg checkpoint and verify its class list.

Generic COCO-pretrained YOLO doesn't work here (no garment classes, only
"person"), so this uses a checkpoint trained specifically on DeepFashion2,
which gives pixel-level masks (not just boxes) for clean background
removal in Step 4.

Requires: pip install ultralytics huggingface_hub
"""

import csv
import shutil

from config import MANIFEST_PATH, YOLO_CHECKPOINT, YOLO_HF_FILENAME, YOLO_HF_REPO_ID


def download_checkpoint():
    from huggingface_hub import hf_hub_download

    downloaded_path = hf_hub_download(repo_id=YOLO_HF_REPO_ID, filename=YOLO_HF_FILENAME)
    shutil.copy(downloaded_path, YOLO_CHECKPOINT)
    print(f"Checkpoint saved to: {YOLO_CHECKPOINT}")


def verify_class_list():
    """
    Loads the checkpoint and runs it on one sample image from the manifest,
    printing the class list — a manual checkpoint to confirm the model's
    classes map sensibly before running the full dataset through it.
    """
    from ultralytics import YOLO

    with open(MANIFEST_PATH) as f:
        manifest_rows = list(csv.DictReader(f))

    model = YOLO(YOLO_CHECKPOINT)
    results = model(manifest_rows[0]["filepath"])
    print("YOLO-seg class list:", results[0].names)
    return model


if __name__ == "__main__":
    download_checkpoint()
    verify_class_list()

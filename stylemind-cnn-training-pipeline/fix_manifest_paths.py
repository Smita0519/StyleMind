"""
One-time fix: the manifest CSVs (manifest_train.csv, manifest_val.csv,
manifest_test.csv) were generated on Colab, where the project root was
/content/stylemind-colab-prep. Their "filepath" column has that Colab
path baked in, which doesn't exist on this machine.

This rewrites each path to point at this machine's local
data/processed_dataset/ folder instead, by keeping everything from
"data/processed_dataset" onward (works whether the original path used
forward or back slashes) and rejoining it under this script's own
PROJECT_ROOT.

Run this from inside stylemind-cnn-training-pipeline/ (same folder as
config.py) - it uses config.py's own path constants, so it always
points at wherever this copy of the repo actually lives, not a
hardcoded guess.

Originals are backed up as *.colab_paths.csv before overwriting, in
case anything needs to be re-checked.
"""

import os
import shutil

import pandas as pd

from config import (
    MANIFEST_TEST_PATH, MANIFEST_TRAIN_PATH, MANIFEST_VAL_PATH, PROJECT_ROOT,
)

MANIFESTS = {
    "train": MANIFEST_TRAIN_PATH,
    "val": MANIFEST_VAL_PATH,
    "test": MANIFEST_TEST_PATH,
}

ANCHOR = "data" + os.sep + "processed_dataset"  # what we search for/rebuild from


def fix_path(old_path: str) -> str:
    normalized = old_path.replace("/", os.sep).replace("\\", os.sep)
    marker = "data" + os.sep + "processed_dataset"
    idx = normalized.find(marker)
    if idx == -1:
        # try the other slash style just in case
        alt = old_path.replace("\\", "/")
        idx2 = alt.find("data/processed_dataset")
        if idx2 == -1:
            return old_path  # couldn't find the anchor - leave untouched, will be reported
        relative = alt[idx2:].replace("/", os.sep)
    else:
        relative = normalized[idx:]
    return os.path.join(PROJECT_ROOT, relative)


def fix_manifest(name, path):
    if not os.path.exists(path):
        print(f"[{name}] SKIPPED - file not found at {path}")
        return

    backup_path = path.replace(".csv", ".colab_paths.csv")
    if not os.path.exists(backup_path):
        shutil.copy(path, backup_path)
        print(f"[{name}] backed up original -> {backup_path}")

    df = pd.read_csv(path)
    if "filepath" not in df.columns:
        print(f"[{name}] SKIPPED - no 'filepath' column found (columns: {list(df.columns)})")
        return

    sample_before = df["filepath"].iloc[0]
    df["filepath"] = df["filepath"].apply(fix_path)
    sample_after = df["filepath"].iloc[0]

    df.to_csv(path, index=False)

    exists_count = df["filepath"].apply(os.path.exists).sum()
    total = len(df)

    print(f"[{name}] {total} rows rewritten")
    print(f"[{name}]   before: {sample_before}")
    print(f"[{name}]   after:  {sample_after}")
    print(f"[{name}]   files that actually exist on disk: {exists_count}/{total}")
    if exists_count < total:
        print(f"[{name}]   WARNING: {total - exists_count} paths still don't resolve - "
              f"check that data/processed_dataset/ has the same folder structure as Colab.")


if __name__ == "__main__":
    print(f"PROJECT_ROOT resolved to: {PROJECT_ROOT}\n")
    for name, path in MANIFESTS.items():
        fix_manifest(name, path)
        print()

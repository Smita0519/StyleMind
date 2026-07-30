"""
Step 6 — Stratified train/val/test split (70/15/15), stratified by category
so class proportions stay consistent across all three splits. Fixed random
seed for reproducibility.
"""

import pandas as pd
from sklearn.model_selection import train_test_split

from config import (
    CLIP_LABELED_MANIFEST_PATH, MANIFEST_TEST_PATH, MANIFEST_TRAIN_PATH,
    MANIFEST_VAL_PATH, SPLIT_RANDOM_SEED, TRAIN_FRACTION,
    VAL_FRACTION_OF_REMAINDER,
)


def split_dataset():
    labeled_df = pd.read_csv(CLIP_LABELED_MANIFEST_PATH)

    train_df, temp_df = train_test_split(
        labeled_df,
        test_size=1 - TRAIN_FRACTION,
        stratify=labeled_df["category"],
        random_state=SPLIT_RANDOM_SEED,
    )
    val_df, test_df = train_test_split(
        temp_df,
        test_size=1 - VAL_FRACTION_OF_REMAINDER,
        stratify=temp_df["category"],
        random_state=SPLIT_RANDOM_SEED,
    )

    print(f"Train: {len(train_df)} ({len(train_df)/len(labeled_df):.1%})")
    print(f"Val:   {len(val_df)} ({len(val_df)/len(labeled_df):.1%})")
    print(f"Test:  {len(test_df)} ({len(test_df)/len(labeled_df):.1%})")

    # Sanity check: category proportions should be near-identical across splits
    print("\n=== Category % by split ===")
    for name, df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        print(f"\n{name}:")
        print((df["category"].value_counts(normalize=True) * 100).round(1))

    train_df.to_csv(MANIFEST_TRAIN_PATH, index=False)
    val_df.to_csv(MANIFEST_VAL_PATH, index=False)
    test_df.to_csv(MANIFEST_TEST_PATH, index=False)

    print("\nSplits saved.")
    return train_df, val_df, test_df


if __name__ == "__main__":
    split_dataset()

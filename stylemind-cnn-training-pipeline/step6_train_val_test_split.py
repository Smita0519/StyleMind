"""
Step 6 - Stratified train/val/test split (70/15/15).

v2 CHANGE: stratification key is now (category + season) combined,
not category alone. Category-only stratification guarantees category
balance across splits but says nothing about season or texture balance -
if e.g. 'all-season' happened to cluster unevenly across the split, the
season head would train/validate on a skewed distribution silently. This
still doesn't explicitly balance texture, but combined category+season
stratification is the highest-value fix since season is the harder head
and category is already covered; texture proportions are printed below
so any drift is at least visible rather than silent.

Falls back to category-only stratification (with a warning) if any
category+season combination has fewer than 2 samples, since
train_test_split's stratify requires at least 2 members per stratum.
"""

import pandas as pd
from sklearn.model_selection import train_test_split

from config import (
    CLIP_LABELED_MANIFEST_PATH, MANIFEST_TEST_PATH, MANIFEST_TRAIN_PATH,
    MANIFEST_VAL_PATH, SPLIT_RANDOM_SEED, TRAIN_FRACTION,
    VAL_FRACTION_OF_REMAINDER,
)


def _pick_stratify_key(df):
    combo = df["category"] + "|" + df["season"]
    combo_counts = combo.value_counts()
    rare_combos = combo_counts[combo_counts < 2]
    if len(rare_combos) > 0:
        print(f"WARNING: {len(rare_combos)} category+season combinations have "
              f"< 2 samples, e.g. {list(rare_combos.index[:5])}. "
              "Falling back to category-only stratification.")
        return df["category"]
    print("Using combined (category + season) stratification.")
    return combo


def split_dataset():
    labeled_df = pd.read_csv(CLIP_LABELED_MANIFEST_PATH)
    stratify_key = _pick_stratify_key(labeled_df)

    train_df, temp_df = train_test_split(
        labeled_df,
        test_size=1 - TRAIN_FRACTION,
        stratify=stratify_key,
        random_state=SPLIT_RANDOM_SEED,
    )
    temp_stratify_key = _pick_stratify_key(temp_df)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=1 - VAL_FRACTION_OF_REMAINDER,
        stratify=temp_stratify_key,
        random_state=SPLIT_RANDOM_SEED,
    )

    print(f"\nTrain: {len(train_df)} ({len(train_df)/len(labeled_df):.1%})")
    print(f"Val:   {len(val_df)} ({len(val_df)/len(labeled_df):.1%})")
    print(f"Test:  {len(test_df)} ({len(test_df)/len(labeled_df):.1%})")

    # Sanity check: category, season, AND texture proportions should be
    # close across splits. Category/season are explicitly stratified for;
    # texture is printed for visibility only (not stratified on).
    for label_col in ["category", "season", "texture"]:
        print(f"\n=== {label_col} % by split ===")
        for name, df in [("train", train_df), ("val", val_df), ("test", test_df)]:
            print(f"\n{name}:")
            print((df[label_col].value_counts(normalize=True) * 100).round(1))

    train_df.to_csv(MANIFEST_TRAIN_PATH, index=False)
    val_df.to_csv(MANIFEST_VAL_PATH, index=False)
    test_df.to_csv(MANIFEST_TEST_PATH, index=False)

    print("\nSplits saved.")
    return train_df, val_df, test_df


if __name__ == "__main__":
    split_dataset()

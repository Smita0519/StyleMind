"""
Step 7 — Encode labels for all three heads, save label maps, and build
the tf.data.Dataset pipelines (with augmentation on the training set only).
"""

import json

import pandas as pd
import tensorflow as tf

from config import (
    BATCH_SIZE, IMG_SIZE, LABEL_MAPS_PATH, MANIFEST_TEST_PATH,
    MANIFEST_TRAIN_PATH, MANIFEST_VAL_PATH,
)

AUTOTUNE = tf.data.AUTOTUNE


def build_label_maps(labeled_df):
    """
    Fits label encodings on the FULL labeled set so class indices stay
    consistent across train/val/test — never fit separately per split.
    """
    category_classes = sorted(labeled_df["category"].unique())
    texture_classes = sorted(labeled_df["texture"].unique())
    season_classes = sorted(labeled_df["season"].unique())

    category_to_idx = {c: i for i, c in enumerate(category_classes)}
    texture_to_idx = {t: i for i, t in enumerate(texture_classes)}
    season_to_idx = {s: i for i, s in enumerate(season_classes)}

    print(f"Category classes ({len(category_classes)}): {category_classes}")
    print(f"Texture classes ({len(texture_classes)}): {texture_classes}")
    print(f"Season classes ({len(season_classes)}): {season_classes}")

    label_maps = {"category": category_to_idx, "texture": texture_to_idx, "season": season_to_idx}
    with open(LABEL_MAPS_PATH, "w") as f:
        json.dump(label_maps, f, indent=2)
    print(f"\nLabel maps saved -> {LABEL_MAPS_PATH}")

    return category_to_idx, texture_to_idx, season_to_idx


def load_and_preprocess(filepath, category_idx, texture_idx, season_idx):
    img = tf.io.read_file(filepath)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, [IMG_SIZE, IMG_SIZE])
    img = tf.cast(img, tf.float32) / 255.0
    return img, {"category": category_idx, "texture": texture_idx, "season": season_idx}


# Augmentation layer — applied to the training set only
data_augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal"),
    tf.keras.layers.RandomRotation(0.08),
    tf.keras.layers.RandomZoom(0.1),
])


def augment(img, labels):
    return data_augmentation(img, training=True), labels


def make_dataset(df, category_to_idx, texture_to_idx, season_to_idx, training=False):
    filepaths = df["filepath"].values
    category_idx = df["category"].map(category_to_idx).values
    texture_idx = df["texture"].map(texture_to_idx).values
    season_idx = df["season"].map(season_to_idx).values

    ds = tf.data.Dataset.from_tensor_slices((filepaths, category_idx, texture_idx, season_idx))
    ds = ds.map(load_and_preprocess, num_parallel_calls=AUTOTUNE)

    if training:
        # shuffle=True re-randomizes batch composition every epoch,
        # preventing gradient bias from fixed category ordering
        ds = ds.shuffle(buffer_size=len(df), reshuffle_each_iteration=True)
        ds = ds.map(augment, num_parallel_calls=AUTOTUNE)

    ds = ds.batch(BATCH_SIZE)
    ds = ds.prefetch(AUTOTUNE)
    return ds


def build_datasets():
    train_df = pd.read_csv(MANIFEST_TRAIN_PATH)
    val_df = pd.read_csv(MANIFEST_VAL_PATH)
    test_df = pd.read_csv(MANIFEST_TEST_PATH)

    # Label maps must be fit on the union of all splits (equivalent to the
    # full labeled_df) so indices match everywhere
    full_df = pd.concat([train_df, val_df, test_df], ignore_index=True)
    category_to_idx, texture_to_idx, season_to_idx = build_label_maps(full_df)

    train_ds = make_dataset(train_df, category_to_idx, texture_to_idx, season_to_idx, training=True)
    val_ds = make_dataset(val_df, category_to_idx, texture_to_idx, season_to_idx, training=False)
    test_ds = make_dataset(test_df, category_to_idx, texture_to_idx, season_to_idx, training=False)

    print("\nDatasets built.")
    for imgs, labels in train_ds.take(1):
        print("Image batch shape:", imgs.shape)
        print("Category label batch shape:", labels["category"].shape)
        print("Texture label batch shape:", labels["texture"].shape)
        print("Season label batch shape:", labels["season"].shape)

    return train_ds, val_ds, test_ds, (category_to_idx, texture_to_idx, season_to_idx)


if __name__ == "__main__":
    build_datasets()

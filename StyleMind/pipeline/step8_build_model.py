"""
Step 8 — Build the 3-head MobileNetV2 model.

Backbone: MobileNetV2, ImageNet-pretrained, frozen for phase 1 transfer
learning. Chosen over a larger backbone for fast Colab training, mobile/
edge-deployment friendliness, and because garment classification doesn't
need extra model capacity. With only a few hundred images per category,
training from scratch would overfit badly — ImageNet pretraining supplies
general visual features (edges, shapes, textures) that transfer well to
clothing.

Three heads (category, texture, season) share a trunk and are trained
jointly, each with its own small dense branch and softmax output.
"""

from tensorflow.keras import Model, layers
from tensorflow.keras.applications import MobileNetV2

from config import IMG_SIZE, PHASE1_LEARNING_RATE
import tensorflow as tf


def build_model(num_category, num_texture, num_season):
    base_model = MobileNetV2(
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
        pooling="avg",
    )
    base_model.trainable = False  # frozen for phase 1

    inputs = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
    x = base_model(inputs, training=False)
    x = layers.Dropout(0.3)(x)

    # Shared trunk
    shared = layers.Dense(256, activation="relu")(x)
    shared = layers.Dropout(0.3)(shared)

    # Category head
    cat_branch = layers.Dense(128, activation="relu")(shared)
    category_output = layers.Dense(num_category, activation="softmax", name="category")(cat_branch)

    # Texture head
    tex_branch = layers.Dense(128, activation="relu")(shared)
    texture_output = layers.Dense(num_texture, activation="softmax", name="texture")(tex_branch)

    # Season head
    sea_branch = layers.Dense(64, activation="relu")(shared)
    season_output = layers.Dense(num_season, activation="softmax", name="season")(sea_branch)

    model = Model(inputs=inputs, outputs=[category_output, texture_output, season_output])
    return model, base_model


def compile_model(model, learning_rate=PHASE1_LEARNING_RATE):
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss={
            "category": "sparse_categorical_crossentropy",
            "texture": "sparse_categorical_crossentropy",
            "season": "sparse_categorical_crossentropy",
        },
        loss_weights={"category": 1.0, "texture": 1.0, "season": 1.0},
        metrics={"category": "accuracy", "texture": "accuracy", "season": "accuracy"},
    )
    return model


if __name__ == "__main__":
    # Example shapes matching the final dataset (10 categories, 7 textures,
    # 4 season classes including the 'all-season' fallback outcome)
    model, base_model = build_model(num_category=10, num_texture=7, num_season=4)
    compile_model(model)
    model.summary()

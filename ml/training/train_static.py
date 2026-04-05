"""
Train static sign classifier (alphabets A-Z, numbers 0-9).
Architecture: Dense MLP with BatchNorm + Dropout.
Input: 63-dim hand landmark vector (normalized).
Target accuracy: 90%+

Usage:
    python train_static.py
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import json
import shutil
from pathlib import Path
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt

DATA_PATH = Path("../data/processed")
MODEL_SAVE_PATH = Path("../models/static_classifier")
EPOCHS = 100
BATCH_SIZE = 64
LEARNING_RATE = 1e-3


def build_model(input_dim: int, num_classes: int) -> keras.Model:
    """Build MLP classifier for static hand landmarks."""
    inputs = keras.Input(shape=(input_dim,), name="landmarks")
    x = layers.Dense(512, activation="relu")(inputs)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)
    model = keras.Model(inputs=inputs, outputs=outputs)
    return model


def train():
    # Load preprocessed data
    X_train = np.load(DATA_PATH / "static_X_train.npy")
    y_train = np.load(DATA_PATH / "static_y_train.npy")
    X_val = np.load(DATA_PATH / "static_X_val.npy")
    y_val = np.load(DATA_PATH / "static_y_val.npy")
    X_test = np.load(DATA_PATH / "static_X_test.npy")
    y_test = np.load(DATA_PATH / "static_y_test.npy")

    with open(DATA_PATH / "static_label_map.json") as f:
        label_map = json.load(f)

    num_classes = len(label_map)
    input_dim = X_train.shape[1]
    print(f"Classes: {num_classes}, Input dim: {input_dim}")
    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # Compute class weights for imbalanced data
    class_weights = compute_class_weight("balanced", classes=np.unique(y_train), y=y_train)
    class_weight_dict = dict(enumerate(class_weights))

    model = build_model(input_dim, num_classes)
    model.compile(
        optimizer=keras.optimizers.Adam(LEARNING_RATE),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    model.summary()

    callbacks = [
        keras.callbacks.EarlyStopping(patience=15, restore_best_weights=True, monitor="val_accuracy"),
        keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=7, min_lr=1e-6),
        keras.callbacks.ModelCheckpoint(str(MODEL_SAVE_PATH / "best_checkpoint"), save_best_only=True)
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        class_weight=class_weight_dict,
        callbacks=callbacks,
        verbose=1
    )

    # Evaluate on test set
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"\nTest accuracy: {test_acc:.4f} ({test_acc * 100:.2f}%)")
    if test_acc < 0.90:
        print("WARNING: Test accuracy below 90% target. Consider more data or hyperparameter tuning.")

    # Save as TF SavedModel
    if MODEL_SAVE_PATH.exists():
        shutil.rmtree(MODEL_SAVE_PATH)
    MODEL_SAVE_PATH.mkdir(parents=True)
    tf.saved_model.save(model, str(MODEL_SAVE_PATH))
    print(f"Model saved to {MODEL_SAVE_PATH}")

    # Copy label map to model directory
    shutil.copy(DATA_PATH / "static_label_map.json", MODEL_SAVE_PATH / "label_map.json")

    # Save training history plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(history.history["accuracy"], label="Train")
    ax1.plot(history.history["val_accuracy"], label="Val")
    ax1.set_title("Accuracy")
    ax1.legend()
    ax2.plot(history.history["loss"], label="Train")
    ax2.plot(history.history["val_loss"], label="Val")
    ax2.set_title("Loss")
    ax2.legend()
    plt.savefig(MODEL_SAVE_PATH / "training_history.png", dpi=100, bbox_inches="tight")
    plt.close()
    print("Training complete!")


if __name__ == "__main__":
    train()

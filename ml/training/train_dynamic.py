"""
Train dynamic sign classifier (296 ISL word signs from INCLUDE dataset).
Architecture: BiLSTM(256x2) + Attention + Dense head.
Augmentation: Gaussian noise, feature dropout, time masking.
LR: Cosine decay with warmup.
Target: 90%+ accuracy on GPU (RTX 4060 ~15-25 min).

Usage:
    python train_dynamic.py
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
MODEL_SAVE_PATH = Path("../models/dynamic_classifier")
EPOCHS = 300
BATCH_SIZE = 64          # GPU batch size
LEARNING_RATE = 1e-3
MIN_LR = 5e-7
WARMUP_EPOCHS = 10
SEQ_LEN = 45
FEATURE_DIM = 258
PATIENCE = 40            # generous patience for cosine schedule


# ── Data augmentation ────────────────────────────────────────────────────────

def augment_batch(X, noise_std=0.008, drop_prob=0.04):
    """
    Apply random augmentations to a batch of sequences.
    All augmentations are label-preserving for sign language features.
    """
    X = X.copy()
    n = len(X)

    # 1. Additive Gaussian noise (50% of batch)
    idx = np.where(np.random.random(n) < 0.5)[0]
    if len(idx):
        X[idx] += np.random.normal(0, noise_std, X[idx].shape).astype(np.float32)

    # 2. Feature dropout — randomly zero individual landmark coords (40%)
    idx = np.where(np.random.random(n) < 0.4)[0]
    if len(idx):
        mask = (np.random.random(X[idx].shape) > drop_prob).astype(np.float32)
        X[idx] *= mask

    # 3. Time masking — zero a random consecutive segment (30%)
    for i in np.where(np.random.random(n) < 0.3)[0]:
        mask_len = np.random.randint(3, 9)
        start = np.random.randint(0, SEQ_LEN - mask_len)
        X[i, start:start + mask_len] = 0.0

    # 4. Temporal scaling — resample sequence at slight speed offset (20%)
    for i in np.where(np.random.random(n) < 0.2)[0]:
        scale = np.random.uniform(0.8, 1.2)
        orig_len = max(5, int(SEQ_LEN * scale))
        src = np.linspace(0, orig_len - 1, SEQ_LEN).astype(int)
        src = np.clip(src, 0, SEQ_LEN - 1)
        X[i] = X[i][src]

    return X.astype(np.float32)


class AugmentedGenerator(keras.utils.Sequence):
    """On-the-fly augmentation generator."""
    def __init__(self, X, y, batch_size, augment=True):
        self.X = X
        self.y = y
        self.batch_size = batch_size
        self.augment = augment
        self.indices = np.arange(len(X))

    def __len__(self):
        return int(np.ceil(len(self.X) / self.batch_size))

    def __getitem__(self, idx):
        batch_idx = self.indices[idx * self.batch_size:(idx + 1) * self.batch_size]
        Xb = self.X[batch_idx].copy()
        if self.augment:
            Xb = augment_batch(Xb)
        return Xb, self.y[batch_idx]

    def on_epoch_end(self):
        np.random.shuffle(self.indices)


# ── Model ────────────────────────────────────────────────────────────────────

class AttentionLayer(layers.Layer):
    def __init__(self, units, **kwargs):
        super().__init__(**kwargs)
        self.W = layers.Dense(units)
        self.V = layers.Dense(1)

    def call(self, encoder_output):
        score = self.V(tf.nn.tanh(self.W(encoder_output)))
        weights = tf.nn.softmax(score, axis=1)
        return tf.reduce_sum(weights * encoder_output, axis=1)


def build_model(num_classes: int) -> keras.Model:
    """BiLSTM(256x2) + Attention + Dense head with LayerNorm input."""
    inputs = keras.Input(shape=(SEQ_LEN, FEATURE_DIM), name="sequence")

    # Normalize raw MediaPipe features
    x = layers.LayerNormalization()(inputs)

    # BiLSTM encoder — two stacked layers at 256 units each
    x = layers.Bidirectional(
        layers.LSTM(256, return_sequences=True, dropout=0.3, recurrent_dropout=0.05),
        name="bilstm_1")(x)
    x = layers.Bidirectional(
        layers.LSTM(256, return_sequences=True, dropout=0.3, recurrent_dropout=0.05),
        name="bilstm_2")(x)

    # Attention pooling over time
    x = AttentionLayer(128, name="attention")(x)

    # Classification head
    x = layers.Dense(512, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.5)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.4)(x)
    # float32 output required even with mixed precision
    outputs = layers.Dense(num_classes, activation="softmax",
                           dtype="float32", name="predictions")(x)

    return keras.Model(inputs, outputs)


# ── LR schedule ──────────────────────────────────────────────────────────────

def cosine_lr(epoch):
    """Linear warmup followed by cosine decay."""
    if epoch < WARMUP_EPOCHS:
        return LEARNING_RATE * (epoch + 1) / WARMUP_EPOCHS
    progress = (epoch - WARMUP_EPOCHS) / max(1, EPOCHS - WARMUP_EPOCHS)
    cosine = 0.5 * (1 + np.cos(np.pi * progress))
    return float(MIN_LR + (LEARNING_RATE - MIN_LR) * cosine)


# ── Training ─────────────────────────────────────────────────────────────────

def train():
    # Load preprocessed data
    X_train = np.load(DATA_PATH / "dynamic_X_train.npy")
    y_train = np.load(DATA_PATH / "dynamic_y_train.npy")
    X_val   = np.load(DATA_PATH / "dynamic_X_val.npy")
    y_val   = np.load(DATA_PATH / "dynamic_y_val.npy")
    X_test  = np.load(DATA_PATH / "dynamic_X_test.npy")
    y_test  = np.load(DATA_PATH / "dynamic_y_test.npy")

    with open(DATA_PATH / "dynamic_label_map.json") as f:
        label_map = json.load(f)

    num_classes = len(label_map)
    print(f"Classes: {num_classes}")
    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    print(f"Sequence shape: {X_train.shape}")

    # GPU setup
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"Training on GPU: {gpus[0].name}")
        # Mixed precision — ~30% faster on RTX 40xx
        tf.keras.mixed_precision.set_global_policy("mixed_float16")
        print("Mixed precision: mixed_float16")
    else:
        print("No GPU — training on CPU")

    # Balanced class weights (mapped to actual indices)
    unique_train = np.unique(y_train)
    weights_arr = compute_class_weight("balanced", classes=unique_train, y=y_train)
    class_weight_dict = {int(c): float(w) for c, w in zip(unique_train, weights_arr)}
    for c in range(num_classes):
        if c not in class_weight_dict:
            class_weight_dict[c] = 1.0

    # One-hot encode for label smoothing support
    y_train_oh = tf.keras.utils.to_categorical(y_train, num_classes).astype(np.float32)
    y_val_oh   = tf.keras.utils.to_categorical(y_val,   num_classes).astype(np.float32)

    # Generators with one-hot labels
    train_gen = AugmentedGenerator(X_train, y_train_oh, BATCH_SIZE, augment=True)
    val_gen   = AugmentedGenerator(X_val,   y_val_oh,   BATCH_SIZE, augment=False)

    model = build_model(num_classes)
    model.compile(
        optimizer=keras.optimizers.Adam(LEARNING_RATE),
        loss=keras.losses.CategoricalCrossentropy(label_smoothing=0.1),
        metrics=["accuracy"]
    )
    model.summary()

    checkpoint_dir = str(MODEL_SAVE_PATH / "best_checkpoint")
    callbacks = [
        keras.callbacks.EarlyStopping(
            patience=PATIENCE, restore_best_weights=True, monitor="val_accuracy"),
        keras.callbacks.LearningRateScheduler(cosine_lr, verbose=0),
        keras.callbacks.ModelCheckpoint(
            checkpoint_dir, save_best_only=True, monitor="val_accuracy"),
    ]

    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS,
        class_weight=class_weight_dict,
        callbacks=callbacks,
        verbose=1
    )

    # Evaluate on test set
    y_test_oh = tf.keras.utils.to_categorical(y_test, num_classes).astype(np.float32)
    preds = model.predict(X_test, batch_size=BATCH_SIZE, verbose=0)
    test_acc = float(np.mean(np.argmax(preds, axis=1) == y_test))
    print(f"\nTest accuracy: {test_acc:.4f} ({test_acc * 100:.2f}%)")
    if test_acc < 0.90:
        print(f"WARNING: below 90% target. Best val_acc: "
              f"{max(history.history['val_accuracy']):.4f}")

    # Save model
    if MODEL_SAVE_PATH.exists():
        shutil.rmtree(MODEL_SAVE_PATH)
    MODEL_SAVE_PATH.mkdir(parents=True)
    tf.saved_model.save(model, str(MODEL_SAVE_PATH))
    shutil.copy(DATA_PATH / "dynamic_label_map.json", MODEL_SAVE_PATH / "label_map.json")

    # Training curve
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(history.history["accuracy"],     label="Train")
    ax1.plot(history.history["val_accuracy"], label="Val")
    ax1.set_title("Accuracy")
    ax1.legend()
    ax2.plot(history.history["loss"],     label="Train")
    ax2.plot(history.history["val_loss"], label="Val")
    ax2.set_title("Loss")
    ax2.legend()
    plt.tight_layout()
    plt.savefig(MODEL_SAVE_PATH / "training_history.png", dpi=100, bbox_inches="tight")
    plt.close()
    print("Dynamic model saved.")


if __name__ == "__main__":
    train()

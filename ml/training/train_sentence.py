"""
Train ISL sentence recognition model using CTC loss.
Architecture: Conv1D + Bidirectional LSTM + CTC decoder.
Input: Variable-length sequences of 258-dim MediaPipe features.
Target: Word-level CTC transcription.

Usage:
    python train_sentence.py
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import json
import shutil
from pathlib import Path

DATA_PATH = Path("../data/processed")
MODEL_SAVE_PATH = Path("../models/sentence_model")
EPOCHS = 80
BATCH_SIZE = 16
LEARNING_RATE = 1e-3
MAX_SEQ_LEN = 300
FEATURE_DIM = 258


def build_ctc_model(num_classes: int):
    """
    Build CTC training and inference models.
    Training model takes (sequence, labels, input_length, label_length) and outputs CTC loss.
    Inference model takes sequence and outputs softmax logits.
    """
    sequence_input = keras.Input(shape=(None, FEATURE_DIM), name="sequence")
    labels_input = keras.Input(shape=(None,), dtype=tf.int32, name="labels")
    input_length = keras.Input(shape=(1,), dtype=tf.int32, name="input_length")
    label_length = keras.Input(shape=(1,), dtype=tf.int32, name="label_length")

    # Conv1D feature extractor
    x = layers.Conv1D(128, 3, activation="relu", padding="same")(sequence_input)
    x = layers.Conv1D(128, 3, activation="relu", padding="same")(x)
    x = layers.MaxPooling1D(2)(x)  # halves the time dimension

    # BiLSTM encoder
    x = layers.Bidirectional(layers.LSTM(256, return_sequences=True, dropout=0.3))(x)
    x = layers.Bidirectional(layers.LSTM(256, return_sequences=True, dropout=0.3))(x)

    # Output projection (num_classes + 1 for CTC blank token)
    y_pred = layers.Dense(num_classes + 1, activation="softmax", name="ctc_output")(x)

    # CTC loss layer — embedded in model so training works with standard .fit()
    ctc_loss = keras.backend.ctc_batch_cost(labels_input, y_pred, input_length, label_length)

    training_model = keras.Model(
        inputs=[sequence_input, labels_input, input_length, label_length],
        outputs=ctc_loss,
        name="ctc_training_model"
    )

    # Inference model: just the encoder (no loss computation)
    inference_model = keras.Model(inputs=sequence_input, outputs=y_pred, name="ctc_inference_model")

    return training_model, inference_model


def prepare_ctc_data(sequences, labels, vocab_map, max_seq_len, max_label_len):
    """
    Pad sequences and encode labels for CTC training.
    Returns (X, Y, input_lengths, label_lengths) where all are numpy arrays.
    CTC requires nonneg integer labels and actual lengths for both input and label.
    """
    n = len(sequences)
    X = np.zeros((n, max_seq_len, FEATURE_DIM), dtype=np.float32)
    Y = np.zeros((n, max_label_len), dtype=np.int32)  # 0-padded (CTC requires nonneg)
    input_lengths = np.zeros((n, 1), dtype=np.int32)
    label_lengths = np.zeros((n, 1), dtype=np.int32)

    for i, (seq, label) in enumerate(zip(sequences, labels)):
        length = min(len(seq), max_seq_len)
        X[i, :length] = seq[:length]
        # After MaxPooling1D(2), temporal dimension is halved
        input_lengths[i, 0] = max(1, length // 2)
        words = label.split()
        actual_len = min(len(words), max_label_len)
        for j, word in enumerate(words[:actual_len]):
            Y[i, j] = vocab_map.get(word, 0)
        label_lengths[i, 0] = actual_len

    return X, Y, input_lengths, label_lengths


def train():
    sequences = np.load(DATA_PATH / "sentence_sequences.npy", allow_pickle=True)
    with open(DATA_PATH / "sentence_labels.json") as f:
        labels = json.load(f)
    with open(DATA_PATH / "sentence_vocab.json") as f:
        vocab_map = json.load(f)

    num_classes = len(vocab_map)
    max_label_len = max(len(l.split()) for l in labels)
    print(f"Vocab: {num_classes}, Max label len: {max_label_len}, Sequences: {len(sequences)}")

    X, Y, input_lengths, label_lengths = prepare_ctc_data(
        sequences, labels, vocab_map, MAX_SEQ_LEN, max_label_len
    )

    split = int(0.85 * len(X))
    X_train, X_val = X[:split], X[split:]
    Y_train, Y_val = Y[:split], Y[split:]
    il_train, il_val = input_lengths[:split], input_lengths[split:]
    ll_train, ll_val = label_lengths[:split], label_lengths[split:]

    # Enable GPU memory growth
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print(f"Training on GPU: {gpus[0].name}")
    else:
        print("No GPU found, training on CPU")

    training_model, inference_model = build_ctc_model(num_classes)

    # Loss is computed inside the model; the dummy_loss just returns the model output
    training_model.compile(
        optimizer=keras.optimizers.Adam(LEARNING_RATE),
        loss=lambda y_true, y_pred: y_pred
    )
    training_model.summary()

    dummy_y_train = np.zeros(len(X_train), dtype=np.float32)
    dummy_y_val = np.zeros(len(X_val), dtype=np.float32)

    callbacks = [
        keras.callbacks.EarlyStopping(patience=15, restore_best_weights=True),
        keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=7, min_lr=1e-6)
    ]

    training_model.fit(
        [X_train, Y_train, il_train, ll_train],
        dummy_y_train,
        validation_data=([X_val, Y_val, il_val, ll_val], dummy_y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1
    )

    if MODEL_SAVE_PATH.exists():
        shutil.rmtree(MODEL_SAVE_PATH)
    MODEL_SAVE_PATH.mkdir(parents=True)

    # Save the inference model (not the training model with CTC inputs)
    tf.saved_model.save(inference_model, str(MODEL_SAVE_PATH))
    shutil.copy(DATA_PATH / "sentence_vocab.json", MODEL_SAVE_PATH / "vocab.json")
    print("Sentence model training complete!")


if __name__ == "__main__":
    train()

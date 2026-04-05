"""
Evaluate all trained models and print comprehensive metrics.

Usage:
    python evaluate.py --model static
    python evaluate.py --model dynamic
    python evaluate.py --all
"""

import numpy as np
import tensorflow as tf
import json
import argparse
from pathlib import Path
from sklearn.metrics import classification_report, confusion_matrix, top_k_accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

DATA_PATH = Path("../data/processed")
MODELS_PATH = Path("../models")


def evaluate_static():
    print("\n=== Static Classifier Evaluation ===")
    X_test = np.load(DATA_PATH / "static_X_test.npy")
    y_test = np.load(DATA_PATH / "static_y_test.npy")

    with open(DATA_PATH / "static_label_map.json") as f:
        label_map = json.load(f)
    labels = [label_map[str(i)] for i in range(len(label_map))]

    model = tf.saved_model.load(str(MODELS_PATH / "static_classifier"))
    preds = model(tf.constant(X_test, dtype=tf.float32)).numpy()
    y_pred = np.argmax(preds, axis=1)

    acc = np.mean(y_pred == y_test)
    top3 = top_k_accuracy_score(y_test, preds, k=3)
    print(f"Top-1 Accuracy: {acc:.4f} ({acc * 100:.2f}%)")
    print(f"Top-3 Accuracy: {top3:.4f} ({top3 * 100:.2f}%)")
    print("\nPer-class report:")
    print(classification_report(y_test, y_pred, target_names=labels))

    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(16, 14))
    sns.heatmap(cm, annot=True, fmt="d", xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_title("Static Classifier Confusion Matrix")
    plt.tight_layout()
    plt.savefig(MODELS_PATH / "static_classifier" / "confusion_matrix.png", dpi=80)
    plt.close()
    print("Confusion matrix saved.")


def evaluate_dynamic():
    print("\n=== Dynamic Classifier Evaluation ===")
    X_test = np.load(DATA_PATH / "dynamic_X_test.npy")
    y_test = np.load(DATA_PATH / "dynamic_y_test.npy")

    with open(DATA_PATH / "dynamic_label_map.json") as f:
        label_map = json.load(f)
    labels = [label_map[str(i)] for i in range(len(label_map))]

    model = tf.saved_model.load(str(MODELS_PATH / "dynamic_classifier"))
    preds = model(tf.constant(X_test, dtype=tf.float32)).numpy()
    y_pred = np.argmax(preds, axis=1)

    all_class_indices = np.arange(len(label_map))
    acc = np.mean(y_pred == y_test)
    top5 = top_k_accuracy_score(y_test, preds, k=5, labels=all_class_indices)
    print(f"Top-1 Accuracy: {acc:.4f} ({acc * 100:.2f}%)")
    print(f"Top-5 Accuracy: {top5:.4f} ({top5 * 100:.2f}%)")
    print("\nPer-class report:")
    present = sorted(np.unique(y_test))
    present_names = [label_map[str(i)] for i in present]
    print(classification_report(y_test, y_pred, labels=present, target_names=present_names, zero_division=0))

    print(f"\nLowest accuracy classes:")
    per_class = {}
    for true, pred in zip(y_test, y_pred):
        per_class.setdefault(true, []).append(int(true == pred))
    worst = sorted(per_class.items(), key=lambda x: np.mean(x[1]))[:10]
    for cls, results in worst:
        print(f"  {labels[cls]}: {np.mean(results) * 100:.1f}%")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["static", "dynamic", "sentence"], default="static")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        evaluate_static()
        evaluate_dynamic()
    elif args.model == "static":
        evaluate_static()
    elif args.model == "dynamic":
        evaluate_dynamic()
    else:
        print(f"Evaluator for '{args.model}' not yet implemented.")


if __name__ == "__main__":
    main()

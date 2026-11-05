"""TV3: LSTM và Conv1D; chỉ ghi vào deep_learning/bo_sung_tv3.

Áp dụng chương 7 (encoding, padding, embedding, LSTM/Conv1D), chương 8
(Sequential, binary cross entropy, Adam, dropout) và chương 5 (validation).
"""
import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "4")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "2")

from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import sys
import time

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, precision_recall_curve
from sklearn.utils.class_weight import compute_class_weight
from text_processing import unicode_lower

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ML = ROOT / "traditional_ml/bo_sung_tv2"
sys.path.insert(0, str(ROOT / "traditional_ml/TV2_hoc_may"))
from evaluate import evaluate


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def dataset(x, y=None, train=False):
    ds = tf.data.Dataset.from_tensor_slices(x if y is None else (x, y))
    if train:
        ds = ds.shuffle(len(x), seed=42, reshuffle_each_iteration=True)
    options = tf.data.Options()
    options.threading.private_threadpool_size = 2
    return ds.batch(32).with_options(options).prefetch(1)


def build_model(architecture, vocab_size, sequence_length):
    layers = [keras.layers.Input(shape=(sequence_length,), dtype="int64"),
              keras.layers.Embedding(vocab_size, 64, mask_zero=architecture == "lstm")]
    if architecture == "lstm":
        layers += [keras.layers.LSTM(32, return_sequences=False)]
    elif architecture == "conv1d":
        layers += [keras.layers.Conv1D(64, 5, activation="relu", padding="valid"),
                   keras.layers.MaxPooling1D(2), keras.layers.GlobalMaxPooling1D(),
                   keras.layers.Dense(32, activation="relu")]
    else:
        raise ValueError(architecture)
    layers += [keras.layers.Dropout(.3), keras.layers.Dense(1, activation="sigmoid")]
    model = keras.Sequential(layers, name=architecture)
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=.001),
                  loss="binary_crossentropy", metrics=[keras.metrics.BinaryAccuracy(name="accuracy")])
    return model


def threshold_on_validation(y, scores):
    precision, recall, thresholds = precision_recall_curve(y, scores)
    f1 = 2 * precision[:-1] * recall[:-1] / (precision[:-1] + recall[:-1] + 1e-12)
    # Cố định cách phá hòa, không tham khảo nhãn test.
    candidates = np.flatnonzero(np.isclose(f1, f1.max(), atol=1e-12, rtol=0))
    chosen = max(candidates, key=lambda i: (precision[i], -abs(thresholds[i] - .5)))
    return float(thresholds[chosen])


def plot_training(history, target):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.3))
    for axis, key in zip(axes, ("loss", "accuracy")):
        axis.plot(np.arange(1, len(history[key]) + 1), history[key], label="train")
        axis.plot(np.arange(1, len(history[key]) + 1), history["val_" + key], label="validation")
        axis.set(xlabel="Epoch", ylabel=key); axis.legend(); axis.grid(alpha=.2)
    fig.tight_layout(); fig.savefig(target, dpi=160); plt.close(fig)


def run(language, max_epochs):
    base = HERE / language
    for folder in (base, base / "models", base / "results", base / "figures"):
        folder.mkdir(exist_ok=True)
    source = ML / language
    paths = {s: source / f"data/{s}.csv" for s in ("train", "val", "test")}
    frames = {s: pd.read_csv(p) for s, p in paths.items()}
    for split, frame in frames.items():
        if frame.text.isna().any() or not frame.id.is_unique or set(frame.y) != {0, 1}:
            raise ValueError(f"Dữ liệu không hợp lệ: {language}/{split}")
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        if set(frames[a].text) & set(frames[b].text):
            raise ValueError("Dữ liệu bị trùng giữa các tập")
    ml_predictions = pd.read_csv(source / "results/pred_ml_test.csv")
    pd.testing.assert_frame_equal(frames["test"][["id", "text", "y"]].rename(columns={"y": "y_true"}),
                                  ml_predictions[["id", "text", "y_true"]])
    ml_version = json.loads((source / "version.json").read_text(encoding="utf-8"))
    seed = 42
    keras.utils.set_random_seed(seed)
    tf.config.experimental.enable_op_determinism()
    # Độ dài chuỗi và từ vựng đều được xác định CHỈ từ train.
    lengths = frames["train"].text.str.split().str.len().to_numpy()
    sequence_length = int(np.clip(np.ceil(np.percentile(lengths, 95)), 24, 160))
    standardize = unicode_lower if language == "vi" else "lower"
    vectorizer = keras.layers.TextVectorization(max_tokens=12000, standardize=standardize, split="whitespace",
                                               output_mode="int", output_sequence_length=sequence_length)
    train_strings = tf.constant(frames["train"].text.to_list(), dtype=tf.string)
    vectorizer.adapt(dataset(train_strings))
    vocabulary = vectorizer.get_vocabulary()
    # Mô hình nhận số nguyên để tệp .keras không phụ thuộc hàm xử lý chuỗi tùy biến.
    x = {split: vectorizer(tf.constant(frame.text.to_list(), dtype=tf.string)).numpy()
         for split, frame in frames.items()}
    y = {split: frame.y.to_numpy(dtype=np.int32) for split, frame in frames.items()}
    preprocessing = {"standardize": "unicode_lower" if language == "vi" else "lower",
                     "split": "whitespace", "max_tokens": 12000,
                     "sequence_length": sequence_length, "vocabulary": vocabulary,
                     "padding": "post, token 0", "unknown_token": "[UNK], token 1",
                     "length_selected_from": "95th percentile of train token lengths, clipped to [24,160]"}
    write_json(base / "preprocessing.json", preprocessing)
    weights = compute_class_weight("balanced", classes=np.array([0, 1]), y=y["train"])
    class_weight = {0: float(weights[0]), 1: float(weights[1])}
    training_notes = []
    configs = {}
    for architecture in ("lstm", "conv1d"):
        keras.backend.clear_session()
        keras.utils.set_random_seed(seed)
        model = build_model(architecture, len(vocabulary), sequence_length)
        with (base / "models" / f"{architecture}_summary.txt").open("w", encoding="utf-8") as output:
            model.summary(print_fn=lambda line: output.write(line + "\n"))
        stop = keras.callbacks.EarlyStopping(monitor="val_loss", patience=3, min_delta=.001,
                                             restore_best_weights=True, verbose=1)
        start = time.perf_counter()
        print(f"\n{language}/{architecture}: train={len(y['train'])}, length={sequence_length}, vocab={len(vocabulary)}", flush=True)
        history = model.fit(dataset(x["train"], y["train"], train=True),
                            validation_data=dataset(x["val"], y["val"]), epochs=max_epochs,
                            class_weight=class_weight, callbacks=[stop], verbose=2)
        fit_seconds = time.perf_counter() - start
        model_path = base / "models" / f"{architecture}.keras"
        model.save(model_path)
        # Chọn ngưỡng bằng validation của chính model đã tải lại.
        loaded = keras.models.load_model(model_path, compile=False)
        scores = loaded.predict(dataset(x["val"]), verbose=0).reshape(-1)
        threshold = threshold_on_validation(y["val"], scores)
        val = evaluate(y["val"], (scores >= threshold).astype(int), scores)
        pred_val = frames["val"][["id", "text"]].assign(y_true=y["val"],
                      y_pred=(scores >= threshold).astype(int), score=scores)
        pred_val.to_csv(base / f"results/pred_{architecture}_val.csv", index=False)
        pd.DataFrame(history.history).rename_axis("epoch_index").to_csv(base / f"results/history_{architecture}.csv")
        plot_training(history.history, base / f"figures/history_{architecture}.png")
        configs[architecture] = {"architecture": architecture, "threshold": threshold,
                                  "model_file": f"models/{architecture}.keras", "model_sha256": digest(model_path),
                                  "validation": val, "epochs_run": len(history.history["loss"]),
                                  "restored_epoch": int(stop.best_epoch + 1), "fit_seconds": round(fit_seconds, 3),
                                  "parameters": model.count_params()}
        training_notes.append({"architecture": architecture, **val})
    # Lựa chọn khóa trước khi đọc điểm test của bất kỳ mô hình DL nào.
    best = max(configs, key=lambda name: (configs[name]["validation"]["F1"],
                                          configs[name]["validation"]["Precision"]))
    selection = {"selected": best, "criterion": "validation F1 spam, tie by validation Precision",
                 "candidates": configs, "dataset_id": ml_version["dataset_id"], "language": language,
                 "data_sha256": {s: digest(p) for s, p in paths.items()},
                 "preprocessing_sha256": digest(base / "preprocessing.json"),
                 "seed": seed, "class_weight": class_weight, "max_epochs": max_epochs,
                 "early_stopping": "val_loss, patience=3, min_delta=0.001, restore_best_weights=True",
                 "packages": {p: importlib.metadata.version(p) for p in ("tensorflow", "keras", "numpy", "pandas", "scikit-learn")},
                 "slide_basis": {"chapter_7": [85, 95, 98, 100, 158, 170, 171, 172, 173],
                                 "chapter_8": [66, 67, 155, 156, 157, 159]},
                 "test_note": "Benchmark kế thừa TV1/TV2, không phải test mới chưa từng dùng."}
    write_json(base / "model_config.json", selection)
    # Từ đây chỉ đo và báo cáo; không thay cấu hình dựa trên test.
    ml_report = json.loads((source / "results/ket_qua_cuoi.json").read_text(encoding="utf-8"))
    rows = [{"model": "ML_TV2", "selected_by_dl_validation": False,
             **ml_report["test_cuoi"], "threshold": json.loads((source / "model/config.json").read_text())["nguong"]}]
    per_model = {}
    for architecture, config in configs.items():
        model = keras.models.load_model(base / config["model_file"], compile=False)
        start = time.perf_counter()
        scores = model.predict(dataset(x["test"]), verbose=0).reshape(-1)
        batch_seconds = time.perf_counter() - start
        pred = (scores >= config["threshold"]).astype(int)
        result = evaluate(y["test"], pred, scores)
        output = frames["test"][["id", "text"]].assign(y_true=y["test"], y_pred=pred, score=scores)
        output.to_csv(base / f"results/pred_{architecture}_test.csv", index=False)
        output[output.y_true != output.y_pred].assign(
            error_type=lambda d: np.where(d.y_true == 0, "FP", "FN")).to_csv(
            base / f"results/errors_{architecture}.csv", index=False)
        if architecture == best:
            output.to_csv(base / "results/pred_dl_test.csv", index=False)
        rows.append({"model": architecture, "selected_by_dl_validation": architecture == best,
                     **result, "threshold": config["threshold"]})
        per_model[architecture] = {"test": result, "validation": config["validation"],
                                   "threshold": config["threshold"], "batch_inference_seconds": round(batch_seconds, 4)}
        fig, ax = plt.subplots(figsize=(4.5, 3.5))
        matrix = confusion_matrix(y["test"], pred, labels=[0, 1])
        ax.imshow(matrix, cmap="Blues")
        for row in range(2):
            for col in range(2):
                ax.text(col, row, str(matrix[row, col]), ha="center", va="center",
                        color="white" if matrix[row, col] > matrix.max() / 2 else "black")
        ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["ham", "spam"], yticklabels=["ham", "spam"],
               xlabel="Predicted", ylabel="Actual", title=f"{language}: {architecture} - test")
        fig.tight_layout(); fig.savefig(base / f"figures/confusion_{architecture}.png", dpi=160); plt.close(fig)
        print(language, architecture, "TEST", result, flush=True)
    pd.DataFrame(rows).to_csv(base / "results/comparison_ml_dl.csv", index=False)
    write_json(base / "results/summary.json", {"language": language, "dataset_id": ml_version["dataset_id"],
               "selected_by_validation": best, "models": per_model, "ml_baseline": ml_report["test_cuoi"],
               "train_val_test": {s: len(frame) for s, frame in frames.items()}})
    fig, ax = plt.subplots(figsize=(6.5, 4))
    table = pd.DataFrame(rows).set_index("model")
    table[["Precision", "Recall", "F1"]].plot.bar(ax=ax, ylim=(0, 1.05))
    ax.set_title(f"{language} - same test, spam class", pad=40)
    ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.01), ncol=3, frameon=False)
    ax.set_xlabel(""); ax.tick_params(axis="x", rotation=0)
    fig.tight_layout(); fig.savefig(base / "figures/comparison_ml_dl.png", dpi=160); plt.close(fig)
    print(f"{language}: selected {best} by validation; output {base}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("vi", "uci", "both"), default="both")
    parser.add_argument("--epochs", type=int, default=18)
    args = parser.parse_args()
    if args.epochs < 1:
        parser.error("epochs phải dương")
    for language in (("vi", "uci") if args.language == "both" else (args.language,)):
        run(language, args.epochs)

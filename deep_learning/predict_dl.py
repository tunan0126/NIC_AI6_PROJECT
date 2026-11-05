"""Giao diện suy luận Deep Learning (TV3): Conv1D & LSTM cho tiếng Việt và tiếng Anh UCI."""
import os
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "4")
os.environ.setdefault("TF_NUM_INTEROP_THREADS", "2")

from pathlib import Path
import argparse
import json
import sys

import tensorflow as tf
from tensorflow import keras

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "data_features"))
sys.path.insert(0, str(HERE))

from text_processing import unicode_lower

try:
    from privacy import redact
except ImportError:
    redact = lambda s: s


def load_model(language="vi", architecture=None):
    if language not in ("vi", "uci"):
        raise ValueError("language phải là vi hoặc uci")
    base = HERE / language
    config = json.loads((base / "model_config.json").read_text(encoding="utf-8"))
    name = architecture or config.get("selected", "conv1d")
    if name not in config["candidates"]:
        raise ValueError("architecture phải là lstm hoặc conv1d")
    candidate = config["candidates"][name]
    path = base / candidate["model_file"]
    
    prep_path = base / "preprocessing.json"
    prep = json.loads(prep_path.read_text(encoding="utf-8"))
    standardize = unicode_lower if prep.get("standardize") == "unicode_lower" else prep.get("standardize")
    vectorizer = keras.layers.TextVectorization(
        max_tokens=prep["max_tokens"],
        standardize=standardize,
        split=prep["split"],
        output_mode="int",
        output_sequence_length=prep["sequence_length"],
        vocabulary=prep["vocabulary"]
    )
    model = keras.models.load_model(path, compile=False)
    return model, vectorizer, {**candidate, "dataset_id": config.get("dataset_id", "unknown"), "language": language}


def predict(text, loaded):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Nội dung tin nhắn không được để trống")
    model, vectorizer, config = loaded
    prepared = redact(text) if config["language"] == "vi" else text
    tokens = vectorizer(tf.constant([prepared], dtype=tf.string))
    score = float(model(tokens, training=False).numpy()[0, 0])
    threshold = float(config.get("threshold", 0.5))
    return {
        "label": "spam" if score >= threshold else "ham",
        "score": score,
        "threshold": threshold,
        "model_version": config.get("model_sha256", "default")[:12],
        "architecture": config.get("architecture", "DL"),
        "dataset_id": config.get("dataset_id", "unknown"),
        "language": config["language"],
        "model_origin": "tv3"
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("vi", "uci"), default="vi")
    parser.add_argument("--architecture", choices=("lstm", "conv1d"))
    parser.add_argument("--text", required=True)
    args = parser.parse_args()
    print(json.dumps(predict(args.text, load_model(args.language, args.architecture)), ensure_ascii=False, indent=2))

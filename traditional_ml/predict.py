"""Giao diện suy luận Machine Learning (TV2). Hỗ trợ tiếng Việt (v2 tối ưu) và tiếng Anh UCI."""
from pathlib import Path
import argparse
import json
import sys
import joblib
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# Cho phép nạp các phụ thuộc tiền xử lý text
sys.path.insert(0, str(ROOT / "data_features"))
sys.path.insert(0, str(HERE))
try:
    import vi_text_v2
except ImportError:
    pass

try:
    from privacy import redact
except ImportError:
    redact = lambda s: s


def load_model(language="vi"):
    if language not in ("vi", "uci"):
        raise ValueError("language phải là vi hoặc uci")
    
    if language == "vi":
        base = HERE / "model"
        model = joblib.load(base / "model.joblib")
        config = json.loads((base / "config.json").read_text(encoding="utf-8"))
        version = json.loads((base / "version.json").read_text(encoding="utf-8"))
        threshold = float(config.get("threshold", config.get("nguong", 0.5)))
    else:
        base = HERE / "uci"
        model = joblib.load(base / "model/model.joblib")
        config = json.loads((base / "model/config.json").read_text(encoding="utf-8"))
        version = json.loads((base / "version.json").read_text(encoding="utf-8"))
        threshold = float(config.get("threshold", config.get("nguong", 0.5)))
        
    return model, threshold, version


def predict(text, loaded):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Nội dung tin nhắn không được để trống")
    model, threshold, version = loaded
    lang = version.get("language", "vi")
    prepared = redact(text) if lang == "vi" else text
    classes = list(model.classes_)
    idx = classes.index(1) if 1 in classes else classes.index("spam")
    score = float(np.round(model.predict_proba([prepared])[0, idx], version.get("score_decimals", 12)))
    
    return {
        "label": "spam" if score >= threshold else "ham",
        "score": score,
        "threshold": threshold,
        "model_version": version["model_sha256"][:12],
        "dataset_id": version.get("dataset_id", "unknown"),
        "language": lang,
        "architecture": version.get("architecture", "LinearSVC+TF-IDF"),
        "model_origin": "tv2"
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--language", choices=("vi", "uci"), default="vi")
    args = parser.parse_args()
    print(json.dumps(predict(args.text, load_model(args.language)), ensure_ascii=False, indent=2))

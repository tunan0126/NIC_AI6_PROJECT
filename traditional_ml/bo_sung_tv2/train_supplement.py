"""Chạy lại mã TV2 nguyên bản, xuất kết quả mới vào bo_sung_tv2/vi và uci."""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time

import joblib
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ORIGINAL = ROOT / "traditional_ml/TV2_hoc_may"
TV1 = ROOT / "data_features/bo_sung_tv1"
sys.path.insert(0, str(ORIGINAL))
from evaluate import evaluate
import train_ml
from select_complete import select


def finalize(language):
    """Đối chiếu lại chính mô hình xuất; chỉ ghi vào thư mục bổ sung.

    Tổng xác suất RandomForest song song có thể lệch rất nhỏ ngay ở ngưỡng.
    Cố định n_jobs khi triển khai và làm tròn 12 chữ số trước so ngưỡng.
    Không thay mô hình được chọn hay tối ưu ngưỡng bằng test.
    """
    destination = HERE / language
    results = destination / "results"
    model_path = destination / "model/model.joblib"
    model = joblib.load(model_path)
    if hasattr(model[-1], "n_jobs"):
        model[-1].set_params(n_jobs=1)
        joblib.dump(model, model_path)
    config_path = destination / "model/config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    threshold = float(config["nguong"])
    config["score_decimals"] = 12
    config["goi"] = "round(model.predict_proba(texts)[:,1], 12) >= nguong -> spam"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = results / "ket_qua_cuoi.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    original_report = results / "training_report_before_export_check.json"
    if not original_report.exists():
        original_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    data = {s: pd.read_csv(destination / f"data/{s}.csv") for s in ("train", "val", "test")}
    outputs = {}
    for split in ("test", "val"):
        frame = data[split]
        scores = np.round(model.predict_proba(frame.text)[:, list(model.classes_).index(1)], 12)
        pred = (scores >= threshold).astype(int)
        outputs[split] = pd.DataFrame({"id": frame.id, "text": frame.text,
                                       "y_true": frame.y, "y_pred": pred, "score": scores})
        outputs[split].to_csv(results / f"pred_ml_{split}.csv", index=False)
    test = outputs["test"]
    report["test_cuoi"] = evaluate(test.y_true, test.y_pred, test.score)
    known_keys = set(pd.concat([data["train"], data["val"]]).text.map(train_ml.template_key))
    seen = test.text.map(train_ml.template_key).isin(known_keys)
    for key, mask in (("mau_cau_da_thay_trong_train", seen), ("mau_cau_moi", ~seen)):
        part = test[mask]
        report["test_theo_nhom_mau_cau"][key] = {"so_tin": len(part), **evaluate(part.y_true, part.y_pred, part.score)}
    report["export_check"] = {"score_decimals": 12, "n_jobs": 1,
                              "note": "Điểm/nhãn tính lại bằng pipeline đã xuất, không chọn lại ngưỡng theo test."}
    start = time.perf_counter()
    model.predict_proba(data["test"].text)
    batch_seconds = time.perf_counter() - start
    inputs = list(data["test"].text.iloc[:100])
    start = time.perf_counter()
    for text in inputs:
        model.predict_proba([text])
    report["thoi_gian_suy_luan"] = {
        f"batch_{len(test)}_tin_s": round(batch_seconds, 4),
        "1_tin_ms": round((time.perf_counter() - start) * 1000 / len(inputs), 2)}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    errors = test[test.y_true != test.y_pred].copy()
    errors["loai_loi"] = np.where(errors.y_true == 0, "FP: tin tốt bị chặn nhầm", "FN: spam bị lọt")
    errors.to_csv(results / "tin_bi_doan_sai.csv", index=False, encoding="utf-8-sig")
    # Danh sách này chỉ gợi ý rà; không gán lại nhãn để tăng điểm.
    candidates = errors[(errors.y_true.eq(0) & errors.text.str.contains(
        r"casino|nap dau|nạp đầu|vay|bit\.ly|https?://|\.vip|\.bet|win", case=False)) |
        (errors.y_true.eq(0) & errors.score.ge(.8)) | (errors.y_true.eq(1) & errors.score.le(.2))].copy()
    candidates["ly_do"] = "Kiểm tra thủ công; không tự đổi nhãn theo mô hình"
    candidates["nhan_dung_theo_nhom"] = ""
    candidates.to_csv(results / "tin_can_ra_soat_nhan.csv", index=False, encoding="utf-8-sig")
    train_ml.init_dirs(str(destination))
    train_ml.ve_hinh(model, data["test"], threshold, pd.read_csv(results / "ket_qua_ml.csv"))
    version_path = destination / "version.json"
    version = json.loads(version_path.read_text(encoding="utf-8"))
    version["model_sha256"] = hashlib.sha256(model_path.read_bytes()).hexdigest()
    version["source_selection_script_sha256"] = hashlib.sha256((HERE / "select_complete.py").read_bytes()).hexdigest()
    version["score_decimals"] = 12
    version_path.write_text(json.dumps(version, ensure_ascii=False, indent=2), encoding="utf-8")
    # Confusion matrix dùng đúng quy ước làm tròn của bộ nạp.
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.metrics import confusion_matrix
    plt.figure(figsize=(5, 4))
    sns.heatmap(confusion_matrix(test.y_true, test.y_pred, labels=[0, 1]), annot=True, fmt="d", cmap="Blues",
                xticklabels=["ham", "spam"], yticklabels=["ham", "spam"])
    plt.xlabel("Predicted"); plt.ylabel("Actual"); plt.title("Exported model - test")
    plt.tight_layout(); plt.savefig(results / "figures/confusion_matrix.png", dpi=200); plt.close()
    print(language, "exported model", report["test_cuoi"], flush=True)


def run(language):
    destination = HERE / language
    destination.mkdir(exist_ok=True)
    command = [sys.executable, str(ORIGINAL / "train_ml.py"), "--out", str(destination)]
    if language == "vi":
        if not (TV1 / "manifest.json").exists():
            raise SystemExit("Chạy data_features/bo_sung_tv1/prepare_data.py trước.")
        command += ["--train", str(TV1 / "data/train_clean.csv"),
                    "--test", str(TV1 / "data/test_clean.csv"), "--regex_set", "vi", "--split", "group"]
    else:
        command += ["--raw", str(ORIGINAL / "tham_khao_UCI_tieng_Anh/data/raw/sms.tsv"),
                    "--regex_set", "en", "--split", "random"]
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    print(f"Training {language}; log: {destination / 'training.log'}", flush=True)
    with (destination / "training.log").open("w", encoding="utf-8") as log:
        subprocess.run(command, cwd=ORIGINAL, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    select(language)
    report = json.loads((destination / "results/ket_qua_cuoi.json").read_text(encoding="utf-8"))
    if language == "vi":
        for split in ("train", "val", "test"):
            if (destination / f"data/{split}.csv").read_bytes() != (TV1 / f"data/{split}.csv").read_bytes():
                raise RuntimeError(f"Split {split} không khớp bản TV1")
        dataset = json.loads((TV1 / "manifest.json").read_text(encoding="utf-8"))["dataset_id"]
    else:
        dataset = "uci-sms-seed42-original-random-split"
    version = {"language": language, "dataset_id": dataset,
               "model_sha256": hashlib.sha256((destination / "model/model.joblib").read_bytes()).hexdigest(),
               "source_train_script_sha256": hashlib.sha256((ORIGINAL / "train_ml.py").read_bytes()).hexdigest(),
               "normalization": "vi-redaction-v1" if language == "vi" else "none",
               "evaluation_note": "Kế thừa mã TV2 gốc: các thí nghiệm báo điểm test; không phải test mới hoàn toàn chưa dùng.",
               "packages": {p: importlib.metadata.version(p) for p in ("scikit-learn", "numpy", "pandas", "scipy", "joblib")}}
    (destination / "version.json").write_text(json.dumps(version, ensure_ascii=False, indent=2), encoding="utf-8")
    print(language, report["test_cuoi"], flush=True)
    finalize(language)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("vi", "uci", "both"), default="both")
    args = parser.parse_args()
    for language in (("vi", "uci") if args.language == "both" else (args.language,)):
        run(language)


if __name__ == "__main__":
    main()

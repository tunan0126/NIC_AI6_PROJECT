"""Chỉ đọc dữ liệu gốc; mọi đầu ra nằm trong thư mục bổ sung TV1."""
from pathlib import Path
import hashlib
import json
import sys

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedGroupKFold

from privacy import redact, remaining_identifiers, VERSION
from verify_source import attach_provenance

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ML = ROOT / "traditional_ml/TV2_hoc_may"
sys.path.insert(0, str(ML))
from train_ml import template_key
from features_regex import regex_features_vi, REGEX_COLS_VI


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = HERE / "data"
    reports = HERE / "reports"
    figures = reports / "figures"
    for p in (out, reports, figures):
        p.mkdir(parents=True, exist_ok=True)
    frames, sources, changed = [], [], {}
    for split, filename in (("train", "train_goc.csv"), ("test", "test_goc.csv")):
        path = ML / "data/raw" / filename
        raw = pd.read_csv(path, dtype=str, keep_default_na=False)
        if not {"message", "label"}.issubset(raw.columns):
            raise ValueError(f"Thiếu message/label: {path.name}")
        y = raw["label"].str.strip().str.lower().map({"0": 0, "1": 1, "ham": 0, "spam": 1})
        frame = pd.DataFrame({"source_id": [f"vi-{split}-{i:05d}" for i in range(len(raw))],
                              "source_split": split, "text": raw["message"].map(redact), "y": y})
        changed[split] = int((frame["text"] != raw["message"]).sum())
        sources.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                        "sha256": sha(path), "rows": len(raw),
                        "origin": "Có sẵn trong repo; chưa có hồ sơ chứng minh nguồn thu thập gốc."})
        frames.append(frame)
    all_data = pd.concat(frames, ignore_index=True)
    invalid = all_data[all_data["y"].isna() | all_data["text"].eq("")].copy()
    invalid["reason"] = "empty_text_or_invalid_label"
    valid = all_data.drop(invalid.index).copy()
    valid["y"] = valid["y"].astype(int)
    valid["template"] = valid["text"].map(template_key)
    # Cách xử lý bảo thủ: cách ly cả nhóm có nhãn trái nhau, không tự sửa nhãn.
    conflict_keys = set(valid.groupby("template")["y"].nunique().loc[lambda s: s > 1].index)
    quarantine = valid[valid["template"].isin(conflict_keys)].copy()
    quarantine["reason"] = "template_has_conflicting_labels_requires_owner_review"
    clean = valid[~valid["template"].isin(conflict_keys)].copy()
    train = clean[clean["source_split"] == "train"].drop_duplicates("text").copy()
    test = clean[clean["source_split"] == "test"].drop_duplicates("text").copy()
    overlap = set(train["text"]) & set(test["text"])
    train = train[~train["text"].isin(overlap)].copy()
    for name, frame in (("train_clean.csv", train), ("test_clean.csv", test)):
        frame[["source_id", "text", "y"]].to_csv(out / name, index=False)
    combined_review = pd.concat([invalid, quarantine], ignore_index=True)
    combined_review.to_csv(reports / "quarantine.csv", index=False, encoding="utf-8-sig")
    candidates = valid.groupby("template")["y"].nunique()
    assert set(quarantine["template"]) == set(candidates[candidates > 1].index)
    assert clean.groupby("template")["y"].nunique().max() == 1
    assert not any(all_data["text"].map(remaining_identifiers))

    # Tương thích cách chia group của mã TV2 gốc; không tạo cách chia mới cho TV3.
    train = train.reset_index(drop=True)
    test = test.reset_index(drop=True)
    i_train, i_val = next(StratifiedGroupKFold(8, shuffle=True, random_state=42).split(
        train, train["y"], train["text"].map(template_key)))
    splits = {"train": train.iloc[i_train], "val": train.iloc[i_val], "test": test}
    summary = {}
    for name, frame in splits.items():
        frame = frame.reset_index(drop=True).copy()
        frame.insert(0, "id", range(len(frame)))
        frame[["id", "text", "y"]].to_csv(out / f"{name}.csv", index=False)
        frame[["id", "source_id"]].to_csv(out / f"{name}_source_ids.csv", index=False)
        feat = pd.DataFrame(regex_features_vi(frame["text"]), columns=REGEX_COLS_VI)
        # Bảng riêng cho TV1 nhận ra cả thẻ đã che; không sửa bộ Regex TV2 cũ.
        feat["co_sdt"] = np.maximum(feat["co_sdt"], frame["text"].str.contains(r"\[PHONE\]").astype(int))
        feat.insert(0, "id", frame["id"])
        feat["y"] = frame["y"]
        feat.to_csv(out / f"{name}_regex_features.csv", index=False)
        summary[name] = {"rows": len(frame), "ham": int(frame["y"].eq(0).sum()),
                         "spam": int(frame["y"].eq(1).sum()),
                         "spam_ratio": round(float(frame["y"].mean()), 4)}
    seen = set(splits["train"]["text"].map(template_key))
    assert not seen.intersection(splits["val"]["text"].map(template_key))
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        assert not set(splits[a]["text"]) & set(splits[b]["text"])

    # Mẫu minh họa lấy từ dữ liệu sẵn có, KHÔNG gọi là tập kiểm thử độc lập mới.
    sample = pd.concat([test[test["y"] == 1].sample(min(150, int(test["y"].eq(1).sum())), random_state=42),
                        test[test["y"] == 0].sample(min(50, int(test["y"].eq(0).sum())), random_state=42)])
    sample[["source_id", "text", "y"]].to_csv(out / "vi_demo_sample.csv", index=False)
    quality = clean.assign(length=clean["text"].str.len()).groupby("y")["length"].describe()
    quality.to_csv(reports / "length_statistics.csv")
    counts = pd.DataFrame(summary).T
    counts.to_csv(reports / "split_statistics.csv")
    plt.figure(figsize=(6, 3.5))
    counts[["ham", "spam"]].plot.bar(ax=plt.gca(), color=["#4a7fb5", "#d9534f"])
    plt.title("Vietnamese supplementary dataset"); plt.ylabel("Messages"); plt.xticks(rotation=0)
    plt.tight_layout(); plt.savefig(figures / "class_distribution.png", dpi=160); plt.close()
    plt.figure(figsize=(6, 3.5))
    for label, name in ((0, "ham"), (1, "spam")):
        plt.hist(clean.loc[clean.y == label, "text"].str.len(), bins=35, alpha=.55, label=name)
    plt.title("Message lengths after redaction"); plt.xlabel("Characters"); plt.legend()
    plt.tight_layout(); plt.savefig(figures / "length_distribution.png", dpi=160); plt.close()

    files = {str(p.relative_to(HERE)).replace("\\", "/"): sha(p) for p in sorted(out.glob("*.csv"))}
    dataset_id = "vi-supplement-" + hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:12]
    manifest = {"dataset_id": dataset_id, "normalization": VERSION, "seed": 42,
                "sources": sources, "text_changed_rows": changed,
                "invalid_rows": len(invalid), "quarantined_rows": len(quarantine),
                "quarantined_template_groups": len(conflict_keys), "train_test_overlap_removed": len(overlap),
                "splits": summary, "files_sha256": files,
                "demo_sample": {"spam": int(sample.y.eq(1).sum()), "ham": int(sample.y.eq(0).sum()),
                                "independent_test": False},
                "source_validation": "Nguồn/đồng ý cung cấp và tên riêng tự do chưa thể xác minh từ repo.",
                "test_history": "Bộ test gốc đã được nhóm xem ở các thí nghiệm cũ; bản này không phải holdout mới chưa từng dùng."}
    manifest = attach_provenance(manifest)
    (HERE / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("files_sha256", "sources")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

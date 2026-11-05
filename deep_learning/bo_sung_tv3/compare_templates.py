"""Phân tích sau huấn luyện; không thay mô hình/ngưỡng đã chọn."""
from pathlib import Path
import sys
import re
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "traditional_ml/TV2_hoc_may"))
from evaluate import evaluate


def template_key(text):
    # Cùng quy ước TV2, không import script huấn luyện và thư viện imbalanced-learn.
    text = re.sub(r"\[[A-Za-z_]+\]", "[T]", text.lower())
    return re.sub(r"\s+", " ", re.sub(r"\d+", "0", text))[:50]


def main():
    combined = []
    for language in ("vi", "uci"):
        ml = ROOT / "traditional_ml/bo_sung_tv2" / language
        full = pd.concat([pd.read_csv(ml / f"data/{s}.csv") for s in ("train", "val")])
        keys = set(full.text.map(template_key))
        rows = []
        for name in ("ML_TV2", "lstm", "conv1d"):
            path = ml / "results/pred_ml_test.csv" if name == "ML_TV2" else HERE / language / f"results/pred_{name}_test.csv"
            predicted = pd.read_csv(path)
            seen = predicted.text.map(template_key).isin(keys)
            for group, mask in (("seen_in_train_or_val", seen), ("new_template", ~seen)):
                subset = predicted[mask]
                scores = subset.score if subset.y_true.nunique() == 2 else None
                rows.append({"language": language, "model": name, "group": group, "messages": len(subset),
                             **evaluate(subset.y_true, subset.y_pred, scores)})
        frame = pd.DataFrame(rows)
        frame.to_csv(HERE / language / "results/test_by_template.csv", index=False)
        combined.extend(rows)
    pd.DataFrame(combined).to_csv(HERE / "comparison_by_template.csv", index=False)


if __name__ == "__main__":
    main()

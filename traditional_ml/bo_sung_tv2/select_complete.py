"""Bước chọn bổ sung xét cả BoW/TF-IDF; không sửa train_ml.py của TV2."""
from pathlib import Path
import json
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import GridSearchCV, cross_validate
from sklearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE, RandomOverSampler
from imblearn.under_sampling import RandomUnderSampler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "traditional_ml/TV2_hoc_may"))
import train_ml as original
from features_regex import regex_features, regex_features_vi, REGEX_COLS, REGEX_COLS_VI
from evaluate import evaluate


def select(language):
    base = HERE / language
    data = {s: pd.read_csv(base / f"data/{s}.csv") for s in ("train", "val", "test")}
    train, val = data["train"], data["val"]
    original.SPLIT_MODE = "group" if language == "vi" else "random"
    original.REGEX_FN, original.REGEX_NAMES = (regex_features_vi, REGEX_COLS_VI) if language == "vi" else (regex_features, REGEX_COLS)
    samplers = {"none": None, "balanced": None,
                "oversample": RandomOverSampler, "smote": SMOTE, "undersample": RandomUnderSampler}

    def make(vector, name, method, regex):
        factory = samplers[method]
        sampler = factory(random_state=42) if factory else None
        return original.make_pipe(vector, name, sampler=sampler,
                                  cw="balanced" if method == "balanced" else None, regex=regex)

    def score(model):
        probabilities = model.predict_proba(val.text)[:, 1]
        return evaluate(val.y, (probabilities >= .5).astype(int), probabilities)

    rows = []
    for vector in ("BoW", "TFIDF"):
        for name in original.MODELS:
            methods = (["none"] if name == "NaiveBayes" else ["balanced"]) if vector == "BoW" else list(samplers)
            for method in methods:
                if name == "NaiveBayes" and method == "balanced":
                    continue
                pipe = make(vector, name, method, False).fit(train.text, train.y)
                rows.append({"Vector": vector, "Model": name, "Method": method, "Regex": False, **score(pipe)})
    for name in original.MODELS:
        method = "none" if name == "NaiveBayes" else "balanced"
        pipe = make("TFIDF", name, method, True).fit(train.text, train.y)
        rows.append({"Vector": "TFIDF", "Model": name, "Method": method, "Regex": True, **score(pipe)})
    ranking = pd.DataFrame(rows).sort_values(["F1", "Precision"], ascending=False, kind="stable").reset_index(drop=True)
    ranking.to_csv(base / "results/selection_all_candidates_val.csv", index=False)
    top = ranking.iloc[0]
    vector, name, method, regex = str(top.Vector), str(top.Model), str(top.Method), bool(top.Regex)
    def build():
        return make(vector, name, method, regex)
    cv, grouped = original.cv_obj(3)
    groups = {"groups": train.text.map(original.template_key)} if grouped else {}
    grid = {("vec__txt__" + k[5:] if regex and k.startswith("vec__") else k): v
            for k, v in original.GRID[name].items()}
    search = GridSearchCV(build(), grid, scoring="f1", cv=cv, n_jobs=1)
    search.fit(train.text, train.y, **groups)
    default = build().fit(train.text, train.y)
    baseline, tuned = score(default), score(search.best_estimator_)
    use_tuned = (tuned["F1"], tuned["Precision"]) >= (baseline["F1"], baseline["Precision"])
    best = search.best_estimator_ if use_tuned else default
    threshold, threshold_info = original.chinh_nguong(best, val)
    full = pd.concat([train, val], ignore_index=True)
    cv, grouped = original.cv_obj(5)
    scores = cross_validate(clone(best), full.text, full.y, cv=cv, scoring=["precision", "recall", "f1"], n_jobs=1,
                            **({"groups": full.text.map(original.template_key)} if grouped else {}))
    exported = Pipeline([(n, step) for n, step in best.steps if n != "samp"])
    joblib.dump(exported, base / "model/model.joblib")
    config = {"nguong": threshold, "nhan": {"0": "ham", "1": "spam"}, "input": "list[str]",
              "goi": "model.predict_proba(texts)[:,1] >= nguong -> spam"}
    (base / "model/config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path = base / "results/ket_qua_cuoi.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["cau_hinh_chon"] = {"model": name, "vector": vector, "dac_trung": vector + (" + Regex" if regex else ""),
                              "xu_ly_mat_can_bang": method, "best_params": search.best_params_,
                              "val_f1_mac_dinh": baseline["F1"], "val_f1_tinh_chinh": tuned["F1"],
                              "dung_ban_tinh_chinh": use_tuned}
    report["nguong"] = threshold_info
    report["cv5_train_val"] = {key: f"{scores['test_'+key].mean():.4f} ± {scores['test_'+key].std():.4f}"
                               for key in ("precision", "recall", "f1")}
    report["selection_scope"] = {"candidates": len(ranking), "includes_bow": True,
                                 "criterion": "validation F1, tie by Precision; tuning CV uses train only",
                                 "test_used_for_selection": False}
    # Đo test sau khi đã khóa lựa chọn; finalize sẽ đối chiếu chính file model đã xuất.
    probabilities = exported.predict_proba(data["test"].text)[:, 1]
    report["test_cuoi"] = evaluate(data["test"].y, (probabilities >= threshold).astype(int), probabilities)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (base / "results/training_report_before_export_check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(language, "selected over all", len(ranking), "candidates:", vector, name, method, "regex", regex, flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", choices=("vi", "uci", "both"), default="both")
    args = parser.parse_args()
    for language in (("vi", "uci") if args.language == "both" else (args.language,)):
        select(language)

"""Kiểm tra model/bộ từ vựng đã xuất và kết quả so sánh ML/DL."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import unittest
import zipfile

import numpy as np
import pandas as pd
from predict_dl import load_model, predict, tf
from text_processing import unicode_lower

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "traditional_ml/TV2_hoc_may"))
from evaluate import evaluate


class HandoffTests(unittest.TestCase):
    def test_vietnamese_case_is_normalized_after_reload(self):
        loaded = load_model("vi")
        _, vectorizer, _ = loaded
        for upper, lower in (("VAY TIỀN", "vay tiền"), ("ĐĂNG KÝ", "đăng ký"),
                             ("NHẬN QUÀ", "nhận quà")):
            tokens = vectorizer(tf.constant([upper, lower])).numpy()
            np.testing.assert_array_equal(tokens[0], tokens[1])
            left, right = predict(upper, loaded), predict(lower, loaded)
            self.assertEqual(left["label"], right["label"])
            self.assertAlmostEqual(left["score"], right["score"], places=7)

    def test_returned_score_agrees_with_label_at_threshold(self):
        threshold = .6148122549057007

        class FixedModel:
            def __init__(self, score):
                self.score = score

            def __call__(self, tokens, training=False):
                return tf.constant([[self.score]], dtype=tf.float64)

        config = {"language": "vi", "threshold": threshold, "model_sha256": "test",
                  "architecture": "conv1d", "dataset_id": "test"}
        for score in (threshold - 1e-8, threshold, threshold + 1e-8):
            result = predict("Tin thử", (FixedModel(score), lambda text: text, config))
            self.assertEqual(result["score"], score)
            self.assertEqual(result["label"], "spam" if result["score"] >= result["threshold"] else "ham")

    def test_group_reports_cover_the_same_test(self):
        for language in ("vi", "uci"):
            base = HERE / language
            groups = pd.read_csv(base / "results/test_by_template.csv")
            overall = pd.read_csv(base / "results/comparison_ml_dl.csv").set_index("model")
            size = len(pd.read_csv(ROOT / f"traditional_ml/bo_sung_tv2/{language}/data/test.csv"))
            for name, part in groups.groupby("model"):
                self.assertEqual(int(part.messages.sum()), size)
                for field in ("TN", "FP", "FN", "TP"):
                    self.assertEqual(int(part[field].sum()), int(overall.loc[name, field]))

    def test_models_preprocessing_metrics_and_selection(self):
        for language in ("vi", "uci"):
            base = HERE / language
            config = json.loads((base / "model_config.json").read_text(encoding="utf-8"))
            prep = json.loads((base / "preprocessing.json").read_text(encoding="utf-8"))
            source = ROOT / "traditional_ml/bo_sung_tv2" / language
            for split in ("train", "val", "test"):
                self.assertEqual(hashlib.sha256((source / f"data/{split}.csv").read_bytes()).hexdigest(),
                                 config["data_sha256"][split])
            train = pd.read_csv(source / "data/train.csv")
            # Chỉ các token có trong train mới có thể vào vocabulary.
            train_text = tf.constant(train.text.to_list())
            lowered = unicode_lower(train_text) if prep["standardize"] == "unicode_lower" else tf.strings.lower(train_text)
            train_tokens = set(tf.strings.split(lowered).flat_values.numpy())
            self.assertTrue(set(word.encode() for word in prep["vocabulary"][2:]) <= train_tokens)
            test = pd.read_csv(source / "data/test.csv")
            val = pd.read_csv(source / "data/val.csv")
            expected = max(config["candidates"], key=lambda name: (
                config["candidates"][name]["validation"]["F1"],
                config["candidates"][name]["validation"]["Precision"]))
            self.assertEqual(config["selected"], expected)
            for name in ("lstm", "conv1d"):
                with self.subTest(language=language, architecture=name):
                    loaded = load_model(language, name)
                    model, vectorizer, candidate = loaded
                    self.assertEqual(vectorizer.get_vocabulary(), prep["vocabulary"])
                    for split, data in (("test", test), ("val", val)):
                        tokens = vectorizer(tf.constant(data.text.to_list()))
                        scores = model(tokens, training=False).numpy().reshape(-1)
                        saved = pd.read_csv(base / f"results/pred_{name}_{split}.csv")
                        self.assertEqual(list(data.id), list(saved.id))
                        self.assertEqual(list(data.text), list(saved.text))
                        np.testing.assert_allclose(scores, saved.score, atol=2e-6, rtol=0)
                        pred = (scores >= candidate["threshold"]).astype(int)
                        np.testing.assert_array_equal(pred, saved.y_pred)
                        if split == "test":
                            report = json.loads((base / "results/summary.json").read_text(encoding="utf-8"))
                            self.assertEqual(evaluate(data.y, pred, scores), report["models"][name]["test"])
                    result = predict("Ma OTP la 123456", loaded)
                    self.assertIn(result["label"], ("ham", "spam"))
                    self.assertEqual(result["architecture"], name)
                    for invalid in ("", "   ", None):
                        with self.assertRaises(ValueError):
                            predict(invalid, loaded)
            selected_predictions = (base / "results/pred_dl_test.csv").read_bytes()
            self.assertEqual(selected_predictions, (base / f"results/pred_{expected}_test.csv").read_bytes())

    def test_other_members_files_unchanged(self):
        result = subprocess.run(["git", "diff", "--exit-code", "HEAD", "--"], cwd=ROOT, capture_output=True)
        self.assertEqual(result.returncode, 0)
        old_package = ROOT.parent / "output/packages/Bo_sung_TV1_TV2.zip"
        if old_package.exists():
            with zipfile.ZipFile(old_package) as package:
                for entry in package.infolist():
                    self.assertEqual((ROOT / entry.filename).read_bytes(), package.read(entry.filename), entry.filename)


if __name__ == "__main__":
    unittest.main(verbosity=2)

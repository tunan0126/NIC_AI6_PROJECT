"""Kiểm tra bàn giao: dữ liệu, metric, suy luận và bảo toàn file nguồn."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import unittest

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TV1 = ROOT / "data_features/bo_sung_tv1"
sys.path.insert(0, str(TV1))
sys.path.insert(0, str(ROOT / "traditional_ml/TV2_hoc_may"))
from privacy import redact, remaining_identifiers
from train_ml import template_key
from evaluate import evaluate
from predict import load_model, predict


class HandoffTests(unittest.TestCase):
    def test_published_source_and_curated_sample(self):
        report = json.loads((TV1 / "reports/source_verification.json").read_text(encoding="utf-8"))
        for item in report["verified_files"]:
            local = (ROOT / item["local_file"]).read_bytes()
            self.assertEqual(hashlib.sha256(local).hexdigest(), item["local_sha256"])
            self.assertEqual(hashlib.sha256(local.replace(b"\r\n", b"\n")).hexdigest(), item["upstream_sha256"])
        path = TV1 / "reports" / report["sample"]["path"]
        sample = pd.read_csv(path)
        self.assertEqual(int(sample.y.eq(1).sum()), 150)
        self.assertEqual(int(sample.y.eq(0).sum()), 50)
        self.assertTrue(sample.source_id.is_unique)
        self.assertFalse(sample.text.map(remaining_identifiers).any())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), report["sample"]["sha256"])

    def test_selection_includes_bow_and_tfidf(self):
        for language in ("vi", "uci"):
            base = HERE / language
            ranking = pd.read_csv(base / "results/selection_all_candidates_val.csv")
            self.assertEqual(len(ranking), 27)
            self.assertEqual(set(ranking.Vector), {"BoW", "TFIDF"})
            report = json.loads((base / "results/ket_qua_cuoi.json").read_text(encoding="utf-8"))
            best = ranking.sort_values(["F1", "Precision"], ascending=False, kind="stable").iloc[0]
            self.assertEqual(report["cau_hinh_chon"]["vector"], best.Vector)
            self.assertEqual(report["cau_hinh_chon"]["model"], best.Model)
            self.assertFalse(report["selection_scope"]["test_used_for_selection"])

    def test_redaction_and_preserved_signals(self):
        text = "OTP 123456; gọi 0912345678; user@example.com; NHẬN QUÀ!!!"
        clean = redact(text)
        self.assertNotIn("123456", clean)
        self.assertNotIn("0912345678", clean)
        self.assertNotIn("user@example.com", clean)
        self.assertIn("NHẬN QUÀ!!!", clean)
        self.assertEqual(redact(clean), clean)
        self.assertFalse(remaining_identifiers(clean))
        with self.assertRaises(TypeError):
            redact(None)

    def test_data_fingerprint_and_splits(self):
        manifest = json.loads((TV1 / "manifest.json").read_text(encoding="utf-8"))
        for relative, expected in manifest["files_sha256"].items():
            self.assertEqual(hashlib.sha256((TV1 / relative).read_bytes()).hexdigest(), expected)
        for source in manifest["sources"]:
            self.assertEqual(hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest(), source["sha256"])
        data = {name: pd.read_csv(TV1 / f"data/{name}.csv") for name in ("train", "val", "test")}
        for name, frame in data.items():
            self.assertTrue(frame.id.is_unique)
            self.assertFalse(frame.text.map(remaining_identifiers).any())
            self.assertEqual(set(frame.y), {0, 1})
            pd.testing.assert_frame_equal(frame, pd.read_csv(HERE / f"vi/data/{name}.csv"))
        for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
            self.assertFalse(set(data[a].text) & set(data[b].text))
        self.assertFalse(set(data["train"].text.map(template_key)) & set(data["val"].text.map(template_key)))
        review = pd.read_csv(TV1 / "reports/quarantine.csv")
        clean_keys = set(pd.concat(list(data.values())).text.map(template_key))
        self.assertFalse(set(review.template) & clean_keys)

    def test_exported_models_reproduce_saved_predictions(self):
        for language in ("vi", "uci"):
            with self.subTest(language=language):
                model, threshold, version = load_model(language)
                test = pd.read_csv(HERE / f"{language}/data/test.csv")
                saved = pd.read_csv(HERE / f"{language}/results/pred_ml_test.csv")
                self.assertEqual(list(test.id), list(saved.id))
                self.assertEqual(list(test.y), list(saved.y_true))
                self.assertEqual(list(test.text), list(saved.text))
                scores = np.round(model.predict_proba(test.text)[:, list(model.classes_).index(1)], 12)
                np.testing.assert_allclose(scores, saved.score, atol=1e-12, rtol=0)
                np.testing.assert_array_equal(scores >= threshold, saved.y_pred)
                report = json.loads((HERE / f"{language}/results/ket_qua_cuoi.json").read_text(encoding="utf-8"))
                result = evaluate(test.y, (scores >= threshold).astype(int), scores)
                self.assertEqual(result, report["test_cuoi"])
                sample = predict("Ma OTP la 123456", (model, threshold, version))
                self.assertIn(sample["label"], ("ham", "spam"))
                with self.assertRaises(ValueError):
                    predict("  ", (model, threshold, version))

    def test_original_tracked_files_unchanged(self):
        result = subprocess.run(["git", "diff", "--exit-code", "HEAD", "--"], cwd=ROOT,
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)

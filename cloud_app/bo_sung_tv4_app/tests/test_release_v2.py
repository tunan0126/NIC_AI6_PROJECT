"""Integrity/reproducibility checks; quality scores remain evaluation results."""
import csv, hashlib, importlib.util, json, sys, unittest, unicodedata
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'data_features/bo_sung_tv1_v2'
ML=ROOT/'traditional_ml/bo_sung_tv2_v2'
sys.path.insert(0,str(DATA))
from vi_text_v2 import normalize
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from model_service import ModelService


def read(path):
    with path.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))


class ReleaseTests(unittest.TestCase):
    def test_data_and_inherited_input_hashes(self):
        manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
        for name,digest in manifest['files_sha256'].items():
            self.assertEqual(hashlib.sha256((DATA/'data'/name).read_bytes()).hexdigest(),digest,name)
        for name,digest in manifest['input_hashes'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)

    def test_no_normalized_overlap_with_train_or_validation(self):
        sets={s:{r['input_key'] for r in read(DATA/f'data/{s}.csv')} for s in ('train','val','test','challenge','regression')}
        self.assertFalse(sets['train'] & sets['val'])
        for protected in ('test','challenge','regression'):
            self.assertFalse(sets['train'] & sets[protected],protected)
            self.assertFalse(sets['val'] & sets[protected],protected)

    def test_fixed_benchmark_text_and_labels_unchanged(self):
        original=read(ROOT/'traditional_ml/bo_sung_tv2/vi/data/test.csv')
        current=read(DATA/'data/test.csv')
        self.assertEqual([(r['text'],r['y']) for r in original],[(r['text'],r['y']) for r in current])

    def test_normalization_contract_for_every_input(self):
        for split in ('train','val','test','challenge','regression'):
            for row in read(DATA/f'data/{split}.csv'):
                value=normalize(row['text'])
                self.assertEqual(value,row['input_key'])
                self.assertEqual(normalize(value),value)
                self.assertEqual(normalize(unicodedata.normalize('NFD',row['text'])),value)

    def test_regex_exports_align_with_labels(self):
        for split in ('train','val','test','challenge','regression'):
            rows=read(DATA/f'data/{split}.csv');features=read(DATA/f'data/{split}_regex.csv')
            self.assertEqual([(r['id'],r['y']) for r in rows],[(r['id'],r['y']) for r in features])
            self.assertGreaterEqual(len(features[0]),14)

    def test_ml_release_selection_gates_and_artifact(self):
        service=ModelService();model,threshold,version=service.load('ml','vi')
        report=json.loads((ML/'report.json').read_text(encoding='utf-8'))
        selected=report['selected'];self.assertTrue(selected['eligible'])
        self.assertEqual(selected['legacy_regression_release_errors'],0)
        self.assertGreaterEqual(selected['validation_source']['Precision'],.90)
        self.assertGreaterEqual(selected['validation_source']['Recall'],.95)
        self.assertGreaterEqual(selected['validation_authored']['Precision'],.90)
        self.assertGreaterEqual(selected['validation_authored']['Recall'],.90)
        self.assertEqual(version['dataset_id'],json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))['dataset_id'])

    def test_ml_saved_predictions_reproduce_and_accent_views_match(self):
        service=ModelService();model,threshold,_=service.load('ml','vi')
        for split in ('test','challenge','regression'):
            rows=read(DATA/f'data/{split}.csv');saved=read(ML/f'pred_{split}.csv')
            scores=np.round(model.predict_proba([r['text'] for r in rows])[:,1],12)
            folded=np.round(model.predict_proba([r['input_key'] for r in rows])[:,1],12)
            np.testing.assert_array_equal(scores,folded)
            np.testing.assert_allclose(scores,[float(r['score']) for r in saved],atol=1e-11,rtol=0)
            self.assertEqual((scores>=threshold).astype(int).tolist(),[int(r['y_pred']) for r in saved])

    def test_reported_message_and_no_accent_ml_pair(self):
        service=ModelService();text='Nhóm sẽ họp lúc 14:00 để chuẩn bị bài thuyết trình.'
        native=service.predict(text,'ml','vi');folded=service.predict(normalize(text),'ml','vi')
        self.assertEqual(native['label'],'ham')
        self.assertEqual(native['score'],folded['score'])
        self.assertEqual(native['model_origin'],'tv1_4_v2')

    def test_bad_release_hash_fails_without_silent_fallback(self):
        service=ModelService();service.v2['ml']['config_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Config v2'):service.load('ml','vi')
        service=ModelService()
        service.v2['ml']['runtime_hashes']['data_features/bo_sung_tv1/privacy.py']='0'*64
        with self.assertRaisesRegex(ValueError,'phụ thuộc v2'):service.load('ml','vi')

    def test_unreleased_dl_and_english_keep_their_versions(self):
        service=ModelService();specs={(r['model'],r['language']):r for r in service.describe()}
        self.assertEqual(specs['ml','vi']['model_origin'],'tv1_4_v2')
        self.assertEqual(specs['dl','vi']['model_origin'],'tv4_vi_revision')
        active=json.loads((ROOT/'cloud_app/bo_sung_tv4_app/vi_model_revision/active.json').read_text(encoding='utf-8'))
        config=json.loads((ROOT/'cloud_app/bo_sung_tv4_app/vi_model_revision/dl/model_config.json').read_text(encoding='utf-8'))
        self.assertEqual(specs['dl','vi']['model_version'],config['candidates'][config['selected']]['model_sha256'][:12])
        self.assertEqual(specs['ml','uci']['model_origin'],'tv2')
        self.assertEqual(specs['dl','uci']['model_origin'],'tv3')


if __name__=='__main__':unittest.main(verbosity=2)

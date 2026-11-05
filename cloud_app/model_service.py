"""ModelService: Nạp và suy luận 4 nhánh mô hình AI (ML & DL, tiếng Việt & tiếng Anh)."""
import os
from pathlib import Path
import sys
import threading

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
os.environ.setdefault('TF_NUM_INTRAOP_THREADS', '2')
os.environ.setdefault('TF_NUM_INTEROP_THREADS', '1')

ROOT = Path(__file__).resolve().parent.parent

# Thêm đường dẫn các thành phần vào sys.path
sys.path.insert(0, str(ROOT / 'traditional_ml'))
sys.path.insert(0, str(ROOT / 'deep_learning'))
sys.path.insert(0, str(ROOT / 'data_features'))

import predict as ml_module
import predict_dl as dl_module

try:
    from privacy import redact
except ImportError:
    redact = lambda s: s


class ModelService:
    def __init__(self):
        self.cache = {}
        self.lock = threading.RLock()

    def load(self, model, language):
        with self.lock:
            key = (model, language)
            if key not in self.cache:
                if model == 'ml':
                    self.cache[key] = ml_module.load_model(language)
                elif model == 'dl':
                    self.cache[key] = dl_module.load_model(language)
                else:
                    raise ValueError(f"Model không hợp lệ: {model}")
            return self.cache[key]

    def predict(self, text, model, language):
        with self.lock:
            loaded = self.load(model, language)
            if model == 'ml':
                res = ml_module.predict(text, loaded)
                res.update(model=model, truncated=False, input_tokens=None, sequence_length=None)
                return res
            elif model == 'dl':
                res = dl_module.predict(text, loaded)
                res.update(model=model, truncated=False, input_tokens=None, sequence_length=None)
                return res

    def warmup(self):
        for language in ('vi', 'uci'):
            for model in ('ml', 'dl'):
                self.predict('Tin mẫu khởi động.' if language == 'vi' else 'Startup message.', model, language)

    def describe(self):
        rows = []
        for language in ('vi', 'uci'):
            # ML info
            try:
                loaded_ml = self.load('ml', language)
                version_ml = loaded_ml[2]
                rows.append({
                    'model': 'ml',
                    'language': language,
                    'architecture': version_ml.get('architecture', 'LinearSVC+TF-IDF'),
                    'representation': version_ml.get('representation', 'TF-IDF (Word & Char)'),
                    'model_version': version_ml.get('model_sha256', 'default')[:12],
                    'threshold': loaded_ml[1],
                    'dataset_id': version_ml.get('dataset_id', 'unknown'),
                    'model_origin': 'tv2'
                })
            except Exception:
                pass
            
            # DL info
            try:
                loaded_dl = self.load('dl', language)
                config_dl = loaded_dl[2]
                rows.append({
                    'model': 'dl',
                    'language': language,
                    'architecture': config_dl.get('architecture', 'Conv1D/LSTM'),
                    'model_origin': 'tv3',
                    'model_version': config_dl.get('model_sha256', 'default')[:12],
                    'threshold': config_dl.get('threshold', 0.5),
                    'dataset_id': config_dl.get('dataset_id', 'unknown')
                })
            except Exception:
                pass
        return rows

import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS','0')
from pathlib import Path
import hashlib,json,sys
import tensorflow as tf
from tensorflow import keras
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'data_features/bo_sung_tv1_v2'))
from vi_text_v2 import normalize


def load_model(language='vi'):
    if language!='vi':raise ValueError('Gói này chỉ cho tiếng Việt')
    config=json.loads((HERE/'model_config.json').read_text(encoding='utf-8'))
    if hashlib.sha256((HERE/'preprocessing.json').read_bytes()).hexdigest()!=config['preprocessing_sha256']:raise ValueError('Hash preprocessing DL v2 không khớp')
    if hashlib.sha256((ROOT/'data_features/bo_sung_tv1_v2/vi_text_v2.py').read_bytes()).hexdigest()!=config['normalizer_sha256']:raise ValueError('Normalizer v2 đã thay đổi')
    prep=json.loads((HERE/'preprocessing.json').read_text(encoding='utf-8'))
    entry=config['candidates'][config['selected']]
    path=HERE/entry['model_file']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=entry['model_sha256']:raise ValueError('Model DL v2 không khớp hash')
    vec=keras.layers.TextVectorization(max_tokens=prep['max_tokens'],standardize=None,split=prep.get('split','whitespace'),output_mode='int',output_sequence_length=prep['sequence_length'],vocabulary=prep['vocabulary'])
    return keras.models.load_model(path,compile=False),vec,{**entry,'dataset_id':config['dataset_id'],'language':'vi','model_origin':'tv1_4_v2'}


def predict(text,loaded):
    if not isinstance(text,str) or not text.strip():raise ValueError('Nội dung không được trống')
    model,vec,config=loaded
    score=float(model(vec(tf.constant([normalize(text)])),training=False).numpy()[0,0])
    return dict(label='spam' if score>=config['threshold'] else 'ham',score=score,threshold=config['threshold'],
                model_version=config['model_sha256'][:12],architecture=config['architecture'],dataset_id=config['dataset_id'],language='vi',model_origin='tv1_4_v2')

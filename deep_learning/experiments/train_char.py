"""Conv1D ký tự; chọn bằng validation, không dùng challenge để điều chỉnh."""
import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2');os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS','0')
os.environ.setdefault('TF_NUM_INTRAOP_THREADS','2');os.environ.setdefault('TF_NUM_INTEROP_THREADS','1')
from pathlib import Path
import importlib.util,json,sys
import numpy as np,pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.utils.class_weight import compute_class_weight
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DATA=ROOT/'data_features/bo_sung_tv1_v2'
sys.path.insert(0,str(DATA));from vi_text_v2 import VERSION
spec=importlib.util.spec_from_file_location('ml_common_v2',ROOT/'traditional_ml/bo_sung_tv2_v2/train.py');common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)


def ds(x,y=None,w=None,train=False):
    value=x if y is None else (x,y,w)
    d=tf.data.Dataset.from_tensor_slices(value)
    if train:d=d.shuffle(len(x),seed=42,reshuffle_each_iteration=True)
    opt=tf.data.Options();opt.threading.private_threadpool_size=2
    return d.batch(32).with_options(opt).prefetch(1)


def main():
    tr=pd.read_csv(DATA/'data/train.csv');va=pd.read_csv(DATA/'data/val.csv')
    keras.utils.set_random_seed(42);tf.config.experimental.enable_op_determinism()
    length=int(np.clip(np.ceil(np.percentile(tr.input_key.str.len(),95)),128,768))
    vec=keras.layers.TextVectorization(max_tokens=512,standardize=None,split='character',output_mode='int',output_sequence_length=length)
    vec.adapt(ds(tf.constant(tr.input_key.to_list())))
    vocabulary=vec.get_vocabulary();x=vec(tf.constant(tr.input_key.to_list())).numpy();vx=vec(tf.constant(va.input_key.to_list())).numpy()
    y=tr.y.to_numpy(dtype=np.int32);vy=va.y.to_numpy(dtype=np.int32)
    cw=compute_class_weight('balanced',classes=np.array([0,1]),y=y);weights=cw[y]*np.where(tr.source.eq('published-corpus'),1.,3.)
    original=va.source.eq('published-corpus').to_numpy();vw=np.where(original,1.,sum(original)/sum(~original))
    model=keras.Sequential([keras.layers.Input(shape=(length,),dtype='int64'),keras.layers.Embedding(len(vocabulary),32),
        keras.layers.Conv1D(64,5,activation='relu'),keras.layers.MaxPooling1D(2),keras.layers.Conv1D(64,5,activation='relu'),
        keras.layers.GlobalMaxPooling1D(),keras.layers.Dense(32,activation='relu'),keras.layers.Dropout(.3),keras.layers.Dense(1,activation='sigmoid')],name='conv1d_char')
    model.compile(optimizer=keras.optimizers.Adam(.001),loss='binary_crossentropy',metrics=['accuracy'])
    stop=keras.callbacks.EarlyStopping(monitor='val_loss',patience=5,min_delta=.001,restore_best_weights=True)
    history=model.fit(ds(x,y,weights,True),validation_data=ds(vx,vy,vw),epochs=24,callbacks=[stop],verbose=2)
    path=HERE/'models/conv1d_char_42.keras';model.save(path)
    model=keras.models.load_model(path,compile=False);scores=model(vx,training=False).numpy().reshape(-1)
    threshold,rank=common.choose_threshold(va,scores)
    entry=dict(architecture='conv1d',representation='character',seed=42,threshold=threshold,model_file='models/conv1d_char_42.keras',model_sha256=common.sha(path),eligible=rank[0],
        validation_source=common.measure(vy[original],scores[original],threshold),validation_authored=common.measure(vy[~original],scores[~original],threshold),epochs_run=len(history.history['loss']),restored_epoch=int(stop.best_epoch)+1)
    pd.DataFrame(history.history).to_csv(HERE/'history_conv1d_char_42.csv',index=False)
    (HERE/'char_candidate.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8');print('CANDIDATE',json.dumps(entry,ensure_ascii=False),flush=True)
    if not entry['eligible']:raise RuntimeError('Character Conv1D does not meet validation gates; do not deploy')
    prep=dict(max_tokens=512,sequence_length=length,vocabulary=vocabulary,normalization=VERSION,split='character')
    previous=HERE/'preprocessing.json'
    if previous.exists():previous.replace(HERE/'preprocessing_word.json')
    previous.write_text(json.dumps(prep,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
    config=dict(selected='conv1d_char_42',candidates={'conv1d_char_42':entry},dataset_id=manifest['dataset_id'],dataset_manifest_sha256=common.sha(DATA/'manifest.json'),
        normalizer_sha256=common.sha(DATA/'vi_text_v2.py'),normalization=VERSION,preprocessing_sha256=common.sha(previous),language='vi',source_script_sha256=common.sha(Path(__file__)),
        selection='Word LSTM/Conv1D attempts failed fixed validation gates; character Conv1D passed same gates. Challenge/regression/test excluded from selection.')
    (HERE/'model_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    results={}
    for split in ('test','challenge','regression'):
        f=pd.read_csv(DATA/f'data/{split}.csv');sx=vec(tf.constant(f.input_key.to_list())).numpy();scores=model(sx,training=False).numpy().reshape(-1)
        results[split]=common.measure(f.y,scores,threshold)
        pd.DataFrame(dict(id=f.id,text=f.text,y_true=f.y,score=scores,y_pred=(scores>=threshold).astype(int))).to_csv(HERE/f'pred_{split}.csv',index=False)
    report=dict(selected='conv1d_char_42',validation=entry,results=results,provenance='Inherited benchmark and assistant-authored challenge. No new human-labelled real-world SMS holdout.')
    (HERE/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()

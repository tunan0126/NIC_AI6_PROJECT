"""LSTM/Conv1D TV4 với phần phủ ngữ cảnh bổ sung; không sửa gói TV3."""
import os
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS','0')
os.environ.setdefault('TF_NUM_INTRAOP_THREADS','2')
os.environ.setdefault('TF_NUM_INTEROP_THREADS','1')
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.utils.class_weight import compute_class_weight
from train_revision import HERE, ROOT, BASE, sha, metrics
sys.path.insert(0,str(ROOT/'deep_learning/bo_sung_tv3'))
from text_processing import unicode_lower
sys.path.insert(0,str(ROOT/'data_features/bo_sung_tv1'))
from privacy import redact


def ds(x,y=None,weights=None,shuffle=False):
    value=x if y is None else (x,y) if weights is None else (x,y,weights)
    result=tf.data.Dataset.from_tensor_slices(value)
    if shuffle:result=result.shuffle(len(x),seed=42,reshuffle_each_iteration=True)
    options=tf.data.Options();options.threading.private_threadpool_size=2
    return result.batch(32).with_options(options).prefetch(1)


def build(name,vocab,length):
    layers=[keras.layers.Input(shape=(length,),dtype='int64'),keras.layers.Embedding(vocab,64,mask_zero=name=='lstm')]
    if name=='lstm':layers += [keras.layers.LSTM(32)]
    else:layers += [keras.layers.Conv1D(64,5,activation='relu'),keras.layers.MaxPooling1D(2),keras.layers.GlobalMaxPooling1D(),keras.layers.Dense(32,activation='relu')]
    layers += [keras.layers.Dropout(.3),keras.layers.Dense(1,activation='sigmoid')]
    model=keras.Sequential(layers,name=name)
    model.compile(optimizer=keras.optimizers.Adam(.001),loss='binary_crossentropy',metrics=['accuracy'])
    return model


def main():
    out=HERE/'dl';(out/'models').mkdir(exist_ok=True,parents=True)
    source=pd.read_csv(BASE/'data/train.csv');extra=pd.read_csv(HERE/'data/train_authored.csv');extra.text=extra.text.map(redact)
    train=pd.concat([source,extra],ignore_index=True)
    old_val=pd.read_csv(BASE/'data/val.csv');new_val=pd.read_csv(HERE/'data/validation_authored.csv');new_val.text=new_val.text.map(redact)
    val=pd.concat([old_val,new_val],ignore_index=True)
    regression=json.loads((HERE.parent/'tests/vi_semantic_cases.json').read_text(encoding='utf-8'))
    assert not {redact(r['text']).casefold() for r in regression} & set(pd.concat([train,val]).text.str.casefold())
    keras.utils.set_random_seed(42);tf.config.experimental.enable_op_determinism()
    length=int(np.clip(np.ceil(np.percentile(train.text.str.split().str.len(),95)),24,160))
    vec=keras.layers.TextVectorization(max_tokens=12000,standardize=unicode_lower,split='whitespace',output_mode='int',output_sequence_length=length)
    vec.adapt(ds(tf.constant(train.text.to_list())))
    vocabulary=vec.get_vocabulary()
    prep=dict(standardize='unicode_lower',split='whitespace',max_tokens=12000,sequence_length=length,vocabulary=vocabulary)
    (out/'preprocessing.json').write_text(json.dumps(prep,ensure_ascii=False,indent=2),encoding='utf-8')
    x=vec(tf.constant(train.text.to_list())).numpy();y=train.y.to_numpy(dtype=np.int32)
    vx=vec(tf.constant(val.text.to_list())).numpy();vy=val.y.to_numpy(dtype=np.int32)
    cw=compute_class_weight('balanced',classes=np.array([0,1]),y=y)
    weights=cw[y]*np.r_[np.ones(len(source)),np.full(len(extra),6.)]
    val_weights=np.r_[np.ones(len(old_val)),np.full(len(new_val),len(old_val)/len(new_val))]
    configs={};ranks={}
    for name in ('lstm','conv1d'):
        keras.backend.clear_session();keras.utils.set_random_seed(42)
        model=build(name,len(vocabulary),length)
        stop=keras.callbacks.EarlyStopping(monitor='val_loss',patience=3,min_delta=.001,restore_best_weights=True)
        history=model.fit(ds(x,y,weights,shuffle=True),validation_data=ds(vx,vy,val_weights),epochs=18,callbacks=[stop],verbose=2)
        path=out/'models'/f'{name}.keras';model.save(path)
        loaded=keras.models.load_model(path,compile=False)
        scores=loaded(vx,training=False).numpy().reshape(-1)
        best=None;best_rank=None
        for threshold in np.unique(np.r_[scores,.5]):
            a=metrics(old_val.y,scores[:len(old_val)],threshold);b=metrics(new_val.y,scores[len(old_val):],threshold)
            eligible=a['Recall']>=.98 and a['Precision']>=.90 and b['Recall']>=.95
            rank=(eligible,min(a['F1'],b['F1']),(a['F1']+b['F1'])/2,min(a['Precision'],b['Precision']))
            if best_rank is None or rank>best_rank:best_rank=rank;best=(float(threshold),a,b)
        threshold,a,b=best;ranks[name]=best_rank
        configs[name]=dict(architecture=name,threshold=threshold,model_file=f'models/{name}.keras',model_sha256=sha(path),
                           original_validation=a,authored_validation=b,eligible=bool(best_rank[0]),epochs_run=len(history.history['loss']),restored_epoch=int(stop.best_epoch)+1)
        pd.DataFrame(history.history).to_csv(out/f'history_{name}.csv',index=False)
        print('CANDIDATE',name,json.dumps(configs[name],ensure_ascii=False),flush=True)
    chosen=max(configs,key=lambda name:ranks[name])
    assert configs[chosen]['eligible'],'No eligible DL model; do not deploy'
    ml_version=json.loads((HERE/'version.json').read_text(encoding='utf-8'))
    config=dict(selected=chosen,candidates=configs,dataset_id=ml_version['dataset_id'],language='vi',
                preprocessing_sha256=sha(out/'preprocessing.json'),model_origin='tv4_vi_revision',
                selection_criterion='Same two-context validation criterion as ML revision; no regression/test used for fit or selection',
                source_inputs_sha256=ml_version['inputs_sha256'],authored_weight=6,seed=42,source_script_sha256=sha(Path(__file__)))
    (out/'model_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    # Đã khóa lựa chọn; chỉ báo cáo từ đây.
    test=pd.read_csv(BASE/'data/test.csv')
    tx=vec(tf.constant(test.text.to_list())).numpy()
    rx=vec(tf.constant([redact(r['text']) for r in regression])).numpy()
    ry=np.array([int(r['label']=='spam') for r in regression])
    reports={}
    for name,entry in configs.items():
        loaded=keras.models.load_model(out/entry['model_file'],compile=False)
        scores=loaded(tx,training=False).numpy().reshape(-1)
        reg=loaded(rx,training=False).numpy().reshape(-1)
        reports[name]=dict(source_test=metrics(test.y,scores,entry['threshold']),regression_development=metrics(ry,reg,entry['threshold']))
        pd.DataFrame({'text':[r['text'] for r in regression],'expected':ry,'score':reg,'pred':(reg>=entry['threshold']).astype(int)}).to_csv(out/f'regression_{name}.csv',index=False)
    report=dict(selected=chosen,models=reports,validation=configs,source_train=len(source),authored_train=len(extra),
                authored_validation=len(new_val),provenance='Authored development coverage, not independently collected SMS. Inherited benchmark already seen; report separately from original TV3.')
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()

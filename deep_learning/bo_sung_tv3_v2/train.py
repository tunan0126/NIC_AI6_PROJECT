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
sys.path.insert(0,str(DATA));from vi_text_v2 import normalize,VERSION
spec=importlib.util.spec_from_file_location('tv2_v2_train',ROOT/'traditional_ml/bo_sung_tv2_v2/train.py')
common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)


def dataset(x,y=None,w=None,train=False):
    value=x if y is None else (x,y) if w is None else (x,y,w)
    ds=tf.data.Dataset.from_tensor_slices(value)
    if train:ds=ds.shuffle(len(x),seed=42,reshuffle_each_iteration=True)
    options=tf.data.Options();options.threading.private_threadpool_size=2
    return ds.batch(32).with_options(options).prefetch(1)


def build(name,vocab,length):
    layers=[keras.layers.Input(shape=(length,),dtype='int64'),keras.layers.Embedding(vocab,64,mask_zero=name=='lstm')]
    if name=='lstm':layers += [keras.layers.LSTM(32)]
    else:layers += [keras.layers.Conv1D(64,5,activation='relu'),keras.layers.MaxPooling1D(2),keras.layers.GlobalMaxPooling1D(),keras.layers.Dense(32,activation='relu')]
    layers += [keras.layers.Dropout(.3),keras.layers.Dense(1,activation='sigmoid')]
    model=keras.Sequential(layers,name=name);model.compile(optimizer=keras.optimizers.Adam(.0003),loss='binary_crossentropy',metrics=['accuracy'])
    return model


def main():
    (HERE/'models').mkdir(exist_ok=True)
    frames={s:pd.read_csv(DATA/f'data/{s}.csv') for s in ('train','val')};tr,va=frames['train'],frames['val']
    lengths=tr.input_key.str.split().str.len();length=int(np.clip(np.ceil(np.percentile(lengths,95)),24,160))
    keras.utils.set_random_seed(42);tf.config.experimental.enable_op_determinism()
    vec=keras.layers.TextVectorization(max_tokens=12000,standardize=None,split='whitespace',output_mode='int',output_sequence_length=length)
    vec.adapt(dataset(tf.constant(tr.input_key.to_list())))
    vocabulary=vec.get_vocabulary();prep=dict(max_tokens=12000,sequence_length=length,vocabulary=vocabulary,normalization=VERSION)
    (HERE/'preprocessing.json').write_text(json.dumps(prep,ensure_ascii=False,indent=2),encoding='utf-8')
    x=vec(tf.constant(tr.input_key.to_list())).numpy();y=tr.y.to_numpy(dtype=np.int32)
    vx=vec(tf.constant(va.input_key.to_list())).numpy();vy=va.y.to_numpy(dtype=np.int32)
    cw=compute_class_weight('balanced',classes=np.array([0,1]),y=y)
    weights=cw[y]*np.where(tr.source.eq('published-corpus'),1.,3.)
    original=va.source.eq('published-corpus').to_numpy();valweights=np.where(original,1.,sum(original)/sum(~original))
    configs={};ranks={}
    for seed in (42,2026):
        for architecture in ('lstm','conv1d'):
            key=f'{architecture}_{seed}';keras.backend.clear_session();keras.utils.set_random_seed(seed)
            model=build(architecture,len(vocabulary),length)
            previous=ROOT/'cloud_app/bo_sung_tv4_app/vi_model_revision/dl'
            old_model=keras.models.load_model(previous/'models'/f'{architecture}.keras',compile=False)
            old_vocabulary=json.loads((previous/'preprocessing.json').read_text(encoding='utf-8'))['vocabulary']
            embedding=model.layers[0].get_weights()[0];old_embedding=old_model.layers[0].get_weights()[0]
            ids={word:i for i,word in enumerate(vocabulary)};buckets={}
            for i,word in enumerate(old_vocabulary[2:],2):
                key_word=normalize(word)
                if key_word in ids:buckets.setdefault(ids[key_word],[]).append(old_embedding[i])
            embedding[:2]=old_embedding[:2]
            for i,values in buckets.items():embedding[i]=np.mean(values,axis=0)
            model.layers[0].set_weights([embedding])
            for target,source in zip(model.layers[1:],old_model.layers[1:]):target.set_weights(source.get_weights())
            print('WARM_START',key,'mapped embedding rows',len(buckets),'of',len(vocabulary),flush=True)
            stop=keras.callbacks.EarlyStopping(monitor='val_loss',patience=3,min_delta=.001,restore_best_weights=True)
            history=model.fit(dataset(x,y,weights,True),validation_data=dataset(vx,vy,valweights),epochs=16,callbacks=[stop],verbose=2)
            path=HERE/'models'/f'{key}.keras';model.save(path)
            loaded=keras.models.load_model(path,compile=False);scores=loaded(vx,training=False).numpy().reshape(-1)
            threshold,rank=common.choose_threshold(va,scores);ranks[key]=rank
            configs[key]=dict(architecture=architecture,seed=seed,threshold=threshold,model_file=f'models/{key}.keras',model_sha256=common.sha(path),eligible=rank[0],
                 validation_source=common.measure(vy[original],scores[original],threshold),validation_authored=common.measure(vy[~original],scores[~original],threshold),
                 epochs_run=len(history.history['loss']),restored_epoch=int(stop.best_epoch)+1)
            pd.DataFrame(history.history).to_csv(HERE/f'history_{key}.csv',index=False)
            print('CANDIDATE',key,json.dumps(configs[key],ensure_ascii=False),flush=True)
    selected=max(configs,key=lambda k:ranks[k])
    if not configs[selected]['eligible']:raise RuntimeError('No DL candidate meets validation gates; keep current deployment')
    manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
    config=dict(selected=selected,candidates=configs,dataset_id=manifest['dataset_id'],dataset_manifest_sha256=common.sha(DATA/'manifest.json'),
                normalizer_sha256=common.sha(DATA/'vi_text_v2.py'),normalization=VERSION,preprocessing_sha256=common.sha(HERE/'preprocessing.json'),
                language='vi',initialization={'kind':'warm start from previous authored-coverage revision; embedding IDs remapped through shared normalizer','files':{name:common.sha(ROOT/'cloud_app/bo_sung_tv4_app/vi_model_revision/dl/models'/f'{name}.keras') for name in ('lstm','conv1d')}},source_script_sha256=common.sha(Path(__file__)),selection='Same source/authored validation gates and ranking as ML; no challenge/test/regression used for selecting')
    (HERE/'model_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    # Evaluate only after model and threshold locked.
    entry=configs[selected];model=keras.models.load_model(HERE/entry['model_file'],compile=False);results={}
    for split in ('test','challenge','regression'):
        f=pd.read_csv(DATA/f'data/{split}.csv');tokens=vec(tf.constant(f.input_key.to_list())).numpy();scores=model(tokens,training=False).numpy().reshape(-1)
        results[split]=common.measure(f.y,scores,entry['threshold'])
        pd.DataFrame(dict(id=f.id,text=f.text,y_true=f.y,score=scores,y_pred=(scores>=entry['threshold']).astype(int))).to_csv(HERE/f'pred_{split}.csv',index=False)
    report=dict(selected=selected,validation=entry,results=results,provenance='Inherited source benchmark; authored challenge frozen before training but not a human-verified real SMS holdout.')
    (HERE/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()

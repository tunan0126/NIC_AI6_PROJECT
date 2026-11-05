"""Train-only native/folded views; deployed inference uses one folded view.

Views of one SMS always stay in its original split. Known regression cases are
a release gate, never training input. No test/challenge score chooses a model.
"""
from train import *
from collections import Counter
from vi_text_v2 import redact


def main():
    tr=pd.read_csv(DATA/'data/train.csv');va=pd.read_csv(DATA/'data/val.csv')
    native=[redact(t).casefold() for t in tr.text]
    folded=tr.input_key.to_list()
    previous=ROOT/'cloud_app/bo_sung_tv4_app/vi_model_revision/dl'
    oldprep=json.loads((previous/'preprocessing.json').read_text(encoding='utf-8'))
    oldvocab=oldprep['vocabulary'];counts=Counter(' '.join(native+folded).split())
    vocabulary=list(oldvocab)
    vocabulary.extend(w for w,_ in counts.most_common() if w not in set(oldvocab))
    length=int(np.clip(np.ceil(np.percentile(tr.input_key.str.split().str.len(),95)),24,160))
    vec=keras.layers.TextVectorization(max_tokens=len(vocabulary)+1,standardize=None,split='whitespace',output_mode='int',output_sequence_length=length,vocabulary=vocabulary)
    prep=dict(max_tokens=len(vocabulary)+1,sequence_length=length,vocabulary=vocabulary,normalization=VERSION,split='whitespace')
    x=vec(tf.constant(native+folded)).numpy();y=np.tile(tr.y.to_numpy(dtype=np.int32),2)
    vx=vec(tf.constant(va.input_key.to_list())).numpy();vy=va.y.to_numpy(dtype=np.int32)
    cw=compute_class_weight('balanced',classes=np.array([0,1]),y=y)
    weights=cw[y]*np.tile(np.where(tr.source.eq('published-corpus'),1.,6.),2)/2
    original=va.source.eq('published-corpus').to_numpy();valweights=np.where(original,1.,sum(original)/sum(~original))
    legacy=pd.read_csv(DATA/'data/regression.csv').iloc[:24]
    lx=vec(tf.constant(legacy.input_key.to_list())).numpy()
    configs={};ranks={};tf.config.experimental.enable_op_determinism()
    for architecture in ('lstm','conv1d'):
        key=f'{architecture}_dual_42';keras.backend.clear_session();keras.utils.set_random_seed(42)
        model=build(architecture,len(vocabulary),length)
        old=keras.models.load_model(previous/'models'/f'{architecture}.keras',compile=False)
        embedding=model.layers[0].get_weights()[0];old_embedding=old.layers[0].get_weights()[0]
        embedding[:len(oldvocab)]=old_embedding
        aliases={}
        for i,w in enumerate(oldvocab[2:],2):
            fw=normalize(w)
            if fw not in aliases or counts[w]>counts[oldvocab[aliases[fw]]]:aliases[fw]=i
        for i,w in enumerate(vocabulary[len(oldvocab):],len(oldvocab)):
            if w in aliases:embedding[i]=old_embedding[aliases[w]]
        model.layers[0].set_weights([embedding])
        for target,source in zip(model.layers[1:],old.layers[1:]):target.set_weights(source.get_weights())
        stop=keras.callbacks.EarlyStopping(monitor='val_loss',patience=5,min_delta=.001,restore_best_weights=True)
        history=model.fit(dataset(x,y,weights,True),validation_data=dataset(vx,vy,valweights),epochs=24,callbacks=[stop],verbose=2)
        path=HERE/'models'/f'{key}.keras';model.save(path)
        scores=model(vx,training=False).numpy().reshape(-1)
        threshold,rank=common.choose_threshold(va,scores)
        legacy_scores=model(lx,training=False).numpy().reshape(-1)
        errors=int(np.sum((legacy_scores>=threshold).astype(int)!=legacy.y.to_numpy()))
        rank=(rank[0] and errors==0,)+rank[1:];ranks[key]=rank
        configs[key]=dict(architecture=architecture,seed=42,threshold=threshold,model_file=f'models/{key}.keras',model_sha256=common.sha(path),eligible=rank[0],legacy_regression_release_errors=errors,validation_source=common.measure(vy[original],scores[original],threshold),validation_authored=common.measure(vy[~original],scores[~original],threshold),epochs_run=len(history.history['loss']),restored_epoch=int(stop.best_epoch)+1)
        pd.DataFrame(history.history).to_csv(HERE/f'history_{key}.csv',index=False)
        print('CANDIDATE',key,json.dumps(configs[key]),flush=True)
        (HERE/'dual_candidates.json').write_text(json.dumps(configs,indent=2),encoding='utf-8')
    selected=max(configs,key=lambda k:ranks[k])
    if not configs[selected]['eligible']:raise RuntimeError('No dual-view candidate passes fixed validation and legacy gates; keep deployed DL')
    (HERE/'preprocessing.json').write_text(json.dumps(prep,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
    config=dict(selected=selected,candidates=configs,dataset_id=manifest['dataset_id'],dataset_manifest_sha256=common.sha(DATA/'manifest.json'),normalizer_sha256=common.sha(DATA/'vi_text_v2.py'),normalization=VERSION,preprocessing_sha256=common.sha(HERE/'preprocessing.json'),language='vi',source_script_sha256=common.sha(Path(__file__)),initialization={'kind':'warm-start native vocabulary preserved; two train-only views; authored weight 6','files':{name:common.sha(previous/'models'/f'{name}.keras') for name in ('lstm','conv1d')}},selection='Fixed source/authored validation gates, then legacy 24 regression release gate; no challenge/test used for selection')
    (HERE/'model_config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    entry=configs[selected];model=keras.models.load_model(HERE/entry['model_file'],compile=False);results={}
    for split in ('test','challenge','regression'):
        f=pd.read_csv(DATA/f'data/{split}.csv');scores=model(vec(tf.constant(f.input_key.to_list())),training=False).numpy().reshape(-1)
        results[split]=common.measure(f.y,scores,entry['threshold'])
        pd.DataFrame(dict(id=f.id,text=f.text,y_true=f.y,score=scores,y_pred=(scores>=entry['threshold']).astype(int))).to_csv(HERE/f'pred_{split}.csv',index=False)
    report=dict(selected=selected,validation=entry,results=results,provenance=manifest['provenance'])
    (HERE/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()

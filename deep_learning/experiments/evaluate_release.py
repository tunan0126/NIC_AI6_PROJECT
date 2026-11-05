"""Collect rejected validation trials and evaluate the retained baseline.

Rejected trials are not scored on test to pick a replacement. Retained model
scores are diagnostic and do not claim a new independently reviewed holdout.
"""
from pathlib import Path
import importlib.util,json,sys
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'cloud_app/bo_sung_tv4_app'))
from model_service import ModelService
spec=importlib.util.spec_from_file_location('v2_metrics',ROOT/'traditional_ml/bo_sung_tv2_v2/train.py')
common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)


def main():
    trials=[]
    for name,kind in [('attempt_01.log','fresh-word'),('training.log','warm-start-folded-word'),('training_dual.log','warm-start-dual-train-view')]:
        for line in (HERE/name).read_text(encoding='utf-8',errors='replace').splitlines():
            if not line.startswith('CANDIDATE '):continue
            _,key,raw=line.split(' ',2)
            trials.append(dict(attempt=kind,key=key,**json.loads(raw)))
    trials.append(dict(attempt='fresh-character',key='conv1d_char_42',**json.loads((HERE/'char_candidate.json').read_text(encoding='utf-8'))))
    for trial in trials:
        path=HERE/trial['model_file']
        trial['saved_weights_match_trial']=path.exists() and common.sha(path)==trial['model_sha256']
    assert len(trials)==11 and not any(t['eligible'] for t in trials)
    service=ModelService();model,vec,entry=service.load('dl','vi');loader=service.loader_for('dl','vi')
    results={}
    for split in ('test','challenge','regression'):
        f=pd.read_csv(ROOT/f'data_features/bo_sung_tv1_v2/data/{split}.csv')
        tokens=vec(loader.tf.constant([loader.redact(t) for t in f.text]))
        scores=np.concatenate([model(tokens[start:start+64],training=False).numpy().reshape(-1) for start in range(0,len(f),64)])
        results[split]=common.measure(f.y,scores,entry['threshold'])
        pd.DataFrame(dict(id=f.id,text=f.text,y_true=f.y,score=scores,y_pred=(scores>=entry['threshold']).astype(int))).to_csv(HERE/f'retained_pred_{split}.csv',index=False)
    report=dict(status='no_new_dl_release',reason='All 11 candidates fail fixed validation and/or legacy regression gates. Keep deployed prior Conv1D without silently lowering gates.',validation_gates=dict(source_precision=.90,source_recall=.95,authored_precision=.90,authored_recall=.90),trials=trials,retained_model=entry,retained_results=results,trial_artifacts='Fresh-word trial weights reused the experimental filenames later overwritten by warm-start attempt; initial logs only, marked saved_weights_match_trial=false. Original member and prior released model files are untouched. Dual-view vocabulary is recreated by train_dual.py; no new DL model_config/preprocessing release is emitted.',limits='Source benchmark inherited and already evaluated previously. Challenge/labels authored by assistant, not new real human-verified SMS. Regression already known and 24 cases used as release gate in dual attempt.')
    (HERE/'experiment_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(status=report['status'],trial_count=len(trials),retained_results=results),indent=2))


if __name__=='__main__':main()

"""Bản sửa triển khai TV4; giữ nguyên artifact/dữ liệu TV1-TV3.

Chọn biểu diễn, regularization, trọng số bổ sung và ngưỡng bằng hai validation.
Không fit/chọn bằng test gốc hoặc các câu hồi quy do người dùng báo.
"""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.metrics import precision_recall_curve, precision_recall_fscore_support, confusion_matrix, roc_auc_score, average_precision_score

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=ROOT/'traditional_ml/bo_sung_tv2/vi'
sys.path.insert(0,str(ROOT/'data_features/bo_sung_tv1'))
from privacy import redact


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(y,scores,threshold):
    pred=(scores>=threshold).astype(int)
    p,r,f,_=precision_recall_fscore_support(y,pred,average='binary',zero_division=0)
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return dict(Precision=round(float(p),4),Recall=round(float(r),4),F1=round(float(f),4),
                ROC_AUC=round(float(roc_auc_score(y,scores)),4),PR_AUC=round(float(average_precision_score(y,scores)),4),
                TN=int(tn),FP=int(fp),FN=int(fn),TP=int(tp))


def vectorizer(kind):
    word=TfidfVectorizer(ngram_range=(1,2),min_df=1,max_features=40000,sublinear_tf=True)
    char=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,max_features=60000,sublinear_tf=True)
    return word if kind=='word' else char if kind=='char_wb' else FeatureUnion([('word',word),('char',char)])


def main():
    train=pd.read_csv(BASE/'data/train.csv')
    original_val=pd.read_csv(BASE/'data/val.csv')
    authored=pd.read_csv(HERE/'data/train_authored.csv')
    authored_val=pd.read_csv(HERE/'data/validation_authored.csv')
    for frame in (authored,authored_val):frame['text']=frame.text.map(redact)
    regression=json.loads((HERE.parent/'tests/vi_semantic_cases.json').read_text(encoding='utf-8'))
    regression_texts={redact(row['text']).casefold() for row in regression}
    train_texts=set(pd.concat([train,authored]).text.str.casefold())
    val_texts=set(pd.concat([original_val,authored_val]).text.str.casefold())
    assert not train_texts & val_texts
    assert not regression_texts & (train_texts|val_texts), 'Regression examples must not be fit or used to select'
    full=pd.concat([train,authored],ignore_index=True)
    records=[];best=None;best_rank=None
    for kind in ('word','char_wb','word+char_wb'):
        for c in (1.,3.,10.):
            for boost in (1.,3.,6.):
                pipe=Pipeline([('vec',vectorizer(kind)),('clf',LogisticRegression(C=c,class_weight='balanced',max_iter=2000,random_state=42))])
                weights=np.r_[np.ones(len(train)),np.full(len(authored),boost)]
                pipe.fit(full.text,full.y,clf__sample_weight=weights)
                old_scores=np.round(pipe.predict_proba(original_val.text)[:,1],12)
                new_scores=np.round(pipe.predict_proba(authored_val.text)[:,1],12)
                # Duyệt ngưỡng validation; tối đa hóa F1 thấp hơn giữa hai ngữ cảnh.
                thresholds=np.unique(np.r_[old_scores,new_scores,.5])
                selected=None;selected_rank=None
                for threshold in thresholds:
                    a=metrics(original_val.y,old_scores,threshold)
                    b=metrics(authored_val.y,new_scores,threshold)
                    eligible=a['Recall']>=.98 and a['Precision']>=.90 and b['Recall']>=.95
                    rank=(eligible,min(a['F1'],b['F1']),(a['F1']+b['F1'])/2,min(a['Precision'],b['Precision']))
                    if selected_rank is None or rank>selected_rank:
                        selected_rank=rank;selected=(float(threshold),a,b)
                threshold,a,b=selected
                row=dict(representation=kind,C=c,authored_weight=boost,threshold=threshold,
                         original_validation=a,authored_validation=b,eligible=bool(selected_rank[0]))
                records.append(row)
                print(kind,c,boost,'old',a['F1'],'authored',b['F1'],'threshold',threshold,flush=True)
                if best_rank is None or selected_rank>best_rank:
                    best_rank=selected_rank;best=(pipe,row)
    model,selected=best
    assert selected['eligible'],'No eligible model; do not deploy'
    (HERE/'selection.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    joblib.dump(model,HERE/'model.joblib')
    (HERE/'config.json').write_text(json.dumps({'nguong':selected['threshold'],'score_decimals':12,'nhan':{'0':'ham','1':'spam'}},ensure_ascii=False,indent=2),encoding='utf-8')
    inputs={str(path.relative_to(ROOT)).replace('\\','/'):sha(path) for path in [BASE/'data/train.csv',BASE/'data/val.csv',HERE/'data/train_authored.csv',HERE/'data/validation_authored.csv']}
    dataset='vi-tv4-revision-'+hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()[:12]
    version=dict(language='vi',dataset_id=dataset,model_sha256=sha(HERE/'model.joblib'),score_decimals=12,
                 architecture='LogisticRegression',representation='TFIDF '+selected['representation'],
                 model_origin='tv4_vi_revision',source_script_sha256=sha(Path(__file__)),inputs_sha256=inputs,
                 packages={name:importlib.metadata.version(name) for name in ('scikit-learn','numpy','scipy','joblib')})
    (HERE/'version.json').write_text(json.dumps(version,ensure_ascii=False,indent=2),encoding='utf-8')
    # Chỉ sau khi khóa model/ngưỡng mới chấm test kế thừa và bộ hồi quy.
    test=pd.read_csv(BASE/'data/test.csv')
    test_scores=np.round(model.predict_proba(test.text)[:,1],12)
    y_reg=np.array([int(row['label']=='spam') for row in regression])
    reg_scores=np.round(model.predict_proba([redact(row['text']) for row in regression])[:,1],12)
    old_model=joblib.load(BASE/'model/model.joblib')
    old_threshold=json.loads((BASE/'model/config.json').read_text(encoding='utf-8'))['nguong']
    old_reg=np.round(old_model.predict_proba([redact(row['text']) for row in regression])[:,1],12)
    report=dict(selection=selected,selection_criterion='max min(F1 original validation, F1 authored validation), then mean F1, then min precision; original val Recall>=0.98, Precision>=0.90; authored Recall>=0.95',
                source_train=len(train),authored_train=len(authored),authored_validation=len(authored_val),
                source_test=metrics(test.y,test_scores,selected['threshold']),
                original_source_test=json.loads((BASE/'results/ket_qua_cuoi.json').read_text(encoding='utf-8'))['test_cuoi'],
                regression_development=metrics(y_reg,reg_scores,selected['threshold']),
                original_regression_development=metrics(y_reg,old_reg,old_threshold),
                provenance='Authored synthetic development messages, not real collected SMS; original train/val/test unchanged. Regression cases excluded from fitting and selection; inherited test already used in prior research, not a new untouched holdout.',
                model_version=version['model_sha256'][:12],dataset_id=dataset)
    (HERE/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    pd.DataFrame({'id':test.id,'text':test.text,'y_true':test.y,'score':test_scores,'y_pred':(test_scores>=selected['threshold']).astype(int)}).to_csv(HERE/'pred_revision_test.csv',index=False)
    pd.DataFrame({'text':[r['text'] for r in regression],'expected':y_reg,'old_score':old_reg,'new_score':reg_scores,
                  'old_pred':(old_reg>=old_threshold).astype(int),'new_pred':(reg_scores>=selected['threshold']).astype(int)}).to_csv(HERE/'regression_predictions.csv',index=False)
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()

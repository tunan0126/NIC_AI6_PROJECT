from pathlib import Path
import hashlib,json,sys
import joblib,numpy as np,pandas as pd
from sklearn.base import clone
from sklearn.pipeline import Pipeline,FeatureUnion
from sklearn.preprocessing import FunctionTransformer
from sklearn.feature_extraction.text import CountVectorizer,TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support,confusion_matrix,roc_auc_score,average_precision_score
from sklearn.model_selection import StratifiedGroupKFold
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];DATA=ROOT/'data_features/bo_sung_tv1_v2'
sys.path.insert(0,str(DATA))
from vi_text_v2 import normalize_many,VERSION


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def measure(y,scores,threshold):
    pred=np.asarray(scores)>=threshold
    p,r,f,_=precision_recall_fscore_support(y,pred,average='binary',zero_division=0)
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return dict(Precision=round(float(p),4),Recall=round(float(r),4),F1=round(float(f),4),
                TN=int(tn),FP=int(fp),FN=int(fn),TP=int(tp),ROC_AUC=round(float(roc_auc_score(y,scores)),4),PR_AUC=round(float(average_precision_score(y,scores)),4))


def prf(y,scores,thresholds):
    y=np.asarray(y,dtype=bool);positive=np.asarray(scores)[:,None]>=thresholds[None,:]
    tp=(positive & y[:,None]).sum(axis=0);fp=(positive & ~y[:,None]).sum(axis=0);fn=(~positive & y[:,None]).sum(axis=0)
    p=tp/np.maximum(tp+fp,1);r=tp/np.maximum(tp+fn,1);f=2*p*r/np.maximum(p+r,1e-12)
    return p,r,f


def choose_threshold(frame,scores):
    original=frame.source.eq('published-corpus').to_numpy()
    thresholds=np.unique(np.r_[scores,.5])
    pa,ra,fa=prf(frame.y[original],scores[original],thresholds);pb,rb,fb=prf(frame.y[~original],scores[~original],thresholds)
    eligible=(pa>=.90)&(ra>=.95)&(pb>=.90)&(rb>=.90)
    def rank(i):return (bool(eligible[i]),float(min(fa[i],fb[i])),float((fa[i]+fb[i])/2),float(min(pa[i],pb[i])))
    i=max(range(len(thresholds)),key=rank)
    return float(thresholds[i]),rank(i)


def main():
    frames={s:pd.read_csv(DATA/f'data/{s}.csv') for s in ('train','val')};tr,va=frames['train'],frames['val']
    manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
    vectors={'BoW':CountVectorizer(ngram_range=(1,2),min_df=1,max_features=40000),
             'TFIDF-word':TfidfVectorizer(ngram_range=(1,3),sublinear_tf=True,min_df=1,max_features=50000),
             'TFIDF-char':TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True,min_df=2,max_features=60000)}
    vectors['TFIDF-word+char']=FeatureUnion([('word',clone(vectors['TFIDF-word'])),('char',clone(vectors['TFIDF-char']))])
    groups=tr.input_key.str.replace(r'\d+','0',regex=True).str[:50]
    cv=list(StratifiedGroupKFold(3,shuffle=True,random_state=42).split(tr,tr.y,groups))
    classifiers={'NaiveBayes':MultinomialNB(alpha=1.),'LogReg-C1':LogisticRegression(C=1,class_weight='balanced',max_iter=2000,random_state=42),
        'LogReg-C3':LogisticRegression(C=3,class_weight='balanced',max_iter=2000,random_state=42),
        'SVM':CalibratedClassifierCV(LinearSVC(C=1,class_weight='balanced',random_state=42),cv=cv),
        'RandomForest':RandomForestClassifier(n_estimators=240,class_weight='balanced',random_state=42,n_jobs=2,min_samples_leaf=1)}
    weights=np.where(tr.source.eq('published-corpus'),1.,3.)
    legacy=pd.read_csv(DATA/'data/regression.csv').iloc[:24]
    records=[];best=None;best_rank=None
    for vector,vec in vectors.items():
        preprocessing=Pipeline([('normalize',FunctionTransformer(normalize_many,validate=False)),('vec',vec)])
        x=preprocessing.fit_transform(tr.text);vx=preprocessing.transform(va.text)
        for name,clf in classifiers.items():
            fitted=clone(clf).fit(x,tr.y,sample_weight=weights)
            scores=np.round(fitted.predict_proba(vx)[:,1],12)
            threshold,rank=choose_threshold(va,scores)
            legacy_scores=fitted.predict_proba(preprocessing.transform(legacy.text))[:,1]
            regression_errors=int(np.sum((legacy_scores>=threshold).astype(int)!=legacy.y.to_numpy()))
            rank=(rank[0] and regression_errors==0,)+rank[1:]
            original=va.source.eq('published-corpus')
            row=dict(vector=vector,model=name,threshold=threshold,eligible=rank[0],legacy_regression_release_errors=regression_errors,rank=rank[1:],
                     validation_source=measure(va.y[original],scores[original],threshold),validation_authored=measure(va.y[~original],scores[~original],threshold))
            records.append(row);print(vector,name,row['validation_source']['F1'],row['validation_authored']['F1'],rank[0],flush=True)
            if best_rank is None or rank>best_rank:best_rank=rank;best=(Pipeline(preprocessing.steps+[('clf',fitted)]),row)
    model,selected=best
    if not selected['eligible']:raise RuntimeError('No model meets validation gates; keep current deployment')
    joblib.dump(model,HERE/'model.joblib')
    (HERE/'config.json').write_text(json.dumps(dict(threshold=selected['threshold'],selection=selected,criterion='max min(source/authored val F1), then mean F1 and min precision; gates source P>=.90 R>=.95, authored P/R>=.90; previously seen 24 regression cases are a release gate, not independent evaluation'),ensure_ascii=False,indent=2),encoding='utf-8')
    version=dict(model_sha256=sha(HERE/'model.joblib'),normalizer_sha256=sha(DATA/'vi_text_v2.py'),dataset_id=manifest['dataset_id'],
                 dataset_manifest_sha256=sha(DATA/'manifest.json'),normalization=VERSION,architecture=selected['model'],representation=selected['vector'],language='vi',source_script_sha256=sha(Path(__file__)))
    (HERE/'version.json').write_text(json.dumps(version,ensure_ascii=False,indent=2),encoding='utf-8')
    (HERE/'selection.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    # Model/threshold locked; evaluate all inherited and new authored cases without selecting on them.
    results={}
    for split in ('test','challenge','regression'):
        f=pd.read_csv(DATA/f'data/{split}.csv');scores=np.round(model.predict_proba(f.text)[:,1],12)
        results[split]=measure(f.y,scores,selected['threshold'])
        pd.DataFrame(dict(id=f.id,text=f.text,y_true=f.y,score=scores,y_pred=(scores>=selected['threshold']).astype(int))).to_csv(HERE/f'pred_{split}.csv',index=False)
        folded=np.round(model.predict_proba(f.input_key)[:,1],12);assert np.array_equal(scores,folded),'Accent invariance failed'
    report=dict(selected=selected,results=results,provenance='Original corpus + synthetic development coverage; new challenge authored by assistant, not real independent human-labelled SMS. Seen 24 legacy regression cases excluded from fitting and used only as explicit release gate after validation thresholds are chosen; remaining seen cases are diagnostics. No challenge/test used for choosing model or threshold.')
    (HERE/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()

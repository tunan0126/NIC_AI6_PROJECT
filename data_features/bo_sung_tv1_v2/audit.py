from pathlib import Path
import json,sys
import numpy as np,pandas as pd
from vi_text_v2 import normalize
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'traditional_ml/TV2_hoc_may'))
from features_regex import regex_features_vi,REGEX_COLS_VI


def main():
    summaries=[];reviews=[]
    for split in ('train','val','test','challenge','regression'):
        frame=pd.read_csv(HERE/f'data/{split}.csv')
        values=regex_features_vi(frame.text.to_list())
        features=pd.DataFrame(values,columns=REGEX_COLS_VI)
        if 'co_sdt' in features:features['co_sdt']=np.maximum(features.co_sdt,frame.text.str.contains(r'\[PHONE\]',regex=True).astype(int))
        pd.concat([frame[['id','y']].reset_index(drop=True),features],axis=1).to_csv(HERE/f'data/{split}_regex.csv',index=False)
        for (source,label),part in frame.groupby(['source','y']):
            summaries.append(dict(split=split,source=source,label=int(label),rows=len(part),mean_characters=round(part.text.str.len().mean(),1),
                                  link_messages=int(part.text.str.contains(r'https?://',case=False,regex=True).sum())))
        if split in ('train','val','test'):
            folded=frame.text.map(normalize)
            suspect=(frame.y.eq(0)&folded.str.contains(r'casino|nha cai|lai.*moi ngay|gui mat khau|nap tien.*hoa hong',regex=True))
            part=frame[suspect].copy()
            part['review_reason']='Ham label with potentially promotional/credential language; context and consent need review, not automatic relabel'
            part['reviewer']='';part['confirmed_label']='';part['review_status']='needs_human_review'
            reviews.append(part[['id','text','y','source','review_reason','reviewer','confirmed_label','review_status']].assign(split=split))
    pd.DataFrame(summaries).to_csv(HERE/'reports/coverage.csv',index=False)
    review=pd.concat(reviews,ignore_index=True);review.to_csv(HERE/'reports/label_review_queue.csv',index=False)
    audit=dict(source_full_dataset={'repository':'trannguyenthaituan251209/vietnamese_sms_dataset','commit':'464a028878023598e16f2f344ee36f7d5d74257f',
        'file':'full_dataset.csv','sha256':'710cd7b56ef1b4aa82e72c1be0f46a5c89a5fdce8382b30874b3cea494d16e3e','rows':2991,'additional_rows_after_canonical_comparison':0},
        other_sources=[dict(url='https://github.com/pth1993/vie-spam-sms-filtering',commit='8987506ce73da3913bcf76aeb1050c77aa72af45',outcome='Only small example data publicly listed, no full usable new corpus; not used'),
                       dict(url='https://github.com/tocong282/vietnamese-fraud-detection',outcome='README describes same primary corpus plus synthetic augmentation; not treated as independent SMS holdout')],
        real_new_user_data='User confirmed unavailable; no private SMS solicited or fabricated as real.',
        review_queue_rows=len(review),automatic_label_changes=0,review_status='Publisher labels inherited; authored labels assigned by assistant; not independently human-validated')
    (HERE/'reports/source_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Regex features exported for five sets; human review queue:',len(review),'automatic label changes: 0')


if __name__=='__main__':main()

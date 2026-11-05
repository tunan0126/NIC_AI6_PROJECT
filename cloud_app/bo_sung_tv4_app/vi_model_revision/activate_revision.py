"""Khóa artifact đã huấn luyện, kiểm tra dữ liệu và phiên bản trước khi khởi động app."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ml=json.loads((HERE/'version.json').read_text(encoding='utf-8'))
    report=json.loads((HERE/'report.json').read_text(encoding='utf-8'))
    dl=json.loads((HERE/'dl/model_config.json').read_text(encoding='utf-8'))
    assert ml['inputs_sha256']==dl['source_inputs_sha256']
    for path,expected in ml['inputs_sha256'].items():assert sha(ROOT/path)==expected,path
    assert report['selection']['eligible']
    assert dl['candidates'][dl['selected']]['eligible']
    assert sha(HERE/'model.joblib')==ml['model_sha256']
    assert sha(HERE/'dl/preprocessing.json')==dl['preprocessing_sha256']
    for entry in dl['candidates'].values():assert sha(HERE/'dl'/entry['model_file'])==entry['model_sha256']
    active={'ml':{'model_sha256':sha(HERE/'model.joblib'),'config_sha256':sha(HERE/'config.json')},
            'dl':{'config_sha256':sha(HERE/'dl/model_config.json')}}
    (HERE/'active.json').write_text(json.dumps(active,indent=2),encoding='utf-8')
    print('Revision artifacts verified. Restart app to load this snapshot.')


if __name__=='__main__':main()

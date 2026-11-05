"""Hồi quy nghĩa các tin tự tạo; không phải benchmark độc lập hoặc dữ liệu train."""
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from model_service import ModelService


class VietnameseSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models=ModelService()

    def test_reported_meeting_message_is_legitimate(self):
        text='Nhóm sẽ họp lúc 14:00 để chuẩn bị bài thuyết trình.'
        for model in ('ml','dl'):
            with self.subTest(model=model):
                result=self.models.predict(text,model,'vi')
                self.assertEqual(result['label'],'ham',result)

    def test_authored_development_examples(self):
        cases=json.loads((HERE/'vi_semantic_cases.json').read_text(encoding='utf-8'))
        failures=[]
        for model in ('ml','dl'):
            for case in cases:
                result=self.models.predict(case['text'],model,'vi')
                if result['label']!=case['label']:
                    failures.append({'model':model,'text':case['text'],'expected':case['label'],'actual':result['label'],'score':result['score']})
        self.assertEqual(failures,[],json.dumps(failures,ensure_ascii=False,indent=2))


if __name__=='__main__':
    unittest.main(verbosity=2)

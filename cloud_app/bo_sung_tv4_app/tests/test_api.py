import concurrent.futures
from contextlib import closing, contextmanager
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import create_app, COOKIE
from model_service import ModelService


@contextmanager
def connect(path):
    with closing(sqlite3.connect(path)) as conn, conn:
        yield conn


class FakeModels:
    def __init__(self):self.calls=0
    def predict(self,text,model,language):
        self.calls+=1
        return dict(label='ham',score=.12,threshold=.6,model_version='fake-for-api-unit-tests',
                    dataset_id='fixture',model=model,language=language,truncated=False)
    def describe(self):return []


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.tmp.name)/'test.sqlite3')
        self.service=FakeModels()
        self.config={'TESTING':True,'DATABASE':self.path,'RATE_LIMITS':False,'ALLOW_REGISTRATION':True}
        self.app=create_app(self.config,self.service)
        self.a,self.ca=self.register('tester_a')
        self.b,self.cb=self.register('tester_b')

    def tearDown(self):self.tmp.cleanup()

    def register(self,username):
        client=self.app.test_client()
        csrf=client.get('/api/session').json['csrf']
        response=client.post('/api/register',json={'username':username,'display_name':username,
            'password':'Test-only-password-123'},headers={'X-CSRF-Token':csrf})
        self.assertEqual(response.status_code,201,response.json)
        return client,response.json['csrf']

    def post(self,client,csrf,path,**data):
        return client.post('/api'+path,json=data,headers={'X-CSRF-Token':csrf})

    def delete(self,client,csrf,path):
        return client.delete('/api'+path,headers={'X-CSRF-Token':csrf})

    def predict(self,client=None,csrf=None,**overrides):
        data=dict(text='Nội dung kiểm thử',sender='DEMO-A',model='ml',language='vi',save_history=True)
        data.update(overrides)
        return self.post(client or self.a,csrf or self.ca,'/predictions',**data)

    def test_auth_csrf_cookie_and_password_storage(self):
        anonymous=self.app.test_client()
        self.assertEqual(anonymous.get('/api/history').status_code,401)
        self.assertEqual(self.a.post('/api/rules',json={'sender':'x','type':'block'}).status_code,403)
        response=self.a.get('/api/session')
        self.assertIsNotNone(response.json['user'])
        cookie=self.a.get_cookie(COOKIE)
        self.assertTrue(cookie.http_only)
        self.assertEqual(cookie.same_site,'Lax')
        with connect(self.path) as conn:
            password=conn.execute('SELECT password_hash FROM users LIMIT 1').fetchone()[0]
            self.assertNotEqual(password,'Test-only-password-123')
            self.assertTrue(password.startswith('scrypt:'))

    def test_login_rotates_session_and_logout_revokes_cookie(self):
        old=self.a.get_cookie(COOKIE).value
        response=self.post(self.a,self.ca,'/login',username='tester_a',password='Test-only-password-123')
        self.assertEqual(response.status_code,200)
        stolen=self.app.test_client();stolen.set_cookie(COOKIE,old)
        self.assertEqual(stolen.get('/api/history').status_code,401)
        token=self.a.get_cookie(COOKIE).value
        self.post(self.a,response.json['csrf'],'/logout')
        stolen.set_cookie(COOKIE,token)
        self.assertEqual(stolen.get('/api/history').status_code,401)

    def test_cross_origin_and_expired_session(self):
        response=self.a.post('/api/rules',json={'sender':'x','type':'block'},
                            headers={'X-CSRF-Token':self.ca,'Origin':'https://other.example'})
        self.assertEqual(response.status_code,403)
        with connect(self.path) as conn:conn.execute('UPDATE sessions SET expires_at=0')
        self.assertEqual(self.a.get('/api/history').status_code,401)

    def test_rule_precedence_and_isolation(self):
        response=self.post(self.a,self.ca,'/rules',sender='DEMO-A',type='block',user_id='tester_b')
        self.assertEqual(response.status_code,200)
        result=self.predict().json
        self.assertEqual(result['decision_source'],'block')
        self.assertIsNone(result['score'])
        self.assertEqual(self.service.calls,0)
        other=self.predict(self.b,self.cb).json
        self.assertEqual(other['decision_source'],'model')
        self.assertEqual(self.service.calls,1)
        self.assertEqual(self.b.get('/api/rules').json['items'],[])

    def test_phone_rule_normalization(self):
        self.post(self.a,self.ca,'/rules',sender='0912 345 678',type='allow')
        self.assertEqual(self.predict(sender='0912345678').json['decision_source'],'allow')

    def test_conflicting_rule_needs_matching_version(self):
        self.post(self.a,self.ca,'/rules',sender='DEMO-A',type='block')
        conflict=self.post(self.a,self.ca,'/rules',sender='DEMO-A',type='allow')
        self.assertEqual(conflict.status_code,409)
        version=conflict.json['existing']['version']
        self.assertEqual(self.post(self.a,self.ca,'/rules',sender='DEMO-A',type='allow',expected_version=version).status_code,200)
        self.assertEqual(self.post(self.a,self.ca,'/rules',sender='DEMO-A',type='block',expected_version=version).status_code,409)
        self.assertEqual(self.a.get('/api/rules').json['items'][0]['type'],'allow')

    def test_cross_user_ids_are_rejected_for_reads_and_mutations(self):
        pid=self.predict().json['prediction_id']
        rid=self.post(self.a,self.ca,'/rules',sender='DEMO-A',type='block').json['id']
        self.assertEqual(self.b.get('/api/predictions/'+pid).status_code,404)
        self.assertEqual(self.delete(self.b,self.cb,'/history/'+pid).status_code,404)
        self.assertEqual(self.delete(self.b,self.cb,'/rules/'+rid).status_code,404)
        self.assertEqual(self.post(self.b,self.cb,'/feedback',prediction_id=pid,proposed_label='spam').status_code,404)
        self.assertEqual(self.b.get('/api/history').json['total'],0)
        self.assertEqual(self.a.get('/api/history').json['total'],1)

    def test_history_opt_in_redaction_and_feedback(self):
        text='Email user@example.com, gọi 0912345678, OTP 123456'
        hidden=self.predict(text=text,save_history=False).json['prediction_id']
        self.assertEqual(self.a.get('/api/history').json['total'],0)
        self.assertIsNone(self.a.get('/api/predictions/'+hidden).json['text'])
        shown=self.predict(text=text).json['prediction_id']
        row=self.a.get('/api/history').json['items'][0]
        self.assertNotIn('user@example.com',row['text'])
        self.assertNotIn('0912345678',row['text'])
        self.post(self.a,self.ca,'/feedback',prediction_id=shown,proposed_label='spam',note=text)
        self.assertEqual(len(self.a.get('/api/feedback').json['items']),1)
        self.assertEqual(len(self.b.get('/api/feedback').json['items']),0)
        self.assertNotIn('user@example.com',self.a.get('/api/feedback').json['items'][0]['note'])
        self.delete(self.a,self.ca,'/history')
        self.assertEqual(self.a.get('/api/history').json['total'],0)
        self.assertEqual(len(self.a.get('/api/feedback').json['items']),1)
        with connect(self.path) as conn:
            rows=conn.execute('SELECT text_redacted,sender_display,result FROM predictions').fetchall()
            self.assertTrue(all(row[0] is None and row[1] is None for row in rows))
            self.assertTrue(all('user@example.com' not in row[2] and 'sender_display' not in row[2] for row in rows))

    def test_feedback_update_is_not_duplicated_and_does_not_train(self):
        pid=self.predict().json['prediction_id']
        self.post(self.a,self.ca,'/feedback',prediction_id=pid,proposed_label='spam')
        self.post(self.a,self.ca,'/feedback',prediction_id=pid,proposed_label='ham')
        items=self.a.get('/api/feedback').json['items']
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]['proposed_label'],'ham')
        self.assertEqual(self.service.calls,1)

    def test_request_replay_prevents_duplicate_history(self):
        first=self.predict(request_id='request-1').json
        second=self.predict(request_id='request-1')
        self.assertEqual(second.status_code,200)
        self.assertEqual(second.json['prediction_id'],first['prediction_id'])
        self.assertEqual(self.a.get('/api/history').json['total'],1)
        self.assertEqual(self.predict(request_id='request-1',text='Khác nội dung').status_code,409)

    def test_concurrent_replay_has_one_record(self):
        token=self.a.get_cookie(COOKIE).value
        def call(_):
            client=self.app.test_client();client.set_cookie(COOKIE,token)
            return self.predict(client,self.ca,request_id='parallel-1')
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            responses=list(pool.map(call,range(2)))
        self.assertTrue(all(r.status_code in (200,201) for r in responses),[r.json for r in responses])
        self.assertEqual(len({r.json['prediction_id'] for r in responses}),1)
        self.assertEqual(self.a.get('/api/history').json['total'],1)

    def test_pagination_and_invalid_inputs(self):
        for i in range(21):self.predict(text=f'Tin {i}')
        self.assertEqual(len(self.a.get('/api/history').json['items']),20)
        self.assertEqual(len(self.a.get('/api/history?page=2').json['items']),1)
        self.assertEqual(self.a.get('/api/history?label=spam').json['total'],0)
        for data in [{'text':''},{'text':'a'*2001},{'language':'xx'},{'model':'other'},
                     {'save_history':'true'},{'sender':23},{'text':['wrong']},{'request_id':'x'*65}]:
            with self.subTest(data=str(data)[:40]):self.assertEqual(self.predict(**data).status_code,400)
        self.assertEqual(self.a.get('/api/history?page=bad').status_code,400)
        self.assertEqual(self.a.get('/api/history?label=unknown').status_code,400)

    def test_database_and_session_survive_app_restart(self):
        self.predict()
        token=self.a.get_cookie(COOKIE).value
        restarted=create_app(self.config,FakeModels()).test_client()
        restarted.set_cookie(COOKIE,token)
        self.assertEqual(restarted.get('/api/history').json['total'],1)

    def test_rate_limit_and_security_headers(self):
        self.app.config['RATE_LIMITS']=True
        for _ in range(20):
            response=self.post(self.a,self.ca,'/login',username='missing',password='wrong')
            self.assertEqual(response.status_code,401)
        self.assertEqual(self.post(self.a,self.ca,'/login',username='missing',password='wrong').status_code,429)
        response=self.a.get('/api/session')
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])


class RealModelsTest(unittest.TestCase):
    def test_api_matches_real_packaged_loaders_for_both_languages_and_model_types(self):
        service=ModelService()
        with tempfile.TemporaryDirectory() as tmp:
            app=create_app({'TESTING':True,'DATABASE':str(Path(tmp)/'real.sqlite3'),'RATE_LIMITS':False},service)
            client=app.test_client();csrf=client.get('/api/session').json['csrf']
            response=client.post('/api/register',json={'username':'real_test','display_name':'Real model test',
                'password':'Real-model-test-123'},headers={'X-CSRF-Token':csrf})
            csrf=response.json['csrf']
            for language,text in [('vi','NHẬN QUÀ! Mã OTP là 123456.'),('uci','Congratulations! Free prize, call to claim now!')]:
                for model in ('ml','dl'):
                    with self.subTest(language=language,model=model):
                        result=client.post('/api/predictions',json={'text':text,'model':model,'language':language},
                                           headers={'X-CSRF-Token':csrf})
                        self.assertEqual(result.status_code,201,result.json)
                        expected=service.loader_for(model,language).predict(text,service.load(model,language))
                        for key in ('label','score','threshold','model_version','dataset_id'):
                            self.assertEqual(result.json[key],expected[key])
                        self.assertEqual(result.json['label'],'spam' if result.json['score']>=result.json['threshold'] else 'ham')
            for model in ('ml','dl'):
                response=client.post('/api/predictions',json={'text':'Nhóm sẽ họp lúc 14:00 để chuẩn bị bài thuyết trình.',
                    'model':model,'language':'vi'},headers={'X-CSRF-Token':csrf})
                self.assertEqual(response.status_code,201,response.json)
                self.assertEqual(response.json['label'],'ham',response.json)
                self.assertEqual(response.json['model_origin'],'tv1_4_v2' if model=='ml' else 'tv4_vi_revision')


if __name__=='__main__':
    unittest.main(verbosity=2)

from contextlib import ExitStack
from datetime import date
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from shared.config import Settings
from shared.service_loader import load_service
from test_access_integration import lab
from test_pedagogy_integration import pedagogy
from test_exercise_integration import practice,start,answer

pytestmark=pytest.mark.integration

@pytest.fixture
def school(practice):
    p=practice
    with ExitStack() as stack:
        for name in ['class','analytics','admin','speech','notification']:
            config=Settings(service_name=name+'-service',db_name=p.engine.url.database,db_user='edu_'+name,
                db_password_file=Path('/run/secrets/db_'+name),redis_username='edu_'+name,redis_db=15,
                redis_password_file=Path('/run/secrets/redis_'+name))
            p.clients[name]=stack.enter_context(TestClient(load_service(name+'-service').build_app(config)))
        r=p.clients['class'].post('/classes',headers=p.headers(p.teacher_token),json={'name':'Atelier','level':'CM1','academic_year':2026,'teacher_id':p.teacher['teacher_id']})
        assert r.status_code==201,r.text
        p.class_id=r.json()['id']
        r=p.clients['class'].post(f'/classes/{p.class_id}/students',headers=p.headers(p.teacher_token),json={'student_id':p.student['student_id']})
        assert r.status_code==200,r.text
        yield p

def submit_job(p,kind,token=None,**kwargs):
    r=p.clients['notification'].post('/jobs',headers=p.headers(token or p.teacher_token),json={'kind':kind,'idempotency_key':str(uuid4()),**kwargs})
    assert r.status_code==202,r.text
    return r.json()

def process(p):
    from edu_notification_service.worker import process
    return process(p.clients['notification'].app.state.engine)

def test_class_groups_missions_and_unenrollment(school):
    p=school;client=p.clients['class'];headers=p.headers(p.teacher_token)
    r=client.post(f'/classes/{p.class_id}/groups',headers=headers,json={'name':'Atelier guidé','student_ids':[p.student['student_id']]})
    assert r.status_code==201,r.text
    group=r.json()['id']
    r=client.post(f'/classes/{p.class_id}/missions',headers=headers,json={'title':'Mission du jour','day':str(date.today()),'group_id':group,'exercise_version_ids':[p.live['id']]})
    assert r.status_code==201,r.text
    assert len(client.get('/missions/today',headers=p.headers(p.student_token)).json())==1
    stranger=p.create('teacher');token=p.login(stranger['login'])
    assert client.get(f'/classes/{p.class_id}/students',headers=p.headers(token)).status_code==404
    r=client.delete(f"/classes/{p.class_id}/students/{p.student['student_id']}",headers=headers);assert r.status_code==204,r.text
    assert client.get('/missions/today',headers=p.headers(p.student_token)).json()==[]

def test_dashboards_parent_links_and_no_private_scores(school):
    p=school;a=start(p);assert answer(p,a).status_code==200
    parent=p.create('parent');token=p.login(parent['login'])
    path=f"/students/{p.student['student_id']}/dashboard"
    assert p.clients['analytics'].get(path,headers=p.headers(token)).status_code==404
    p.link(parent,p.student)
    r=p.clients['analytics'].get(path,headers=p.headers(token));assert r.status_code==200,r.text
    assert r.json()['tentatives_terminees']==1
    for key in ['probability','score','rank','classement']:assert key not in r.text
    assert p.clients['analytics'].get(path,headers=p.headers(p.teacher_token)).status_code==200
    r=p.clients['analytics'].get(f'/classes/{p.class_id}/dashboard',headers=p.headers(p.teacher_token));assert r.status_code==200,r.text

def test_flags_moderation_and_safety_are_admin_only(school):
    p=school;admin=p.clients['admin']
    assert admin.get('/safety/events',headers=p.headers(p.student_token)).status_code==403
    r=admin.put('/feature-flags/missions',headers=p.headers(p.admin),json={'enabled':False,'expected_revision':0});assert r.status_code==200,r.text
    assert admin.put('/feature-flags/missions',headers=p.headers(p.admin),json={'enabled':True,'expected_revision':0}).status_code==409
    assert p.clients['class'].get('/missions/today',headers=p.headers(p.student_token)).status_code==403
    r=admin.get('/moderation/pending',headers=p.headers(p.admin));assert r.status_code==200,r.text

def test_report_worker_delivers_once_to_verified_parent(school):
    p=school;parent=p.create('parent');p.link(parent,p.student);token=p.login(parent['login'])
    j=submit_job(p,'weekly_reports');process(p)
    r=p.clients['notification'].get('/jobs/'+j['id'],headers=p.headers(p.teacher_token));assert r.status_code==200,r.text
    assert r.json()['status']=='completed',r.text
    notices=p.clients['notification'].get('/inbox',headers=p.headers(token));assert notices.status_code==200,notices.text
    assert len(notices.json())==1
    submit_job(p,'weekly_reports');process(p)
    assert len(p.clients['notification'].get('/inbox',headers=p.headers(token)).json())==1
    with p.engine.begin() as c:c.execute(text('UPDATE guardian_students SET revoked_at=now() WHERE student_id=:id'),{'id':p.student['student_id']})
    assert p.clients['notification'].get('/inbox',headers=p.headers(token)).json()==[]

def test_batch_is_validated_draft_and_revoked_worker_is_denied(school):
    p=school
    j=submit_job(p,'exercise_batch',generations=[{'template':'arithmetic','kind':'short_text','competency_id':p.competencies[0],'source_ids':[p.source],'seed':7}])
    process(p)
    r=p.clients['notification'].get('/jobs/'+j['id'],headers=p.headers(p.teacher_token));assert r.json()['status']=='completed',r.text
    id=r.json()['result']['draft_version_ids'][0]
    with p.engine.connect() as c:assert c.scalar(text('SELECT status FROM exercise_versions WHERE id=:id'),{'id':id})=='draft'
    j=submit_job(p,'difficulty_alerts')
    with p.engine.begin() as c:c.execute(text("UPDATE users SET status='locked' WHERE id=:id"),{'id':p.teacher['id']})
    process(p)
    with p.engine.connect() as c:assert c.scalar(text('SELECT status FROM background_jobs WHERE id=:id'),{'id':j['id']})=='failed'

def test_speech_consent_and_flags(school,monkeypatch):
    p=school;client=p.clients['speech'];payload={'exercise_version_id':p.live['id']}
    assert client.post('/synthesize',headers=p.headers(p.student_token),json=payload).status_code==403
    parent=p.create('parent');p.link(parent,p.student);token=p.login(parent['login'])
    r=p.clients['user'].post(f"/students/{p.student['student_id']}/consents",headers=p.headers(token),json={'purpose':'voice','policy_version':'2026-09-v1','granted':True,'understood':True});assert r.status_code==201,r.text
    r=p.clients['user'].post('/me/assents',headers=p.headers(p.student_token),json={'purpose':'voice','policy_version':'2026-09-v1','agreed':True});assert r.status_code==201,r.text
    from edu_speech_service import routes
    monkeypatch.setattr(routes,'synthesize',lambda text:b'RIFF-test-double')
    r=client.post('/synthesize',headers=p.headers(p.student_token),json=payload)
    assert r.status_code==200 and r.headers['content-type']=='audio/wav',r.text
    assert 'no-store' in r.headers['cache-control']


def test_automation_auth_scope_and_idempotency(school,tmp_path):
    import json
    p=school;client=p.clients['notification'];keyfile=tmp_path/'keys.json'
    keyfile.write_text(json.dumps([{'token':'test-automation-secret','school_id':str(p.school),'user_id':p.teacher['id'],'kinds':['weekly_reports']}]))
    client.app.state.settings.automation_keys_file=keyfile
    body={'kind':'weekly_reports','idempotency_key':str(uuid4())}
    assert client.post('/automation/jobs',json=body).status_code==403
    headers={'X-Edu-Automation':'test-automation-secret'}
    r=client.post('/automation/jobs',headers=headers,json=body);assert r.status_code==202,r.text
    assert client.post('/automation/jobs',headers=headers,json=body).json()['id']==r.json()['id']
    assert client.post('/automation/jobs',headers=headers,json={**body,'kind':'privacy_purge'}).status_code==403


def test_difficulty_alert_and_expiry_purge(school):
    p=school
    for _ in range(3):
        a=start(p)
        with p.engine.begin() as c:
            c.execute(text('UPDATE exercise_attempts SET max_hint_level=5 WHERE id=:id'),{'id':a['id']})
    job=submit_job(p,'difficulty_alerts');process(p)
    r=p.clients['notification'].get('/jobs/'+job['id'],headers=p.headers(p.teacher_token));assert r.json()['status']=='completed',r.text
    notices=p.clients['notification'].get('/inbox',headers=p.headers(p.teacher_token)).json()
    assert len(notices)==1 and notices[0]['kind']=='difficulty_alert'
    with p.engine.begin() as c:c.execute(text("UPDATE notifications SET expires_at=now()-interval '1 day' WHERE id=:id"),{'id':notices[0]['id']})
    j=submit_job(p,'privacy_purge',token=p.admin);process(p)
    r=p.clients['notification'].get('/jobs/'+j['id'],headers=p.headers(p.admin));assert r.json()['status']=='completed',r.text
    assert r.json()['result']['notifications']==1

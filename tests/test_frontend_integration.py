import pytest
from test_school_integration import school
from test_access_integration import lab
from test_pedagogy_integration import pedagogy
from test_exercise_integration import practice,start

pytestmark=pytest.mark.integration

def test_teacher_controls_are_enforced_by_tutor_and_hints(school):
    p=school;path=f"/classes/{p.class_id}/students/{p.student['student_id']}/tutor-control"
    c=p.clients['class'];h=p.headers(p.teacher_token)
    assert c.get(path,headers=h).json()['max_help']==6
    r=c.put(path,headers=h,json={'enabled':True,'max_help':0,'expected_revision':0});assert r.status_code==200,r.text
    assert c.put(path,headers=h,json={'enabled':True,'max_help':6,'expected_revision':0}).status_code==409
    a=start(p)
    assert p.a.get(f"/attempts/{a['id']}/hints/1",headers=p.headers(p.student_token)).status_code==403
    assert c.put(path,headers=p.headers(p.student_token),json={'enabled':False,'max_help':0,'expected_revision':1}).status_code==403
    r=c.put(path,headers=h,json={'enabled':False,'max_help':0,'expected_revision':1});assert r.status_code==200,r.text
    from shared.db.session import tenant_session
    from shared.school import tutor_limit
    from fastapi import HTTPException
    with tenant_session(c.app.state.engine,p.school) as session:
        with pytest.raises(HTTPException) as exc:tutor_limit(session,p.student['student_id'])
        assert exc.value.status_code==403

def test_controls_require_class_assignment_and_published_route_is_public_shape(school):
    p=school;other=p.create('teacher');token=p.login(other['login'])
    path=f"/classes/{p.class_id}/students/{p.student['student_id']}/tutor-control"
    assert p.clients['class'].get(path,headers=p.headers(token)).status_code==404
    response=p.clients['exercise'].get('/published/'+p.live['id'],headers=p.headers(p.student_token))
    assert response.status_code==200,response.text
    assert 'answer_spec' not in response.text and 'candidate' not in response.json()


from test_ai_integration import ai,document,consent,turn

def test_tutor_replay_respects_lowered_limit_and_suspension(ai):
    from sqlalchemy import text
    from uuid import uuid4
    p=ai;document(p);consent(p)
    assert turn(p).json()['niveau_aide']==0
    key=str(uuid4());r=turn(p,request_id=key,plus_aide=True)
    assert r.status_code==200 and r.json()['niveau_aide']==1,r.text
    with p.engine.begin() as c:
        c.execute(text('INSERT INTO tutor_controls(tenant_id,student_id,changed_by,max_help) VALUES (:t,:s,:u,0)'),{'t':str(p.school),'s':p.student['student_id'],'u':p.teacher['id']})
    replay=turn(p,request_id=key,plus_aide=True)
    assert replay.status_code==200 and replay.json()['niveau_aide']==0,replay.text
    assert turn(p,plus_aide=True).json()['niveau_aide']==0
    with p.engine.begin() as c:c.execute(text('UPDATE tutor_controls SET enabled=false WHERE student_id=:s'),{'s':p.student['student_id']})
    calls=len(p.provider_calls)
    assert turn(p).status_code==403
    assert len(p.provider_calls)==calls

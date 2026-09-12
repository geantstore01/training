from uuid import UUID
from pathlib import Path
import pytest
from test_access_integration import lab
from test_pedagogy_integration import pedagogy
from test_exercise_integration import practice
from scripts.stage_french_courses import stage
from shared.service_loader import load_service
from uuid import uuid4

@pytest.mark.integration
def test_install_review_publish_and_private_answers(practice,tmp_path):
    p=practice
    source=tmp_path/'synthetic.pdf';source.write_bytes(b'%PDF synthetic test fixture; never a production source')
    result=stage(p.engine,UUID(str(p.school)),UUID(p.creator['id']),source,True)
    assert result['exercises_created']==84
    assert stage(p.engine,UUID(str(p.school)),UUID(p.creator['id']),source,True)['exercises_created']==0
    content=p.clients['content'];teacher=p.headers(p.teacher_token);student=p.headers(p.student_token)
    assert content.get('/french/review-catalogue',headers=student).status_code==403
    courses=content.get('/french/review-catalogue',headers=teacher).json()['courses'];assert len(courses)==28
    from edu_content_service.schemas import ContentBody
    for course in courses:ContentBody.model_validate(course['body'])
    course=next(c for c in courses if 'attribut' in c['title'])
    url=f"/contents/{course['id']}/versions/1/reviews"
    approval=dict(decision='approved',reason_code='TEST_CHECKED',confirmed_human_review=True)
    assert content.post(url,headers=teacher,json=approval).status_code==422
    ids=[course['body']['cm2']['check_exercise_id'],*course['body']['cm2']['practice_exercise_ids']]
    for identifier in ids:
        assert p.e.get('/review-version/'+identifier,headers=student).status_code==403
        ex=p.e.get('/review-version/'+identifier,headers=teacher).json()
        review=f"/exercises/{ex['exercise_id']}/versions/1/reviews"
        assert p.e.post(review,headers=p.headers(p.creator_token),json=approval).status_code==403
        assert p.e.post(review,headers=teacher,json=approval).status_code==200
        public=p.e.get('/published/'+identifier,headers=student).json();assert 'candidate' not in public and 'answer_spec' not in public
    assert content.post(url,headers=teacher,json=approval).status_code==201
    assert content.get(f"/contents/{course['id']}/versions/1",headers=student).status_code==200

@pytest.mark.integration
def test_owner_publication_without_fabricated_review(practice,tmp_path):
    from scripts.publish_french_owner import publish
    from sqlalchemy import text
    p=practice;source=tmp_path/'fixture.pdf';source.write_bytes(b'%PDF synthetic fixture')
    stage(p.engine,UUID(str(p.school)),UUID(p.creator['id']),source,True)
    with p.engine.connect() as c:before=c.scalar(text('SELECT count(*) FROM content_reviews WHERE tenant_id=:t'),{'t':p.school})
    assert publish(p.engine,UUID(str(p.school)))['lessons']==28
    assert publish(p.engine,UUID(str(p.school)))['exercises']==84
    with p.engine.connect() as c:assert c.scalar(text('SELECT count(*) FROM content_reviews WHERE tenant_id=:t'),{'t':p.school})==before
    headers=p.headers(p.student_token)
    assert p.clients['content'].get('/availability',headers=headers).status_code==200
    assert len(p.clients['content'].get('/availability',headers=headers).json()['competency_ids'])>=28

@pytest.mark.integration
def test_course_report_scores_three_exercises_and_builds_remediation(practice,tmp_path):
    from scripts.publish_french_owner import publish
    from sqlalchemy import text
    p=practice;source=tmp_path/'fixture.pdf';source.write_bytes(b'%PDF synthetic fixture')
    with p.engine.begin() as connection:
        connection.execute(text("UPDATE students SET curriculum_level_id='00000000-0000-0000-0000-000000000102' WHERE id=:id"),{'id':p.student['student_id']})
    stage(p.engine,UUID(str(p.school)),UUID(p.creator['id']),source,True);publish(p.engine,UUID(str(p.school)))
    student=p.headers(p.student_token);teacher=p.headers(p.teacher_token)
    courses=p.clients['content'].get('/french/review-catalogue',headers=teacher).json()['courses']
    course=next(c for c in courses if c['title']=='Distinguer classe et fonction')
    ids=[course['body']['cm2']['check_exercise_id'],*course['body']['cm2']['practice_exercise_ids']]
    report_path=f"/students/{p.student['student_id']}/course-progress?subject=francais"
    before=p.a.get(report_path,headers=student);assert before.status_code==200,before.text
    row=next(r for r in before.json() if r['lesson_id']==course['id'])
    assert row['status']=='non_commencé' and row['progress_percent']==0 and row['note'] is None
    candidates=[]
    for identifier in ids:
        candidate=p.e.get('/review-version/'+identifier,headers=teacher).json()['candidate'];candidates.append(candidate)
        wrong={part['id']:next(option['id'] for option in part['options'] if option['id']!=candidate['answers'][part['id']]['expected']) for part in candidate['parts']}
        attempt=p.a.post('/attempts',headers=student,json={'session_id':p.learning['id'],'exercise_version_id':identifier,'idempotency_key':str(uuid4())}).json()
        result=p.a.post(f"/attempts/{attempt['id']}/submit",headers=student,json={'answers':wrong});assert result.status_code==200,result.text
    failed=next(r for r in p.a.get(report_path,headers=student).json() if r['lesson_id']==course['id'])
    assert failed['status']=='à_revoir' and failed['note']==0 and failed['progress_percent']==100
    assert failed['adapted_course']['method'] and failed['adapted_course']['worked_example']
    for identifier,candidate in zip(ids,candidates):
        correct={part['id']:candidate['answers'][part['id']]['expected'] for part in candidate['parts']}
        attempt=p.a.post('/attempts',headers=student,json={'session_id':p.learning['id'],'exercise_version_id':identifier,'idempotency_key':str(uuid4())}).json()
        assert p.a.post(f"/attempts/{attempt['id']}/submit",headers=student,json={'answers':correct}).status_code==200
    passed=next(r for r in p.a.get(report_path,headers=student).json() if r['lesson_id']==course['id'])
    assert passed['status']=='passed' and passed['note']==20 and passed['adapted_course'] is None

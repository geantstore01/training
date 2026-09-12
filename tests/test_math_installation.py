from uuid import UUID,uuid4
import pytest
from test_access_integration import lab
from test_pedagogy_integration import pedagogy
from test_exercise_integration import practice
from scripts.stage_math_ateliers import stage

MATH_LEVEL='00000000-0000-0000-0000-000000000102'

@pytest.mark.integration
def test_math_staging_is_idempotent_and_never_publishes(practice,tmp_path):
    p=practice
    source=tmp_path/'synthetic.pdf';source.write_bytes(b'%PDF synthetic math fixture; never a production source')
    result=stage(p.engine,UUID(str(p.school)),UUID(p.creator['id']),source,True)
    assert result['exercises_created']==96
    assert stage(p.engine,UUID(str(p.school)),UUID(p.creator['id']),source,True)['exercises_created']==0
    from sqlalchemy import text
    with p.engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM lesson_versions v JOIN lessons l ON l.id=v.lesson_id WHERE l.slug LIKE 'cm2-math-%' AND v.status='approved'"))==0

@pytest.mark.integration
def test_math_owner_publication_without_fabricated_review(practice,tmp_path):
    from scripts.publish_math_owner import publish
    from sqlalchemy import text
    p=practice;source=tmp_path/'fixture.pdf';source.write_bytes(b'%PDF synthetic fixture')
    stage(p.engine,UUID(str(p.school)),UUID(p.creator['id']),source,True)
    with p.engine.connect() as c:before=c.scalar(text('SELECT count(*) FROM content_reviews WHERE tenant_id=:t'),{'t':p.school})
    result=publish(p.engine,UUID(str(p.school)))
    assert result['lessons']==32 and result['exercises_published']==96
    assert publish(p.engine,UUID(str(p.school)))['exercises_published']==0
    with p.engine.connect() as c:assert c.scalar(text('SELECT count(*) FROM content_reviews WHERE tenant_id=:t'),{'t':p.school})==before
    headers=p.headers(p.student_token)
    availability=p.clients['content'].get('/availability',headers=headers)
    assert availability.status_code==200,availability.text
    assert len(availability.json()['competency_ids'])>=32

@pytest.mark.integration
def test_math_course_report_scores_three_exercises_and_builds_remediation(practice,tmp_path):
    from scripts.publish_math_owner import publish
    from sqlalchemy import text
    p=practice;source=tmp_path/'fixture.pdf';source.write_bytes(b'%PDF synthetic fixture')
    with p.engine.begin() as connection:
        connection.execute(text("UPDATE students SET curriculum_level_id=:level WHERE id=:id"),{'level':MATH_LEVEL,'id':p.student['student_id']})
    stage(p.engine,UUID(str(p.school)),UUID(p.creator['id']),source,True);publish(p.engine,UUID(str(p.school)))
    student=p.headers(p.student_token);teacher=p.headers(p.teacher_token)
    with p.engine.connect() as c:
        competency=str(c.scalar(text("SELECT id FROM competencies WHERE code='CM2-MATH-ENTIERS'")))
    course=p.clients['content'].get(f"/contents?status=approved&kind=lesson&competency_id={competency}&limit=1",headers=student).json()[0]
    lesson=p.clients['content'].get(f"/contents/{course['id']}/versions/{course['version']}",headers=student).json()
    ids=[lesson['body']['cm2']['check_exercise_id'],*lesson['body']['cm2']['practice_exercise_ids']]
    report_path=f"/students/{p.student['student_id']}/course-progress?subject=mathematiques"
    before=p.a.get(report_path,headers=student);assert before.status_code==200,before.text
    assert len(before.json())==32
    row=next(r for r in before.json() if r['lesson_id']==course['id'])
    assert row['status']=='non_commencé' and row['progress_percent']==0 and row['note'] is None
    candidates=[]
    for identifier in ids:
        candidate=p.e.get('/review-version/'+identifier,headers=teacher).json()['candidate'];candidates.append(candidate)
        wrong={part['id']:"0" for part in candidate['parts']}
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

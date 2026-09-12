from uuid import UUID
import pytest
from test_access_integration import lab
from test_pedagogy_integration import pedagogy
from test_exercise_integration import practice
from scripts.stage_french_courses import stage as stage_v1
from scripts.publish_french_owner import publish as publish_v1


def test_deepening_pack_covers_and_enriches_all_lessons():
    from shared.exercises.french_deepening import enriched_courses
    from shared.exercises.french_pack import COURSES
    enriched=enriched_courses()
    assert len(enriched)==28
    for before,after in zip(COURSES,enriched):
        assert before['code']==after['code'] and before['tasks']==after['tasks']
        assert len(after['explanation'])>len(before['explanation'])*2
        assert len(after['method'])>=4 and len(after['worked_example'])>=3 and len(after['common_errors'])>=3
        assert len(after['prerequisites'])>=2


@pytest.mark.integration
def test_deepening_staging_is_idempotent_and_never_publishes(practice,tmp_path):
    from scripts.stage_french_deepening import stage as stage_v2
    from sqlalchemy import text
    p=practice
    source=tmp_path/'synthetic.pdf';source.write_bytes(b'%PDF synthetic fixture; never a production source')
    stage_v1(p.engine,UUID(str(p.school)),UUID(p.creator['id']),source,True)
    publish_v1(p.engine,UUID(str(p.school)))
    preview=stage_v2(p.engine,UUID(str(p.school)),UUID(p.creator['id']))
    assert preview=={'lessons':28,'versions_created':28,'unchanged':0,'publication':'human_review_required'}
    result=stage_v2(p.engine,UUID(str(p.school)),UUID(p.creator['id']),True)
    assert result['versions_created']==28 and result['unchanged']==0
    again=stage_v2(p.engine,UUID(str(p.school)),UUID(p.creator['id']),True)
    assert again['versions_created']==0 and again['unchanged']==28
    with p.engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM lesson_versions v JOIN lessons l ON l.id=v.lesson_id WHERE v.tenant_id=CAST(:t AS uuid) AND l.slug LIKE 'cm2-fr-%-atelier-francais' AND v.status='pending_review'"),{'t':str(p.school)})==28
        assert c.scalar(text("SELECT count(*) FROM lesson_versions v JOIN lessons l ON l.id=v.lesson_id WHERE v.tenant_id=CAST(:t AS uuid) AND l.slug LIKE 'cm2-fr-%-atelier-francais' AND v.status='approved'"),{'t':str(p.school)})==28
        shallow=c.scalar(text("SELECT v.body['cm2']['explanation'] FROM lesson_versions v JOIN lessons l ON l.id=v.lesson_id WHERE v.tenant_id=CAST(:t AS uuid) AND l.slug='cm2-fr-natures-atelier-francais' AND v.version=1"),{'t':str(p.school)})
        deep=c.scalar(text("SELECT v.body['cm2']['explanation'] FROM lesson_versions v JOIN lessons l ON l.id=v.lesson_id WHERE v.tenant_id=CAST(:t AS uuid) AND l.slug='cm2-fr-natures-atelier-francais' AND v.version=2"),{'t':str(p.school)})
        assert len(deep)>len(shallow)*2


@pytest.mark.integration
def test_deepening_publication_archives_v1_and_serves_v2(practice,tmp_path):
    from scripts.stage_french_deepening import stage as stage_v2
    from scripts.publish_french_deepening import publish as publish_v2
    from sqlalchemy import text
    p=practice
    source=tmp_path/'synthetic.pdf';source.write_bytes(b'%PDF synthetic fixture')
    with p.engine.begin() as connection:
        connection.execute(text("UPDATE students SET curriculum_level_id='00000000-0000-0000-0000-000000000102' WHERE id=:id"),{'id':p.student['student_id']})
    stage_v1(p.engine,UUID(str(p.school)),UUID(p.creator['id']),source,True)
    publish_v1(p.engine,UUID(str(p.school)))
    stage_v2(p.engine,UUID(str(p.school)),UUID(p.creator['id']),True)
    with p.engine.connect() as c:before=c.scalar(text('SELECT count(*) FROM content_reviews WHERE tenant_id=:t'),{'t':p.school})
    result=publish_v2(p.engine,UUID(str(p.school)))
    assert result['lessons_published']==28
    assert publish_v2(p.engine,UUID(str(p.school)))['lessons_published']==0
    with p.engine.connect() as c:
        assert c.scalar(text('SELECT count(*) FROM content_reviews WHERE tenant_id=:t'),{'t':p.school})==before
        rows=c.execute(text("SELECT l.slug,max(v.version) FILTER (WHERE v.status='approved') AS approved,max(v.version) FILTER (WHERE v.status='archived') AS archived,count(*) FILTER (WHERE v.status='approved') AS n FROM lesson_versions v JOIN lessons l ON l.id=v.lesson_id WHERE v.tenant_id=CAST(:t AS uuid) AND l.slug LIKE 'cm2-fr-%-atelier-francais' GROUP BY l.slug"),{'t':str(p.school)}).all()
        assert len(rows)==28
        for slug,approved,archived,n in rows:
            assert approved==2 and archived==1 and n==1,(slug,approved,archived,n)
        assert c.scalar(text("SELECT count(*) FROM lesson_versions v JOIN lessons l ON l.id=v.lesson_id WHERE v.tenant_id=CAST(:t AS uuid) AND l.slug LIKE 'cm2-fr-%-atelier-francais' AND v.status='approved' AND v.published_at IS NULL"),{'t':str(p.school)})==0
    student=p.headers(p.student_token)
    with p.engine.connect() as c:competency=str(c.scalar(text("SELECT id FROM competencies WHERE code='CM2-FR-NATURES' AND programme_version='programme-2025-cm2-2026'")))
    course=p.clients['content'].get(f"/contents?status=approved&kind=lesson&competency_id={competency}&limit=1",headers=student).json()[0]
    assert course['version']==2
    lesson=p.clients['content'].get(f"/contents/{course['id']}/versions/{course['version']}",headers=student).json()
    body=lesson['body']['cm2']
    assert body['subject']=='francais' and len(body['method'])>=4 and len(body['common_errors'])>=3
    assert 'catégorie' in body['explanation']
    assert 'answer_spec' not in lesson and 'candidate' not in lesson

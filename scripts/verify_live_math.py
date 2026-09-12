"""Vérification HTTP en lecture seule ; identifiants fournis sur stdin, jamais enregistrés."""
import json,sys
import httpx
credentials=json.load(sys.stdin)
base='https://boostclasse.com'
parent=next(c for c in credentials if c['login']=='parent.demo')
student_id='c35533af-25ca-4420-8895-4ddba1194ecb'
with httpx.Client(base_url=base,headers={'Origin':base},timeout=30) as client:
    r=client.get('/api/health');assert r.status_code==200,r.text
    r=client.post('/api/session',json={**parent,'level':'CM2'});assert r.status_code==200,r.text
    redirect=r.json().get('redirect')
    r=client.get(f'/api/assessment/students/{student_id}/course-progress',params={'subject':'mathematiques'})
    assert r.status_code==200,r.text
    rows=r.json();assert len(rows)==32,f"attendu 32 cours de maths, obtenu {len(rows)}"
    assert all(row['status']=='non_commencé' and row['progress_percent']==0 and row['note'] is None for row in rows)
    assert all(row['total_exercises']==3 for row in rows)
    r=client.get(f'/api/assessment/students/{student_id}/course-progress',params={'subject':'francais'})
    assert r.status_code==200,r.text
    french=r.json();assert len(french)==28,f"attendu 28 cours de français, obtenu {len(french)}"
    lesson=rows[0]
    for version in (2,1):
        r=client.get(f"/api/content/contents/{lesson['lesson_id']}/versions/{version}")
        if r.status_code==200: break
    content_status=r.status_code
    exercise_status=None
    if content_status==200:
        body=r.json()['body']['cm2']
        assert body['explanation'] and body['worked_example'] and body['method']
        r=client.get('/api/exercise/published/'+body['check_exercise_id']);exercise_status=r.status_code
        if exercise_status==200:
            exercise=r.json();assert exercise['prompt']['parts'] and 'answer_spec' not in exercise and 'candidate' not in exercise
    client.delete('/api/session')
    print(f"32 cours de maths (3 exercices chacun) et 28 cours de français suivis pour l'élève ; redirection parent={redirect} ; contenu={content_status}, exercice={exercise_status}.")

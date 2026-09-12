"""Read-only HTTP verification; credentials supplied over stdin, never saved."""
import json,sys,time
import httpx
credentials=json.load(sys.stdin)
base='https://boostclasse.com'
with httpx.Client(base_url=base,headers={'Origin':base},timeout=30) as client:
    def login(name):
        credential=next(c for c in credentials if c['login']==name)
        r=client.post('/api/session',json={**credential,'level':'CM2'});assert r.status_code==200,r.text
        return r.json()
    assert login('admin')['redirect']=='/administration'
    r=client.get('/api/content/french/review-catalogue')
    assert r.status_code==200,r.text
    courses=r.json()['courses'];assert len(courses)==28
    assert all(c['status']=='approved' for c in courses)
    client.delete('/api/session');assert login('eleve1')['redirect']=='/eleve'
    count=0
    for course in courses:
        r=client.get(f"/api/content/contents/{course['id']}/versions/1");assert r.status_code==200,(course['title'],r.status_code)
        lesson=r.json()['body']['cm2'];assert lesson['explanation'] and lesson['worked_example']
        for identifier in [lesson['check_exercise_id'],*lesson['practice_exercise_ids']]:
            time.sleep(.12)
            r=client.get('/api/exercise/published/'+identifier);assert r.status_code==200,r.text
            exercise=r.json();assert exercise['prompt']['parts'] and 'answer_spec' not in exercise and 'candidate' not in exercise
            count+=1
    client.delete('/api/session')
    print(f'{len(courses)} cours et {count} exercices ouverts avec le compte élève ; réponses privées absentes.')

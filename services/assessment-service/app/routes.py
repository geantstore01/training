from datetime import datetime,timedelta,timezone
from decimal import Decimal
import hashlib,hmac,json
from uuid import UUID,uuid4
from fastapi import APIRouter,Depends,HTTPException,Query,Request
from sqlalchemy import func,select,text
from shared.db.models import (Answer,Competency,ExerciseAttempt,ExerciseVersion,ExerciseSource,Hint,LearningSession,
    Lesson,LessonCompetency,LessonVersion,MasteryEvidence,MasteryRecord,SpacedRepetitionItem,Student,Subject)
from shared.db.session import tenant_session
from shared.security.api import current_principal,enforce_rate,require_roles
from shared.security.policy import accessible_student,audit
from shared.security.tokens import Principal
from shared.exercises.schemas import Candidate,Responses
from shared.exercises.correctors import VERSION as CORRECTOR_VERSION,grade
from shared.exercises.coaching import correction, diagnose
from .algorithms import PRIOR,VERSION,Schedule,bkt,mastery_level,schedule
from .schemas import (AdaptiveCourse,AttemptInput,AttemptView,AttemptDetail,SessionView,HintView,Result,Feedback,
    Progress,ErrorPattern,CourseProgress,CorrectionPart,NextExercise,CorrectionRequest)

router=APIRouter(tags=["assessment"])
LEARNER=require_roles("student")
MESSAGES={"MISSING_ANSWER":"Tu peux reprendre cette partie tranquillement.",
    "HUMAN_REVIEW":"Ton texte est enregistré. Il doit être relu avec ton enseignant ; aucune erreur n'est déduite automatiquement.",
    "DICTATION_ERROR":"Relis ta phrase en vérifiant les accords, les verbes et les mots appris.",
    "INVALID_FORMAT":"Vérifie la forme de ta réponse.","INVALID_NUMBER":"Écris un nombre ou un calcul simple.",
    "CALCULATION_ERROR":"Reprends le calcul une étape à la fois.","CHOICE_ERROR":"Relis les propositions.",
    "ORDER_ERROR":"Vérifie l’ordre des éléments.","ACCENT_ERROR":"Observe les accents.",
    "SPELLING_ERROR":"Vérifie l’orthographe du mot.","AGREEMENT_ERROR":"Observe les mots qui doivent s’accorder.",
    "CONJUGATION_ERROR":"Repère le sujet et la forme du verbe.","GRAMMAR_ERROR":"Relis la règle travaillée.",
    "FORMULATION_NOT_RECOGNIZED":"Cette formulation n’est pas prévue par le correcteur. Demande à ton enseignant de la vérifier."}

def own_student(session,principal,lock=False):
    q=select(Student).where(Student.user_id==principal.user_id)
    if lock:
        # Serialize the learner's assessment writes without granting UPDATE on their profile.
        session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
            {"key":f"assessment:{principal.school_id}:{principal.user_id}"})
    student=session.scalar(q)
    if student is None: raise HTTPException(403,"Profil élève requis.")
    return student

def attempt_view(a):
    return AttemptView(id=a.id,session_id=a.session_id,exercise_version_id=a.exercise_version_id,
        started_at=a.started_at,submitted_at=a.submitted_at,result=a.assessment_result)

def attempt_for_write(session,principal,identifier):
    student=own_student(session,principal,True)
    a=session.scalar(select(ExerciseAttempt).where(ExerciseAttempt.id==identifier,ExerciseAttempt.student_id==student.id).with_for_update())
    if a is None: raise HTTPException(404,"Tentative introuvable.")
    return student,a

def candidate(session,v):
    if v.validator_name!="controlled" or v.validator_version!=CORRECTOR_VERSION:
        raise HTTPException(409,"Correcteur de cette version indisponible.")
    return Candidate(kind=v.kind,instruction=v.prompt["instruction"],parts=v.prompt["parts"],answers=v.answer_spec,
        source_ids=list(session.scalars(select(ExerciseSource.source_id).where(ExerciseSource.exercise_version_id==v.id))),difficulty=v.difficulty)

@router.post("/sessions",response_model=SessionView,status_code=201)
def start_session(request:Request,principal:Principal=Depends(LEARNER)):
    enforce_rate(request,"session",principal.user_id,10)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        student=own_student(session,principal,True)
        active=session.scalar(select(LearningSession).where(LearningSession.student_id==student.id,LearningSession.status=="active").order_by(LearningSession.started_at.desc()).limit(1))
        if active: return SessionView.model_validate(active)
        item=LearningSession(tenant_id=principal.school_id,student_id=student.id)
        session.add(item);session.flush();audit(session,principal,"assessment.session_started","learning_session",item.id)
        return SessionView.model_validate(item)

@router.post("/sessions/{session_id}/complete",response_model=SessionView)
def finish_session(session_id:UUID,request:Request,principal:Principal=Depends(LEARNER)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        student=own_student(session,principal,True)
        item=session.scalar(select(LearningSession).where(LearningSession.id==session_id,LearningSession.student_id==student.id).with_for_update())
        if item is None: raise HTTPException(404,"Session introuvable.")
        if item.status=="active":
            item.status="completed";item.ended_at=datetime.now(timezone.utc);session.flush()
            audit(session,principal,"assessment.session_completed","learning_session",item.id)
        return SessionView.model_validate(item)

@router.post("/attempts",response_model=AttemptView,status_code=201)
def start_attempt(payload:AttemptInput,request:Request,principal:Principal=Depends(LEARNER)):
    enforce_rate(request,"attempt",principal.user_id,30)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        student=own_student(session,principal,True)
        existing=session.scalar(select(ExerciseAttempt).where(ExerciseAttempt.idempotency_key==payload.idempotency_key))
        if existing:
            if (existing.student_id,existing.session_id,existing.exercise_version_id)!=(student.id,payload.session_id,payload.exercise_version_id):
                raise HTTPException(409,"Clé d’idempotence déjà utilisée.")
            return attempt_view(existing)
        learning=session.scalar(select(LearningSession).where(LearningSession.id==payload.session_id,LearningSession.student_id==student.id,LearningSession.status=="active"))
        if learning is None: raise HTTPException(404,"Session active introuvable.")
        v=session.scalar(select(ExerciseVersion).where(ExerciseVersion.id==payload.exercise_version_id,ExerciseVersion.status=="published"))
        if v is None: raise HTTPException(404,"Exercice publié introuvable.")
        candidate(session,v)
        a=ExerciseAttempt(tenant_id=principal.school_id,student_id=student.id,session_id=learning.id,
            exercise_version_id=v.id,idempotency_key=payload.idempotency_key)
        session.add(a);session.flush();audit(session,principal,"assessment.attempt_started","exercise_attempt",a.id)
        return attempt_view(a)

@router.get("/attempts/{attempt_id}/hints/{level}",response_model=HintView)
def hint(attempt_id:UUID,level:int,request:Request,principal:Principal=Depends(LEARNER)):
    if not 1<=level<=6: raise HTTPException(422,"Niveau d’aide invalide.")
    enforce_rate(request,"hint",principal.user_id,30)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        student,a=attempt_for_write(session,principal,attempt_id)
        if a.submitted_at: raise HTTPException(409,"Cet essai est terminé. Tu peux consulter la correction ou recommencer avec les indices.")
        from shared.school import tutor_limit
        if level > tutor_limit(session, student.id):raise HTTPException(403,"Niveau d’aide limité par l’enseignant.")
        if level > a.max_hint_level + 1: raise HTTPException(409,"Lis d'abord l'indice précédent.")
        h=session.scalar(select(Hint).where(Hint.exercise_version_id==a.exercise_version_id,Hint.level==level))
        if h is None: raise HTTPException(404,"Aide indisponible.")
        a.max_hint_level=max(a.max_hint_level,level);session.flush()
        audit(session,principal,"assessment.hint_used","exercise_attempt",a.id)
        return HintView(level=level,text=h.body["text"])

def update_mastery(session,student,a,c,results,now):
    progress=[]
    for competency_id in sorted({p.competency_id for p in c.parts},key=str):
        part_ids={p.id for p in c.parts if p.competency_id==competency_id}
        relevant=[r for r in results if r.part_id in part_ids]
        correct=all(r.correct for r in relevant)
        old=session.scalar(select(MasteryRecord).where(MasteryRecord.student_id==student.id,MasteryRecord.competency_id==competency_id).with_for_update())
        previous=float(old.probability) if old else PRIOR
        repeated=session.scalar(select(MasteryEvidence.id).where(MasteryEvidence.student_id==student.id,MasteryEvidence.competency_id==competency_id,
            MasteryEvidence.exercise_version_id==a.exercise_version_id,MasteryEvidence.created_at>now-timedelta(hours=20)).limit(1))
        reason="assisted" if a.max_hint_level else "repeated" if repeated else "independent"
        # Unknown free formulations are not evidence that the learner lacks a skill.
        if any(r.error_code in {"FORMULATION_NOT_RECOGNIZED","HUMAN_REVIEW"} for r in relevant): reason="unrecognized"
        applied=reason=="independent"
        elapsed=(now-old.last_assessed_at).total_seconds()/86400 if old and old.last_assessed_at else 0
        posterior=bkt(previous,correct,max(0,elapsed)) if applied else previous
        item=session.scalar(select(SpacedRepetitionItem).where(SpacedRepetitionItem.student_id==student.id,SpacedRepetitionItem.competency_id==competency_id).with_for_update())
        previous_schedule=Schedule(item.due_at,item.interval_days,item.ease_factor,item.repetitions) if item else None
        next_schedule=schedule(now,correct and reason not in {"assisted","unrecognized"},previous_schedule) if applied or not item or reason in {"assisted","unrecognized"} else previous_schedule
        if reason=="unrecognized" and previous_schedule is not None:next_schedule=previous_schedule
        if item is None:
            item=SpacedRepetitionItem(tenant_id=student.tenant_id,student_id=student.id,competency_id=competency_id,algorithm_version=VERSION)
            session.add(item)
        item.due_at=next_schedule.due_at;item.interval_days=next_schedule.interval_days
        item.ease_factor=next_schedule.ease_factor;item.repetitions=next_schedule.repetitions
        if old is None:
            old=MasteryRecord(tenant_id=student.tenant_id,student_id=student.id,competency_id=competency_id,
                probability=Decimal(str(PRIOR)),evidence_count=0,algorithm_version=VERSION)
            session.add(old)
        if applied:
            old.probability=Decimal(str(posterior));old.evidence_count+=1;old.last_assessed_at=now;old.algorithm_version=VERSION
        old.evaluation_level=mastery_level(float(old.probability),old.evidence_count,item.repetitions).value
        session.add(MasteryEvidence(tenant_id=student.tenant_id,attempt_id=a.id,student_id=student.id,exercise_version_id=a.exercise_version_id,
            competency_id=competency_id,applied=applied,correct=correct,reason=reason,probability_before=Decimal(str(previous)),
            probability_after=Decimal(str(posterior)),algorithm_version=VERSION,created_at=now))
        progress.append(Progress(competency_id=competency_id,level=old.evaluation_level,next_review_at=item.due_at))
    return progress

@router.post("/attempts/{attempt_id}/submit",response_model=AttemptView)
def submit(attempt_id:UUID,payload:Responses,request:Request,principal:Principal=Depends(LEARNER)):
    enforce_rate(request,"submit",principal.user_id,30)
    raw=json.dumps(payload.model_dump(exclude_defaults=True),sort_keys=True,ensure_ascii=False,separators=(",",":"))
    digest=hmac.new(request.app.state.rate_key,raw.encode(),hashlib.sha256).hexdigest()
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        student,a=attempt_for_write(session,principal,attempt_id)
        if a.submitted_at:
            if not hmac.compare_digest(a.submission_digest or "",digest): raise HTTPException(409,"Tentative déjà soumise avec une autre réponse.")
            return attempt_view(a)
        learning=session.get(LearningSession,a.session_id)
        if learning.status!="active": raise HTTPException(409,"Session terminée.")
        c=candidate(session,session.get(ExerciseVersion,a.exercise_version_id))
        if not set(payload.reasoning) <= {part.id for part in c.parts}:
            raise HTTPException(422,"Partie inconnue dans la démarche.")
        if not any(isinstance(value,str) and value.strip() or isinstance(value,list) and value for value in payload.answers.values()):
            raise HTTPException(422,"Écris une première réponse avant de vérifier ton travail.")
        try: results=grade(c,payload.answers)
        except ValueError: raise HTTPException(422,"Partie inconnue.") from None
        now=datetime.now(timezone.utc)
        progress=update_mastery(session,student,a,c,results,now)
        for r in results:
            session.add(Answer(tenant_id=principal.school_id,attempt_id=a.id,part_key=r.part_id,
                response_ciphertext=request.app.state.cipher.encrypt({"response":payload.answers.get(r.part_id,""),"reasoning":payload.reasoning.get(r.part_id,"")},
                    school_id=principal.school_id,owner_id=a.id,purpose="answer:"+r.part_id),
                is_correct=None if r.error_code in {"HUMAN_REVIEW","FORMULATION_NOT_RECOGNIZED"} else r.correct,feedback_code=r.error_code))
        a.submitted_at=now;a.submission_digest=digest
        scored=[r for r in results if r.error_code not in {"HUMAN_REVIEW","FORMULATION_NOT_RECOGNIZED"}]
        a.score=Decimal(sum(r.correct for r in scored))/len(scored) if scored else None
        feedback=[]
        for r in results:
            diagnosis=diagnose(c.answers[r.part_id],payload.answers.get(r.part_id)) if not r.correct else None
            from shared.exercises.french import dictation_feedback
            dictation=dictation_feedback(c.answers[r.part_id],payload.answers.get(r.part_id, "")) if c.answers[r.part_id].mode=="dictation" and not r.correct and isinstance(payload.answers.get(r.part_id,""),str) else None
            if dictation:diagnosis={"message":dictation["message"],"category":None}
            feedback.append(Feedback(part_id=r.part_id,outcome="réussi" if r.correct else "à_relire" if r.error_code in {"HUMAN_REVIEW","FORMULATION_NOT_RECOGNIZED"} else "à_revoir",error_code=r.error_code,
                message="Tu as réussi cette étape. Peux-tu expliquer ta méthode ?" if r.correct else diagnosis["message"] if diagnosis else MESSAGES[r.error_code],
                misconception=diagnosis["category"] if diagnosis else None,categories=dictation["categories"] if dictation else []))
        a.assessment_result=Result(feedback=feedback,progress=progress,
            message="Chaque essai t’aide à apprendre. Tu peux reprendre les étapes à ton rythme.").model_dump(mode="json")
        session.flush();audit(session,principal,"assessment.attempt_submitted","exercise_attempt",a.id)
        return attempt_view(a)

@router.get("/attempts/{attempt_id}/correction",response_model=list[CorrectionPart])
def detailed_correction(attempt_id:UUID,request:Request,principal:Principal=Depends(LEARNER)):
    enforce_rate(request,"correction",principal.user_id,30)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        _,a=attempt_for_write(session,principal,attempt_id)
        if not a.submitted_at:
            raise HTTPException(409,"Essaie d'abord l'exercice avant de lire la correction.")
        attempted=set()
        for row in session.scalars(select(Answer).where(Answer.attempt_id==a.id)):
            value=request.app.state.cipher.decrypt(row.response_ciphertext,school_id=principal.school_id,owner_id=a.id,purpose="answer:"+row.part_key)["response"]
            if isinstance(value,str) and value.strip() or isinstance(value,list) and value:
                attempted.add(row.part_key)
        c=candidate(session,session.get(ExerciseVersion,a.exercise_version_id))
        audit(session,principal,"assessment.correction_read","exercise_attempt",a.id)
        return correction(c,attempted)

@router.post("/attempts/{attempt_id}/correction",response_model=list[CorrectionPart])
def requested_correction(attempt_id:UUID,body:CorrectionRequest,request:Request,principal:Principal=Depends(LEARNER)):
    from shared.db.models import ExerciseCompetency, Competency, Subject, CurriculumLevel
    enforce_rate(request,"correction",principal.user_id,30)
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        _,a=attempt_for_write(session,principal,attempt_id)
        contexts=session.execute(select(Subject.code,CurriculumLevel.code).select_from(ExerciseCompetency)
            .join(Competency,Competency.id==ExerciseCompetency.competency_id)
            .join(Subject,Subject.id==Competency.subject_id)
            .join(CurriculumLevel,CurriculumLevel.id==Competency.curriculum_level_id)
            .where(ExerciseCompetency.exercise_version_id==a.exercise_version_id)).all()
        if not contexts or any(tuple(row) not in {("francais","CM2"),("mathematiques","CM2"),("sciences","CM2"),("histoire","CM2")} for row in contexts):
            raise HTTPException(409,"La correction sur demande est réservée aux parcours de français, de mathématiques, de sciences et d’histoire CM2.")
        c=candidate(session,session.get(ExerciseVersion,a.exercise_version_id))
        if not a.submitted_at:a.max_hint_level=max(1,a.max_hint_level)
        audit(session,principal,"assessment.correction_requested","exercise_attempt",a.id)
        return correction(c,set(c.answers))

@router.get("/attempts/{attempt_id}/next",response_model=NextExercise)
def next_exercise(attempt_id:UUID,request:Request,principal:Principal=Depends(LEARNER)):
    from shared.db.models import ExerciseCompetency
    from shared.exercises.adaptive import choose_next
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        student,a=attempt_for_write(session,principal,attempt_id)
        if not a.submitted_at: raise HTTPException(409,"Termine d'abord ton essai.")
        current=session.get(ExerciseVersion,a.exercise_version_id)
        skills=set(session.scalars(select(ExerciseCompetency.competency_id).where(ExerciseCompetency.exercise_version_id==current.id)))
        # The candidate must teach exactly the same competencies; no inferred new curriculum.
        linked=select(ExerciseCompetency.exercise_version_id).where(ExerciseCompetency.competency_id.in_(skills))
        rows=session.scalars(select(ExerciseVersion).where(ExerciseVersion.id.in_(linked),ExerciseVersion.status=="published",
            ExerciseVersion.validator_name=="controlled",ExerciseVersion.validator_version==CORRECTOR_VERSION)).all()
        candidates=[]
        for row in rows:
            row_skills=set(session.scalars(select(ExerciseCompetency.competency_id).where(ExerciseCompetency.exercise_version_id==row.id)))
            if row_skills==skills: candidates.append({"id":row.id,"difficulty":row.difficulty})
        seen=set(session.scalars(select(ExerciseAttempt.exercise_version_id).where(ExerciseAttempt.student_id==student.id)
            .order_by(ExerciseAttempt.started_at.desc(),ExerciseAttempt.id).limit(20)))
        seen.add(current.id)
        review=all(f["outcome"]=="à_relire" for f in (a.assessment_result or {}).get("feedback",[]))
        return choose_next(candidates,seen,current.difficulty,a.score==1 or review,bool(a.max_hint_level) or review)

@router.get("/attempts/{attempt_id}",response_model=AttemptDetail)
def detail(attempt_id:UUID,request:Request,principal:Principal=Depends(current_principal)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        a=session.get(ExerciseAttempt,attempt_id)
        if a is None: raise HTTPException(404,"Tentative introuvable.")
        accessible_student(session,principal,a.student_id)
        decoded={r.part_key:request.app.state.cipher.decrypt(r.response_ciphertext,school_id=principal.school_id,owner_id=a.id,purpose="answer:"+r.part_key)
            for r in session.scalars(select(Answer).where(Answer.attempt_id==a.id))}
        audit(session,principal,"assessment.responses_read","exercise_attempt",a.id)
        return AttemptDetail(**attempt_view(a).model_dump(),responses={key:value["response"] for key,value in decoded.items()},
            reasoning={key:value.get("reasoning","") for key,value in decoded.items()},
            prompt=session.get(ExerciseVersion,a.exercise_version_id).prompt)

@router.get("/students/{student_id}/attempts",response_model=list[AttemptView])
def history(student_id:UUID,request:Request,limit:int=Query(30,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),principal:Principal=Depends(current_principal)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        accessible_student(session,principal,student_id)
        return [attempt_view(a) for a in session.scalars(select(ExerciseAttempt).where(ExerciseAttempt.student_id==student_id).order_by(ExerciseAttempt.started_at.desc(),ExerciseAttempt.id).limit(limit).offset(offset))]

@router.get("/students/{student_id}/mastery",response_model=list[Progress])
def mastery(student_id:UUID,request:Request,due_only:bool=False,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),principal:Principal=Depends(current_principal)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        accessible_student(session,principal,student_id)
        q=select(MasteryRecord,SpacedRepetitionItem).join(SpacedRepetitionItem,
            (SpacedRepetitionItem.student_id==MasteryRecord.student_id)&(SpacedRepetitionItem.competency_id==MasteryRecord.competency_id)).where(MasteryRecord.student_id==student_id)
        if due_only: q=q.where(SpacedRepetitionItem.due_at<=datetime.now(timezone.utc))
        return [Progress(competency_id=m.competency_id,level=m.evaluation_level,next_review_at=s.due_at)
            for m,s in session.execute(q.order_by(SpacedRepetitionItem.due_at,MasteryRecord.competency_id).limit(limit).offset(offset))]

COURSE_SLUGS={"francais":"cm2-fr-%-atelier-francais","mathematiques":"cm2-math-%"}

@router.get("/students/{student_id}/course-progress",response_model=list[CourseProgress])
def course_progress(student_id:UUID,request:Request,subject:str=Query("francais",pattern="^(francais|mathematiques)$"),principal:Principal=Depends(current_principal)):
    """Build the learner's course report from the latest submitted test attempt for each authored exercise."""
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        student=accessible_student(session,principal,student_id)
        rows=session.execute(select(Lesson,LessonVersion,Competency,Subject).select_from(Lesson)
            .join(LessonVersion,LessonVersion.lesson_id==Lesson.id)
            .join(LessonCompetency,LessonCompetency.lesson_version_id==LessonVersion.id)
            .join(Competency,Competency.id==LessonCompetency.competency_id)
            .join(Subject,Subject.id==Competency.subject_id)
            .where(LessonVersion.status=="approved",Subject.code==subject,
                Competency.curriculum_level_id==student.curriculum_level_id,
                Lesson.slug.like(COURSE_SLUGS[subject]))
            .order_by(LessonVersion.title,Lesson.id)).all()
        courses=[]
        exercise_ids=[]
        for lesson,version,competency,course_subject in rows:
            cm2=(version.body or {}).get("cm2") or {}
            ids=[cm2.get("check_exercise_id"),*(cm2.get("practice_exercise_ids") or [])]
            ids=[UUID(value) if isinstance(value,str) else value for value in ids if value]
            if not ids: continue
            courses.append((lesson,version,competency,course_subject,cm2,ids))
            exercise_ids.extend(ids)
        attempts=session.scalars(select(ExerciseAttempt).where(ExerciseAttempt.student_id==student_id,
            ExerciseAttempt.exercise_version_id.in_(set(exercise_ids)),ExerciseAttempt.submitted_at.is_not(None))
            .order_by(ExerciseAttempt.exercise_version_id,ExerciseAttempt.submitted_at.desc(),ExerciseAttempt.id.desc())).all() if exercise_ids else []
        latest={}
        for attempt in attempts: latest.setdefault(attempt.exercise_version_id,attempt)
        output=[]
        for lesson,version,competency,course_subject,cm2,ids in courses:
            completed=[latest[id] for id in ids if id in latest]
            note=None;adapted=None;help_used=any(a.max_hint_level>0 for a in completed)
            if not completed: status="non_commencé"
            elif len(completed)<len(ids): status="en_cours"
            elif any(a.score is None for a in completed): status="à_relire"
            else:
                average=sum(float(a.score) for a in completed)/len(completed)
                note=round(average*20,1)
                status="passed" if average>=0.70 else "à_revoir"
                if status=="à_revoir":
                    failed=[a for a in completed if a.score is not None and float(a.score)<1]
                    codes=list(dict.fromkeys(session.scalars(select(Answer.feedback_code).where(
                        Answer.attempt_id.in_([a.id for a in failed]),Answer.is_correct.is_(False))).all())) if failed else []
                    focus=MESSAGES.get(codes[0],f"Reprendre la méthode de « {version.title} ».") if codes else f"Reprendre la méthode de « {version.title} »."
                    adapted=AdaptiveCourse(title=f"Ton cours adapté : {version.title}",focus=focus,
                        explanation=cm2.get("explanation",version.body.get("summary","")),method=cm2.get("method",[]),
                        worked_example=cm2.get("worked_example",[]),exercise_version_id=failed[0].exercise_version_id if failed else ids[0])
            output.append(CourseProgress(lesson_id=lesson.id,competency_id=competency.id,title=version.title,
                subject=course_subject.code,completed_exercises=len(completed),total_exercises=len(ids),
                progress_percent=round(len(completed)*100/len(ids)),status=status,note=note,
                last_attempt_at=max((a.submitted_at for a in completed),default=None),help_used=help_used,adapted_course=adapted))
        return output

@router.get("/students/{student_id}/errors",response_model=list[ErrorPattern])
def errors(student_id:UUID,request:Request,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),principal:Principal=Depends(current_principal)):
    with tenant_session(request.app.state.engine,principal.school_id) as session:
        accessible_student(session,principal,student_id)
        # Match each part's own competency, not every competency attached to its exercise.
        from sqlalchemy import text
        rows=session.execute(text("""SELECT (p.value->>'competency_id')::uuid competency_id,a.feedback_code,count(*) occurrences
          FROM answers a JOIN exercise_attempts t ON (t.tenant_id,t.id)=(a.tenant_id,a.attempt_id)
          JOIN exercise_versions v ON (v.tenant_id,v.id)=(t.tenant_id,t.exercise_version_id)
          CROSS JOIN LATERAL jsonb_array_elements(v.prompt->'parts') p(value)
          WHERE t.student_id=:student AND a.is_correct=false AND p.value->>'id'=a.part_key
          AND a.feedback_code NOT IN ('HUMAN_REVIEW','FORMULATION_NOT_RECOGNIZED')
          GROUP BY competency_id,a.feedback_code ORDER BY count(*) DESC,competency_id,a.feedback_code LIMIT :limit OFFSET :offset"""),
            {"student":student_id,"limit":limit,"offset":offset}).all()
        return [ErrorPattern(competency_id=r.competency_id,error_code=r.feedback_code,recurring=r.occurrences>=2,
            message=MESSAGES.get(r.feedback_code,"Reprends cette étape avec ton enseignant.")) for r in rows]

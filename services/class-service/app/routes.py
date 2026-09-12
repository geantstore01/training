from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import Field
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, or_, delete
from shared.ai.contracts import Strict
from shared.db.models import (Class,Teacher,TeacherClass,Student,Enrollment,LearningGroup,GroupMember,Mission,MissionExercise,ExerciseVersion,CurriculumLevel,ExerciseCompetency,Competency)
from shared.db.session import tenant_session
from shared.school import class_access, active_enrollment, flag
from shared.security.api import current_principal, require_roles, enforce_rate
from shared.security.policy import audit

router=APIRouter()
staff=require_roles("teacher","school_admin","sys_admin")

class ClassInput(Strict):
    name: str=Field(min_length=1,max_length=80)
    academic_year: int=Field(ge=2020,le=2200)
    level: Literal["CM1","CM2"]
    teacher_id: UUID
class ClassView(Strict):
    id: UUID
    name: str
    academic_year: int
class EnrollmentInput(Strict):
    student_id: UUID
class GroupInput(Strict):
    name: str=Field(min_length=1,max_length=80)
    student_ids: list[UUID]=Field(min_length=1,max_length=40)
class GroupView(Strict):
    id: UUID
    name: str
    student_ids: list[UUID]
class MissionInput(Strict):
    title: str=Field(min_length=1,max_length=160)
    day: date
    group_id: UUID|None=None
    exercise_version_ids: list[UUID]=Field(min_length=1,max_length=12)
class MissionView(MissionInput):
    id: UUID
    class_id: UUID
    status: Literal["published","archived"]="published"
class StudentView(Strict):
    id: UUID
    pseudonym: str

@router.post("/classes",response_model=ClassView,status_code=201)
def create(body:ClassInput,request:Request,p=Depends(staff)):
    enforce_rate(request,"create",p.user_id,15)
    with tenant_session(request.app.state.engine,p.school_id) as s:
        teacher=s.get(Teacher,body.teacher_id)
        if not teacher or (not p.roles & {"school_admin","sys_admin"} and teacher.user_id!=p.user_id):
            raise HTTPException(403,"Enseignant autorisé requis.")
        row=Class(tenant_id=p.school_id,school_id=p.school_id,name=body.name,academic_year=body.academic_year,
            curriculum_level_id=s.scalar(select(CurriculumLevel.id).where(CurriculumLevel.code==body.level)))
        s.add(row);s.flush()
        s.add(TeacherClass(tenant_id=p.school_id,teacher_id=teacher.id,class_id=row.id))
        audit(s,p,"class.created","class",row.id)
        return ClassView(id=row.id,name=row.name,academic_year=row.academic_year)

@router.get("/classes",response_model=list[ClassView])
def listing(request:Request,p=Depends(staff)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        q=select(Class)
        if not p.roles & {"school_admin","sys_admin"}:
            q=q.join(TeacherClass,TeacherClass.class_id==Class.id).join(Teacher,Teacher.id==TeacherClass.teacher_id).where(Teacher.user_id==p.user_id)
        return [ClassView(id=x.id,name=x.name,academic_year=x.academic_year) for x in s.scalars(q.order_by(Class.name).limit(100))]

@router.post("/classes/{id}/students",response_model=StudentView)
def enroll(id:UUID,body:EnrollmentInput,request:Request,p=Depends(staff)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        cls=class_access(s,p,id);student=s.get(Student,body.student_id)
        if not student or student.curriculum_level_id!=cls.curriculum_level_id:
            raise HTTPException(422,"Élève du niveau de la classe requis.")
        if not s.scalar(active_enrollment(student.id,id)):
            s.add(Enrollment(tenant_id=p.school_id,class_id=id,student_id=student.id,starts_on=date.today()))
        audit(s,p,"class.enrolled","student",student.id)
        return StudentView(id=student.id,pseudonym=student.pseudonym)

@router.delete("/classes/{id}/students/{student_id}",status_code=204)
def unenroll(id:UUID,student_id:UUID,request:Request,p=Depends(staff)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        class_access(s,p,id)
        rows=s.scalars(active_enrollment(student_id,id)).all()
        for row in rows:
            if row.starts_on==date.today(): s.delete(row)
            else: row.ends_on=date.fromordinal(date.today().toordinal()-1)
        s.execute(delete(GroupMember).where(GroupMember.student_id==student_id,GroupMember.group_id.in_(select(LearningGroup.id).where(LearningGroup.class_id==id))))
        audit(s,p,"class.unenrolled","student",student_id)

@router.get("/classes/{id}/students",response_model=list[StudentView])
def students(id:UUID,request:Request,p=Depends(staff)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        class_access(s,p,id)
        q=select(Student).join(Enrollment,Enrollment.student_id==Student.id).where(Enrollment.class_id==id,Enrollment.starts_on<=date.today(),or_(Enrollment.ends_on.is_(None),Enrollment.ends_on>=date.today()))
        return [StudentView(id=x.id,pseudonym=x.pseudonym) for x in s.scalars(q.order_by(Student.id).limit(100))]

@router.post("/classes/{id}/groups",response_model=GroupView,status_code=201)
def group(id:UUID,body:GroupInput,request:Request,p=Depends(staff)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        class_access(s,p,id)
        for student in set(body.student_ids):
            if not s.scalar(active_enrollment(student,id)):raise HTTPException(422,"Membre non inscrit à cette classe.")
        row=LearningGroup(tenant_id=p.school_id,class_id=id,name=body.name);s.add(row);s.flush()
        s.add_all([GroupMember(tenant_id=p.school_id,group_id=row.id,student_id=x) for x in set(body.student_ids)])
        return GroupView(id=row.id,name=row.name,student_ids=sorted(set(body.student_ids)))

@router.get("/classes/{id}/groups",response_model=list[GroupView])
def groups(id:UUID,request:Request,p=Depends(staff)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        class_access(s,p,id)
        return [GroupView(id=g.id,name=g.name,student_ids=list(s.scalars(select(GroupMember.student_id).where(GroupMember.group_id==g.id)))) for g in s.scalars(select(LearningGroup).where(LearningGroup.class_id==id).limit(100))]

@router.post("/classes/{id}/missions",response_model=MissionView,status_code=201)
def mission(id:UUID,body:MissionInput,request:Request,p=Depends(staff)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        flag(s,"missions");cls=class_access(s,p,id)
        if body.group_id:
            group=s.get(LearningGroup,body.group_id)
            if not group or group.class_id!=id:raise HTTPException(422,"Groupe incompatible.")
        ids=list(dict.fromkeys(body.exercise_version_ids))
        valid=s.scalars(select(ExerciseVersion.id).where(ExerciseVersion.id.in_(ids),ExerciseVersion.status=="published")).all()
        if len(valid)!=len(ids):raise HTTPException(422,"Exercices publiés requis.")
        for identifier in ids:
            levels=s.scalars(select(Competency.curriculum_level_id).join(ExerciseCompetency,ExerciseCompetency.competency_id==Competency.id).where(ExerciseCompetency.exercise_version_id==identifier)).all()
            if not levels or any(level!=cls.curriculum_level_id for level in levels):raise HTTPException(422,"Exercice incompatible avec le niveau de la classe.")
        row=Mission(tenant_id=p.school_id,class_id=id,author_id=p.user_id,**body.model_dump(exclude={"exercise_version_ids"}));s.add(row);s.flush()
        s.add_all([MissionExercise(tenant_id=p.school_id,mission_id=row.id,exercise_version_id=x,ordinal=i) for i,x in enumerate(ids)])
        audit(s,p,"mission.created","mission",row.id)
        return MissionView(id=row.id,class_id=id,**body.model_dump())

@router.get("/missions/today",response_model=list[MissionView])
def today(request:Request,p=Depends(require_roles("student"))):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        flag(s,"missions")
        student=s.scalar(select(Student).where(Student.user_id==p.user_id))
        if not student:raise HTTPException(404,"Profil introuvable.")
        q=select(Mission).join(Enrollment,Enrollment.class_id==Mission.class_id).where(Enrollment.student_id==student.id,Enrollment.starts_on<=date.today(),
            or_(Enrollment.ends_on.is_(None),Enrollment.ends_on>=date.today()),Mission.day==date.today(),Mission.status=="published",
            or_(Mission.group_id.is_(None),Mission.group_id.in_(select(GroupMember.group_id).where(GroupMember.student_id==student.id))))
        output=[]
        for m in s.scalars(q.distinct().limit(50)):
            ids=list(s.scalars(select(MissionExercise.exercise_version_id).join(ExerciseVersion,ExerciseVersion.id==MissionExercise.exercise_version_id).where(MissionExercise.mission_id==m.id,ExerciseVersion.status=="published").order_by(MissionExercise.ordinal)))
            if ids:output.append(MissionView(id=m.id,class_id=m.class_id,title=m.title,day=m.day,group_id=m.group_id,exercise_version_ids=ids))
        return output

@router.put("/classes/{id}/groups/{group_id}",response_model=GroupView)
def replace_group(id:UUID,group_id:UUID,body:GroupInput,request:Request,p=Depends(staff)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        class_access(s,p,id);row=s.get(LearningGroup,group_id)
        if not row or row.class_id!=id:raise HTTPException(404,"Groupe introuvable.")
        for student in set(body.student_ids):
            if not s.scalar(active_enrollment(student,id)):raise HTTPException(422,"Élève non inscrit.")
        row.name=body.name
        s.execute(delete(GroupMember).where(GroupMember.group_id==group_id))
        s.add_all([GroupMember(tenant_id=p.school_id,group_id=group_id,student_id=x) for x in set(body.student_ids)])
        return GroupView(id=row.id,name=row.name,student_ids=sorted(set(body.student_ids)))

@router.post("/classes/{id}/missions/{mission_id}/archive",status_code=204)
def archive_mission(id:UUID,mission_id:UUID,request:Request,p=Depends(staff)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        class_access(s,p,id);row=s.get(Mission,mission_id)
        if not row or row.class_id!=id:raise HTTPException(404,"Mission introuvable.")
        row.status="archived";audit(s,p,"mission.archived","mission",row.id)

@router.get("/classes/{id}/missions",response_model=list[MissionView])
def class_missions(id:UUID,request:Request,p=Depends(staff)):
    with tenant_session(request.app.state.engine,p.school_id) as s:
        class_access(s,p,id)
        return [MissionView(id=m.id,class_id=m.class_id,title=m.title,day=m.day,group_id=m.group_id,status=m.status,
            exercise_version_ids=list(s.scalars(select(MissionExercise.exercise_version_id).where(MissionExercise.mission_id==m.id).order_by(MissionExercise.ordinal))))
            for m in s.scalars(select(Mission).where(Mission.class_id==id).order_by(Mission.day.desc()).limit(100))]


class ControlInput(Strict):
    enabled: bool
    max_help: int=Field(ge=0,le=6)
    expected_revision: int=Field(ge=0)
class ControlView(Strict):
    student_id: UUID
    enabled: bool
    max_help: int
    revision: int

@router.get("/classes/{id}/students/{student_id}/tutor-control",response_model=ControlView)
def get_control(id:UUID,student_id:UUID,request:Request,p=Depends(staff)):
    from shared.db.models import TutorControl
    with tenant_session(request.app.state.engine,p.school_id) as s:
        class_access(s,p,id)
        if not s.scalar(active_enrollment(student_id,id)):raise HTTPException(404,"Élève non inscrit.")
        row=s.scalar(select(TutorControl).where(TutorControl.student_id==student_id))
        return ControlView(student_id=student_id,enabled=row.enabled if row else True,max_help=row.max_help if row else 6,revision=row.revision if row else 0)

@router.put("/classes/{id}/students/{student_id}/tutor-control",response_model=ControlView)
def set_control(id:UUID,student_id:UUID,body:ControlInput,request:Request,p=Depends(staff)):
    from shared.db.models import TutorControl
    from sqlalchemy import text
    with tenant_session(request.app.state.engine,p.school_id) as s:
        class_access(s,p,id)
        if not s.scalar(active_enrollment(student_id,id)):raise HTTPException(404,"Élève non inscrit.")
        s.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:k,0))"),{"k":f"control:{p.school_id}:{student_id}"})
        row=s.scalar(select(TutorControl).where(TutorControl.student_id==student_id))
        if (row.revision if row else 0)!=body.expected_revision:raise HTTPException(409,"Réglage modifié. Rechargez la page.")
        if row:row.enabled=body.enabled;row.max_help=body.max_help;row.changed_by=p.user_id;row.revision+=1
        else:row=TutorControl(tenant_id=p.school_id,student_id=student_id,enabled=body.enabled,max_help=body.max_help,changed_by=p.user_id,revision=1);s.add(row)
        audit(s,p,"tutor.control_changed","student",student_id)
        return ControlView(student_id=student_id,enabled=row.enabled,max_help=row.max_help,revision=row.revision)

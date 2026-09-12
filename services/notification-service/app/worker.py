"""SQL durable + réveil Redis. Les effets et l'état du job sont validés ensemble."""
from datetime import datetime,timedelta,timezone
import time
from uuid import uuid4
from sqlalchemy import create_engine,select
from sqlalchemy.orm import Session
from redis import Redis
from redis.exceptions import RedisError
from shared.config import Settings
from shared.db.models import JobDispatch,BackgroundJob
from shared.db.session import tenant_session
from shared.security.api import subject_state
from shared.security.tokens import Principal
from shared.jobs import run_job
from .routes import ROLES

def process(engine):
    now=datetime.now(timezone.utc)
    with Session(engine) as s:
        envelopes=s.execute(select(JobDispatch.id,JobDispatch.school_id,JobDispatch.job_id).where(JobDispatch.ready_at<=now).order_by(JobDispatch.ready_at).limit(100)).all()
    count=0
    for envelope in envelopes:
        with tenant_session(engine,envelope.school_id) as s:
            job=s.scalar(select(BackgroundJob).where(BackgroundJob.id==envelope.job_id,BackgroundJob.status=="queued",BackgroundJob.available_at<=now).with_for_update(skip_locked=True))
            if job is None:continue
            dispatch=s.get(JobDispatch,envelope.id)
            job.attempts+=1
            try:
                with s.begin_nested():
                    state=subject_state(s,job.requested_by)
                    if not state or not state[1] & ROLES[job.kind]:raise PermissionError("revoked")
                    principal=Principal(user_id=job.requested_by,school_id=envelope.school_id,roles=state[1],auth_version=state[0],session_id=uuid4())
                    job.result=run_job(s,principal,job)
                    s.flush()
                job.status="completed";job.error_code=None;s.delete(dispatch)
            except Exception as exc:
                # Seul un code de classe, aucun contenu de l'exception ni donnée personnelle.
                job.error_code=type(exc).__name__[:80]
                job.result=None
                if job.attempts>=5 or isinstance(exc,PermissionError):job.status="failed";s.delete(dispatch)
                else:
                    job.available_at=now+timedelta(seconds=min(60,2**job.attempts));dispatch.ready_at=job.available_at
            count+=1
    return count

def main():
    settings=Settings(service_name="notification-service")
    engine=create_engine(settings.database_url(),pool_pre_ping=True)
    cache=Redis(host=settings.redis_host,username=settings.redis_username,password=settings.redis_password_file.read_text().strip(),socket_timeout=8)
    try:
        while True:
            try:process(engine)
            except Exception:time.sleep(5)
            try:cache.blpop("edu:jobs:wake",timeout=5)
            except RedisError:time.sleep(5)
    finally:
        cache.close();engine.dispose()

if __name__=="__main__":main()

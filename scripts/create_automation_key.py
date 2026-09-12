"""Provisionnement local explicite d'une clé n8n liée à un compte et un établissement."""
import argparse,json,os,secrets
from pathlib import Path
from uuid import UUID
from sqlalchemy import create_engine
from shared.config import Settings
from shared.db.session import tenant_session
from shared.security.api import subject_state

parser=argparse.ArgumentParser()
parser.add_argument("--school",type=UUID,required=True)
parser.add_argument("--user",type=UUID,required=True)
parser.add_argument("--kinds",nargs="+",choices=["weekly_reports","difficulty_alerts","privacy_purge","exercise_batch"],required=True)
args=parser.parse_args()
settings=Settings();engine=create_engine(settings.database_url())
with tenant_session(engine,args.school) as s:state=subject_state(s,args.user)
engine.dispose()
required={"exercise_batch":{"teacher","content_creator"},"privacy_purge":{"school_admin","sys_admin"},"weekly_reports":{"teacher","school_admin","sys_admin"},"difficulty_alerts":{"teacher","school_admin","sys_admin"}}
if not state or any(not state[1]&required[k] for k in args.kinds):parser.error("Compte actif et rôles compatibles requis")
path=settings.automation_keys_file
records=json.loads(path.read_text())
token=secrets.token_hex(32)
records.append({"school_id":str(args.school),"user_id":str(args.user),"kinds":args.kinds,"token":token})
os.chmod(path,0o600)
path.write_bytes((json.dumps(records,indent=2)+"\n").encode())
os.chmod(path,0o444)
print("Clé ajoutée au registre protégé. Copier sa valeur dans le credential n8n X-Edu-Automation ; aucune valeur affichée.")

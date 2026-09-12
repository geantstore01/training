"""Provisionnement opérateur du premier administrateur. Aucun mot de passe en argument."""
import argparse
import getpass
import re
from uuid import uuid4

from sqlalchemy import create_engine

from shared.config import Settings
from shared.db.models import School, Tenant, User, UserRole
from shared.db.session import tenant_session
from shared.security.passwords import hash_password


def provision(engine, name, login, password, *, system_admin=False):
    if not 2 <= len(name) <= 200 or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", login) or not 12 <= len(password) <= 128:
        raise ValueError("Nom, identifiant ou longueur de mot de passe invalide")
    school_id, user_id = uuid4(), uuid4()
    encoded = hash_password(password)
    with tenant_session(engine, school_id) as session:
        session.add(Tenant(id=school_id, name=name))
        session.flush()
        session.add(School(id=school_id, tenant_id=school_id, name=name))
        session.add(User(id=user_id, tenant_id=school_id, login=login, password_hash=encoded, status="active"))
        session.flush()
        session.add(UserRole(tenant_id=school_id, user_id=user_id, role="sys_admin" if system_admin else "school_admin"))
    return school_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--login", required=True)
    parser.add_argument("--system-admin", action="store_true")
    args = parser.parse_args()
    password = getpass.getpass("Mot de passe (12–128 caractères) : ")
    if password != getpass.getpass("Confirmation : "):
        parser.error("Les mots de passe diffèrent.")
    settings = Settings()
    if settings.db_user != "edu_user":
        parser.error("Exécuter dans user-service avec le compte edu_user.")
    engine = create_engine(settings.database_url())
    try:
        school_id = provision(engine, args.name, args.login, password, system_admin=args.system_admin)
    finally:
        engine.dispose()
    print(f"École créée : {school_id}. Identifiant : {args.login}. Aucun mot de passe enregistré en clair.")


if __name__ == "__main__":
    main()

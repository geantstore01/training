"""Provisionnement opérateur d'un compte parent de démonstration lié à un élève existant.

Demande explicite du propriétaire du site. Suit le même contrat que POST /accounts
(role parent) puis POST /guardian-links de user-service : Guardian vérifié, lien
d'autorité horodaté, preuve chiffrée, journal d'audit opérateur. Aucune relecture
humaine n'est prétendue ; aucun mot de passe n'est enregistré ailleurs que son hash.
"""
import argparse
import getpass
import re
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

from sqlalchemy import create_engine, select

from shared.config import Settings
from shared.db.models import Guardian, GuardianStudent, Student, User, UserRole
from shared.db.session import tenant_session
from shared.security.crypto import IdentityCipher
from shared.security.passwords import hash_password
from shared.security.policy import audit


def provision(engine, cipher, tenant, login, password, student_login, relationship):
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", login) or not 12 <= len(password) <= 128:
        raise ValueError("Identifiant ou longueur de mot de passe invalide")
    operator = SimpleNamespace(school_id=tenant, user_id=None)
    now = datetime.now(timezone.utc)
    with tenant_session(engine, tenant) as session:
        if session.scalar(select(User.id).where(User.tenant_id == tenant, User.login == login)):
            raise ValueError("Cet identifiant existe déjà")
        student_user = session.scalar(select(User).where(User.tenant_id == tenant, User.login == student_login, User.status == "active"))
        if not student_user:
            raise ValueError("Élève introuvable")
        student = session.scalar(select(Student).where(Student.tenant_id == tenant, Student.user_id == student_user.id))
        if not student:
            raise ValueError("Cet identifiant n'est pas un élève")
        user_id, guardian_id, link_id = uuid4(), uuid4(), uuid4()
        session.add(User(id=user_id, tenant_id=tenant, login=login, password_hash=hash_password(password), status="active"))
        session.flush()
        session.add(UserRole(tenant_id=tenant, user_id=user_id, role="parent"))
        session.add(Guardian(id=guardian_id, tenant_id=tenant, user_id=user_id, verified_at=now))
        session.flush()
        session.add(GuardianStudent(id=link_id, tenant_id=tenant, guardian_id=guardian_id, student_id=student.id,
            relationship=relationship, authority_verified_at=now, verified_by=None,
            verification_evidence_ciphertext=cipher.encrypt(
                {"reference": "compte de démonstration créé par opérateur à la demande du propriétaire",
                 "verified_by": None},
                school_id=tenant, owner_id=link_id, purpose="guardian_verification")))
        audit(session, operator, "operator.parent_demo_created", "guardian_link", link_id)
        return {"parent_login": login, "student_id": str(student.id), "student_pseudonym": student.pseudonym}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant", type=UUID, required=True)
    parser.add_argument("--login", required=True)
    parser.add_argument("--student-login", required=True)
    parser.add_argument("--relationship", choices=["parent", "legal_guardian"], default="parent")
    args = parser.parse_args()
    password = getpass.getpass("Mot de passe du parent (12–128 caractères) : ")
    if password != getpass.getpass("Confirmation : "):
        parser.error("Les mots de passe diffèrent.")
    settings = Settings()
    if settings.db_user != "edu_user":
        parser.error("Exécuter dans user-service avec le compte edu_user.")
    engine = create_engine(settings.database_url())
    cipher = IdentityCipher(settings.pii_keys_file)
    try:
        print(provision(engine, cipher, args.tenant, args.login, password, args.student_login, args.relationship))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

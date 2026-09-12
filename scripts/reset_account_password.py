"""Réinitialisation opérateur d'un mot de passe à la demande du propriétaire.

Mot de passe fourni sur stdin (jamais en argument, jamais enregistré). Le hash
argon2 remplace l'ancien, auth_version est incrémenté pour invalider les jetsons
antérieurs et la décision est journalisée (operator.access_reset).
"""
import argparse
import getpass
from types import SimpleNamespace
from uuid import UUID

from sqlalchemy import create_engine, select

from shared.config import Settings
from shared.db.models import User
from shared.db.session import tenant_session
from shared.security.passwords import hash_password
from shared.security.policy import audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant", type=UUID, required=True)
    parser.add_argument("--login", required=True)
    args = parser.parse_args()
    password = getpass.getpass(f"Nouveau mot de passe pour {args.login} (12–128 caractères) : ")
    if not 12 <= len(password) <= 128:
        raise SystemExit("Longueur invalide : la plateforme exige 12 à 128 caractères.")
    settings = Settings()
    if settings.db_user != "edu_user":
        raise SystemExit("Exécuter avec le compte edu_user.")
    engine = create_engine(settings.database_url())
    operator = SimpleNamespace(school_id=args.tenant, user_id=None)
    try:
        with tenant_session(engine, args.tenant) as session:
            user = session.scalar(select(User).where(User.tenant_id == args.tenant, User.login == args.login))
            if user is None:
                raise SystemExit(f"Compte introuvable : {args.login}")
            if user.status != "active":
                raise SystemExit(f"Compte non actif ({user.status}) : {args.login}")
            user.password_hash = hash_password(password)
            user.auth_version += 1
            audit(session, operator, "operator.access_reset", "user", user.id)
            session.flush()
            print(f"{args.login}: mot de passe réinitialisé, auth_version={user.auth_version}.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

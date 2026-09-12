"""Purge explicite des traces expirées d'un tenant avec le compte de maintenance.

Les durées doivent être définies par la politique de conservation validée.
Ne supprime ni données pédagogiques, ni consentements, ni comptes utilisateurs.
"""
import argparse
from uuid import UUID

from sqlalchemy import create_engine, text

from shared.config import Settings
from shared.db.session import tenant_session

parser = argparse.ArgumentParser()
parser.add_argument("--tenant", type=UUID, required=True)
args = parser.parse_args()
config = Settings()
if config.db_user != "edu_migrator":
    parser.error("Le compte edu_migrator est requis pour la maintenance.")
engine = create_engine(config.database_url())
with tenant_session(engine, args.tenant) as session:
    counts = {}
    counts["tutor_turns"] = session.execute(text("DELETE FROM tutor_turns WHERE expires_at <= now()")).rowcount
    counts["safety_events"] = session.execute(text("DELETE FROM safety_events WHERE expires_at <= now()")).rowcount
    counts["ai_interactions"] = session.execute(text("DELETE FROM ai_interactions a WHERE expires_at <= now() AND NOT EXISTS (SELECT 1 FROM safety_events s WHERE s.tenant_id=a.tenant_id AND s.interaction_id=a.id)")).rowcount
    counts["audit_logs"] = session.execute(text("DELETE FROM audit_logs WHERE expires_at <= now()")).rowcount
engine.dispose()
print(counts)

"""Outil de construction de la révision 0001. Ne plus exécuter après une évolution métier.

Les migrations ultérieures doivent être ajoutées, jamais remplacer ce snapshot.
"""
from pathlib import Path
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from shared.db.models import Base

root = Path(__file__).resolve().parents[1] / "migrations" / "sql"
root.mkdir(parents=True, exist_ok=True)
dialect = postgresql.dialect()
statements = ["-- Révision 0001 figée. Extension vector et rôles installés par infra/postgres/init.sh."]
for table in Base.metadata.sorted_tables:
    statements.append(str(CreateTable(table).compile(dialect=dialect)).strip() + ";")
    statements.extend(str(CreateIndex(index).compile(dialect=dialect)) + ";" for index in sorted(table.indexes, key=lambda item: item.name))
(root / "0001_schema.sql").write_text("\n\n".join(statements) + "\n", encoding="utf-8")
down = [f'DROP TABLE "{table.name}";' for table in reversed(Base.metadata.sorted_tables)]
down += [f"DROP FUNCTION IF EXISTS {name}();" for name in ["edu_touch_updated_at", "edu_check_prerequisite_cycle", "edu_guard_version", "edu_guard_review", "edu_guard_version_child", "edu_check_consent", "edu_check_attempt"]]
(root / "0001_down.sql").write_text("\n".join(down) + "\n", encoding="utf-8")

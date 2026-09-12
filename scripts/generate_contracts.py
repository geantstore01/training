"""Regénère les contrats publics de santé des 15 services."""
import json
from pathlib import Path

from shared.service_loader import load_service

root = Path(__file__).resolve().parents[1]
for directory in sorted((root / "services").iterdir()):
    if directory.is_dir():
        schema = load_service(directory.name).app.openapi()
        (directory / "openapi.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

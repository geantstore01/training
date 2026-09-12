"""Fige les dépendances installées, en séparant le modèle NER du runtime commun."""
from importlib.metadata import distribution
import json
from pathlib import Path
import tomllib
import hashlib
from urllib.request import urlopen

from packaging.requirements import Requirement

root = Path(__file__).resolve().parents[1]
project = tomllib.loads((root / "pyproject.toml").read_text())["project"]


def closure(requirements):
    collected = {}
    processed = set()

    def visit(spec):
        req = Requirement(spec)
        if req.marker and not any(req.marker.evaluate({"extra": extra}) for extra in ["", *req.extras]):
            return
        key = (req.name.lower().replace("_", "-"), tuple(sorted(req.extras)))
        if key in processed:
            return
        processed.add(key)
        package = distribution(req.name)
        collected[package.metadata["Name"].lower().replace("_", "-")] = package.version
        for entry in package.requires or []:
            child = Requirement(entry)
            if child.marker is None or any(child.marker.evaluate({"extra": extra}) for extra in ["", *req.extras]):
                child.marker = None
                visit(str(child))
    for item in requirements:
        visit(item)
    return collected


base = closure(project["dependencies"])
# Uvicorn nécessite click ; colorama reste utilisable aussi sur Linux pour garder le lock portable.
base["colorama"] = distribution("colorama").version
tests = closure(project["optional-dependencies"]["test"])
safety = closure(project["optional-dependencies"]["safety"])
(root / "requirements.lock").write_text("\n".join(f"{name}=={version}" for name, version in sorted(base.items())) + "\n")
(root / "requirements-test.lock").write_text("-r requirements.lock\n" + "\n".join(f"{name}=={version}" for name, version in sorted(tests.items()) if name not in base) + "\n")
direct = json.loads(distribution("fr-core-news-sm").read_text("direct_url.json"))
archive_info = direct["archive_info"]
checksum = archive_info.get("hashes", {}).get("sha256")
if not checksum and archive_info.get("hash", "").startswith("sha256="):
    checksum = archive_info["hash"].split("=", 1)[1]
if not checksum:
    with urlopen(direct["url"], timeout=30) as response:
        checksum = hashlib.sha256(response.read()).hexdigest()
model = direct["url"] + "#sha256=" + checksum
(root / "requirements-safety.lock").write_text("-r requirements.lock\n" + "\n".join(f"{name}=={version}" for name, version in sorted(safety.items()) if name not in base) + "\n" + model + "\n")

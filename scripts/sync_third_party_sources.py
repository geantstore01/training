#!/usr/bin/env python3
"""Clone/update approved upstream repositories and record an auditable snapshot.

The script never executes upstream application code. It stores commit hashes, file
inventories and licence-file locations so the content review workflow can decide
what may be imported into Éducapilote.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SOURCES = {
    "ressources-pedagogiques": "https://github.com/Kazhnuz/ressources-pedagogiques.git",
    "locochoco": "https://github.com/grouan/LocoChoco.git",
    "ecole-interactive": "https://github.com/nakkouche/ecole-interactive.git",
    "jeux": "https://github.com/Antonin777/Jeux.git",
}


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def sync(root: Path) -> list[dict[str, object]]:
    root.mkdir(parents=True, exist_ok=True)
    records = []
    for name, url in SOURCES.items():
        directory = root / name
        if (directory / ".git").is_dir():
            run("git", "fetch", "--depth", "1", "origin", cwd=directory)
            run("git", "reset", "--hard", "origin/HEAD", cwd=directory)
        else:
            run("git", "clone", "--depth", "1", url, str(directory))
        files = [p for p in directory.rglob("*") if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts]
        licences = [str(p.relative_to(directory)) for p in files if p.name.lower().startswith(("licence", "license", "copying"))]
        digest = hashlib.sha256("\n".join(sorted(f"{p.relative_to(directory)}:{hashlib.sha256(p.read_bytes()).hexdigest()}" for p in files)).encode()).hexdigest()
        records.append({"name": name, "repository": url, "commit": run("git", "rev-parse", "HEAD", cwd=directory), "files": len(files), "licence_files": licences, "snapshot_sha256": digest})
    return records


if __name__ == "__main__":
    base = Path("/stockage/training/sources/third-party")
    output = base / "sync-manifest.json"
    output.write_text(json.dumps({"synchronised_at": datetime.now(timezone.utc).isoformat(), "sources": sync(base)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)

#!/usr/bin/env python3
"""Stage MIT-declared École Interactive CM2 QCMs for independent review.

The script reads only the upstream Markdown files. It does not publish material
or execute upstream code: a reviewer must map each QCM to an official
competency and approve the resulting controlled exercise in Éducapilote.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/stockage/training/sources/third-party/ecole-interactive")
OUTPUT = ROOT.parent / "staged-ecole-interactive-cm2.json"
FRONT = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
QUESTION = re.compile(r"^## Question \d+\s*\n(.*?)(?=^## Question \d+\s*$|\Z)", re.M | re.S)
OPTION = re.compile(r"^- \[([ x])\] (.+)$", re.M)


def metadata(raw: str) -> tuple[dict[str, str], str]:
    match = FRONT.match(raw)
    if not match:
        raise ValueError("front matter absent")
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError("front matter invalide")
        values[key.strip()] = value.strip().strip('"')
    return values, raw[match.end():]


def parse(path: Path) -> dict[str, object]:
    raw = path.read_text(encoding="utf-8")
    head, body = metadata(raw)
    questions = []
    for index, match in enumerate(QUESTION.finditer(body), start=1):
        lines = match.group(1).strip().splitlines()
        prompt = next((line.strip() for line in lines if line.strip() and not line.startswith("- [")), "")
        options = [{"label": label.strip(), "correct": mark == "x"} for mark, label in OPTION.findall(match.group(1))]
        if not prompt or len(options) < 2 or sum(item["correct"] for item in options) != 1:
            raise ValueError(f"question {index} invalide")
        questions.append({"ordinal": index, "prompt": prompt, "options": options})
    if not questions:
        raise ValueError("aucune question")
    return {"upstream_path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "metadata": head, "questions": questions}


def main() -> None:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, text=True,
                            stdout=subprocess.PIPE).stdout.strip()
    records, rejected = [], []
    for path in sorted((ROOT / "content/qcm/CM2").rglob("*.md")):
        try:
            records.append(parse(path))
        except ValueError as exc:
            rejected.append({"upstream_path": str(path.relative_to(ROOT)), "reason": str(exc)})
    document = {"source": "https://github.com/nakkouche/ecole-interactive", "commit": commit,
                "license": "MIT declared in upstream README; verify LICENSE file before publication",
                "created_at": datetime.now(timezone.utc).isoformat(), "records": records, "rejected": rejected,
                "publication": "staged_only_independent_human_review_required"}
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{OUTPUT}: {len(records)} QCM CM2 staged, {len(rejected)} rejected")


if __name__ == "__main__":
    main()

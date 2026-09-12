"""Vendor only the inspected QuizInput contract, preserving its MPL-2.0 notice.

No application entry point, file/network access, auth code or dependencies are run.
"""
import ast
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
repo=ROOT/"artifacts/reference-science-classquiz"
if subprocess.check_output(["git","-C",str(repo),"rev-parse","HEAD"],text=True).strip()!="711bdde7a7dcd2d217cfc75dbbbb2592a78582d3":
    raise ValueError("Révision amont non vérifiée")
source=(repo/"classquiz/db/models.py").read_text(encoding="utf-8")
names={"ABCDQuizAnswer","RangeQuizAnswer","VotingQuizAnswer","QuizQuestionType","TextQuizAnswer","QuizQuestion","QuizInput"}
tree=ast.parse(source)
parts=[ast.get_source_segment(source,node) for node in tree.body if isinstance(node,ast.ClassDef) and node.name in names]
if len(parts)!=len(names):raise ValueError("Upstream contract changed")
target=ROOT/"shared/science/vendor";target.mkdir(parents=True,exist_ok=True)
(target/"__init__.py").write_text("",encoding="utf-8")
(target/"classquiz_contract.py").write_text('''# SPDX-FileCopyrightText: 2023 Marlon W (Mawoka)
# SPDX-License-Identifier: MPL-2.0
# Source: mawoka-myblock/classquiz, commit 711bdde7a7dcd2d217cfc75dbbbb2592a78582d3
# Extracted seven unmodified data-model classes; imports reduced to their needs.
from enum import Enum
from pydantic import BaseModel, field_validator, ValidationInfo

'''+"\n\n\n".join(parts)+"\n",encoding="utf-8")
(target/"CLASSQUIZ-LICENSE.txt").write_text((repo/"LICENSE").read_text(encoding="utf-8"),encoding="utf-8")

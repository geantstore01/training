"""Explicit adapters: ClassQuiz schema and PhET/openZIM delivery configuration.

ClassQuiz schema reviewed at commit 711bdde7, classquiz/db/models.py (MPL-2.0).
Original adapter; the extracted upstream QuizInput contract retains its MPL notice.
"""
from .catalogue import BY_CHAPTER
from .vendor.classquiz_contract import QuizInput

PHET = {
    "circuits": {"name":"Circuit Construction Kit: DC","url":"https://phet.colorado.edu/sims/html/circuit-construction-kit-dc/latest/circuit-construction-kit-dc_all.html?locale=fr",
        "provider":"PhET Interactive Simulations, University of Colorado Boulder","delivery":"external_link","review":"Select only battery/lamp/switch for CM2."},
}

def classquiz_payload(chapter: str) -> dict:
    """Staff QuizInput payload for editor/finish; contains private teacher answers."""
    entry=BY_CHAPTER[chapter]
    questions=[]
    for task in entry["tasks"]:
        if task["response_type"]!="choice":continue
        questions.append({"question":task["question"],"time":"180","type":"ABCD",
            "answers":[{"answer":o["label"],"right":o["id"]==task["rule"]["expected"]} for o in task["options"]],
            "hide_results":True})
    return QuizInput.model_validate({"title":entry["title"],"description":"Sciences CM2 — quiz collectif accompagné. Faire justifier les réponses. Source : "+entry["science"]["source"]["url"],
        "public":False,"questions":questions}).model_dump(mode="json")

def offline_command(output: str) -> list[str]:
    """Argument vector for openzim/phet's documented CLI. Does NOT execute/download.

Its subject filter is broad: teacher must review the resulting catalogue; the
four original instruments do not require PhET/ZIM or any external downloads.
"""
    return ["phet2zim","--includeLanguages","fr","--subjects","physics","--output",output]

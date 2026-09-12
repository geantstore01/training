"""Finite reference tables and editorial dictation categories. No guessed grammar."""
from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata

@lru_cache
def verb_forms():
    forms=json.loads((Path(__file__).parent/"data/french_verbs.json").read_text(encoding="utf-8"))["forms"]
    # Original reviewed addition: upstream CSV uses corrupt combining characters here.
    forms["être|indicatif|present|4"]="êtes"
    # Original finite additions; no suffix guessing for unknown or irregular verbs.
    for tense,values in {"present":["chante","chantes","chante","chantons","chantez","chantent"],
        "passe_simple":["chantai","chantas","chanta","chantâmes","chantâtes","chantèrent"]}.items():
        for person,value in enumerate(values):forms[f"chanter|indicatif|{tense}|{person}"]=value
    for tense,auxiliary in (("passe_compose","present"),("plus_que_parfait","imparfait")):
        for person in range(6):forms[f"chanter|indicatif|{tense}|{person}"]=forms[f"avoir|indicatif|{auxiliary}|{person}"]+" chanté"
    return forms

def conjugate(key):
    if key not in verb_forms():raise ValueError("Conjugaison absente du corpus vérifié")
    return verb_forms()[key]

def words(text):
    return re.findall(r"[\w]+(?:['’][\w]+)?",unicodedata.normalize("NFC",text).casefold().replace("’","'"))

def dictation_feedback(rule,response):
    expected,received=words(rule.expected),words(response)
    if len(received)!=len(expected):
        return {"needs_review":True,"categories":[],"message":"Le nombre de mots a changé. Relis la phrase avec ton enseignant pour retrouver les mots ajoutés ou oubliés."}
    targets={item.position:item for item in rule.dictation_targets}
    differences=[i for i,(a,b) in enumerate(zip(expected,received)) if a!=b]
    if any(i not in targets for i in differences):
        return {"needs_review":True,"categories":[],"message":"Cette modification n'est pas prévue par le correcteur. Relis-la avec ton enseignant."}
    selected=[targets[i] for i in differences]
    return {"needs_review":False,"categories":list(dict.fromkeys(item.category for item in selected)),
        "message":" ".join(dict.fromkeys(item.hint for item in selected))}

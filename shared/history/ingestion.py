"""Extract candidate entities without turning co-occurrence into historical facts."""
import re
from .vendor.deeptutor_chunker import chunk_with_boundary
from .catalogue import BY_CHAPTER

def history_chunks(text):
    if not 80 <= len(text) <= 100_000 or any(len(w)>300 for w in text.split()):
        raise ValueError("Document historique vide, trop long ou mal formé")
    spans=chunk_with_boundary(text,budget=100,overlap_ratio=.1,min_chunk_chars=900,max_chunk_chars=1600,boundary="sentence")
    if not 1 <= len(spans) <= 100:
        raise ValueError("Nombre de passages invalide")
    return [span.text for span in spans]

def extract_entities(text,chapter):
    meta=BY_CHAPTER[chapter]["history"]
    if len(text)>100_000:raise ValueError("Document trop long")
    # Offsets trace every proposal back to the extracted source. No invented NER.
    dates=[dict(value=m.group(),start=m.start(),end=m.end()) for m in re.finditer(r"\b(?:17|18|19|20)\d{2}\b",text)]
    figures=[f["name"] for f in meta["figures"] if f["name"].casefold() in text.casefold()]
    places=[p["name"] for p in meta["places"] if p["name"].casefold() in text.casefold()]
    events=[e["id"] for e in meta["timeline"] if str(e["year"]) in {d["value"] for d in dates} and e["title"].casefold() in text.casefold()]
    return dict(status="draft",human_review_required=True,chapter=chapter,dates=dates,figures=figures,places=places,event_candidates=events,
        warning="La présence de mots et de dates ne prouve aucune relation historique entre eux.")

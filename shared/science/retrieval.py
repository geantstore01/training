"""Small local source explorer, adapted from Renee Noble's get_search_summary.

Copyright (c) 2024 Renee Noble. MIT; see docs/science/THIRD_PARTY.md.
Changes: Unicode token boundaries, typed source IDs, caller-supplied vetted
passages, no product corpus, no credentials, no substring matching, bounded size.
This is lexical retrieval for editorial preview, NOT an embedding service.
"""
import re
import unicodedata

STOP_WORDS={"le","la","les","un","une","des","du","de","et","en","que","qui","pour","dans","est","au","aux","ce","cette","avec","sur"}

def words(text):
    return set(re.findall(r"[^\W\d_]+",unicodedata.normalize("NFKC",text).casefold()))-STOP_WORDS

def retrieve(question,passages,limit=3):
    if not 1<=limit<=5 or len(question)>1000 or len(passages)>100:
        raise ValueError("Recherche locale trop large")
    keywords=words(question)
    scores=[]
    for passage in passages:
        if passage.get("status")!="approved" or passage.get("level")!="CM2" or passage.get("subject")!="sciences":continue
        score=len(keywords & words(passage["body"][:4000]))
        if score:scores.append((score,passage))
    return [p for _,p in sorted(scores,key=lambda row:-row[0])[:limit]]

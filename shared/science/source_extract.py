"""Layout-specific extraction of the CM column in the verified 2023 annex.

Fail closed if the official file changes. Rectangles use PDF points, bottom-left
origin, and are tied to this SHA-256, not a generic guess about PDF columns.
"""
import hashlib
from collections import defaultdict

SHA256="a6b2a8a97a1027c6debe8df87c168b1d1b0bcff2d44f4cc16b799ee01bc33218"
REGIONS={4:(65,310,480,625),7:(65,310,290,515),9:(65,310,369,558),14:(65,310,579,610)}

def cm_extract(data,reader,pages):
    if hashlib.sha256(data).hexdigest()!=SHA256:
        raise ValueError("Le PDF a changé : vérifier à nouveau le découpage CM / sixième")
    if not pages or any(page not in REGIONS for page in pages):
        raise ValueError("Pages hors du profil scientifique CM2 vérifié")
    output=[]
    for page in pages:
        x0,x1,y0,y1=REGIONS[page];lines=defaultdict(list)
        def visit(value,cm,tm,font,size):
            x,y=tm[4],tm[5]
            if x0<=x<x1 and y0<=y<=y1 and value.strip():
                lines[round(y)].append((x,value.replace("\n","").replace("\uf0b7","")))
        reader.pages[page-1].extract_text(visitor_text=visit)
        # Preserve spaces carried by PDF text fragments: inserting a new space
        # between font/kerning runs would turn « fabriqués » into « f abriqués ».
        text="\n".join("".join(t for _,t in sorted(parts)).strip() for _,parts in sorted(lines.items(),reverse=True))
        if len(text)<50:raise ValueError("Colonne CM inexploitable")
        output.append(f"[Annexe 2023, page {page}, connaissances de cours moyen]\n{text}")
    return "\n\n".join(output)

"""Opt-in local Ollama drafting, requiring existing curriculum and approved excerpts.

Input: chapter, competency, source_ids, exercise_ids, passages. No credentials or
student messages are accepted. Outputs a draft file, never an API publication.
"""
import argparse,json
from pathlib import Path
from shared.science.generation import generate_with_ollama

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context",type=Path,required=True)
    parser.add_argument("--model",required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    context=json.loads(args.context.read_text(encoding="utf-8"))
    if set(context)!={"chapter","competency","source_ids","exercise_ids","passages"}:raise ValueError("Contexte pédagogique uniquement")
    draft=generate_with_ollama(**context,model=args.model)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(draft,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Brouillon créé. Validation humaine indépendante requise avant publication.")

if __name__=="__main__":main()

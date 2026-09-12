from .correctors import calculate,correct,grade
from .schemas import Candidate, Check, PipelineReport

STEPS=["schema","resource_limits","typology","identifiers","answer_coverage","choice_coherence",
       "mathematical_rules","linguistic_rules","curriculum_and_sources","self_correction"]

def validate(candidate:Candidate,competency_ids:set,source_ids:set):
    c=candidate
    def typology():
        types=[p.response_type for p in c.parts]
        if c.kind=="multiple_choice": return len(types)==1 and types[0]=="choice"
        if c.kind in {"ordering","timeline"}: return len(types)==1 and types[0]=="ordering"
        if c.kind=="short_text": return len(types)==1 and types[0] in {"number","text"}
        if c.kind=="fill_blanks": return all(t in {"number","text"} for t in types) and all("{"+p.id+"}" in p.question for p in c.parts)
        return len(types)>=2 and all(t in {"number","text","choice"} for t in types)
    def identifiers():
        return len({p.id for p in c.parts})==len(c.parts) and len({h.level for h in c.hints})==len(c.hints) and len(set(c.source_ids))==len(c.source_ids)
    def choices():
        for p in c.parts:
            r=c.answers[p.id]; ids=[o.id for o in p.options]
            if len(ids)!=len(set(ids)) or len({o.label for o in p.options})!=len(ids): return False
            if p.response_type=="choice":
                if r.mode!="choice" or len(ids)<2 or r.expected not in ids: return False
            elif p.response_type=="ordering":
                if r.mode!="ordering" or len(ids)<2 or not isinstance(r.expected,list) or len(r.expected)!=len(set(r.expected)) or set(r.expected)!=set(ids): return False
            elif ids: return False
        return True
    def mathematics():
        for p in c.parts:
            r=c.answers[p.id]
            if r.decimal_only and r.mode!="number":return False
            if (p.response_type=="number")!=(r.mode=="number"): return False
            if r.mode=="number":
                calculate(r.expected)
                if r.variants: return False
            if r.diagram_measure:
                v=p.visual
                if v is None or r.mode!="number":return False
                if r.diagram_measure=="fraction":
                    if v.kind!="fraction":return False
                    value=calculate(f"{v.selected}/{v.parts}")
                else:
                    if v.kind!="grid":return False
                    value=v.rows*v.columns if r.diagram_measure=="area" else 2*(v.rows+v.columns)
                if calculate(r.expected)!=value:return False
            for equality in r.verified_equalities:
                sides=equality.split("=")
                if len(sides)!=2 or calculate(sides[0])!=calculate(sides[1]): return False
            for mistake in r.misconceptions:
                if r.mode not in {"number","choice","grammar","spelling","formulation"}: return False
                if correct(r,mistake.response)[0]: return False
                if r.mode=="number": calculate(mistake.response)
        return True
    def language():
        for p in c.parts:
            r=c.answers[p.id]
            if p.response_type=="text" and (r.mode not in {"spelling","grammar","formulation","open_writing","dictation"} or not isinstance(r.expected,str)): return False
            if r.conjugation_key:
                from .french import conjugate
                if r.mode!="grammar" or r.expected!=conjugate(r.conjugation_key):return False
            if r.dictation_targets:
                from .french import words
                if r.mode!="dictation" or len({t.position for t in r.dictation_targets})!=len(r.dictation_targets):return False
                if any(t.position>=len(words(r.expected)) for t in r.dictation_targets):return False
            if p.response_type!="text" and (r.variants or r.known_errors): return False
            if len(r.known_errors)>20: return False
            if any(correct(r,wrong)[0] for wrong in r.known_errors): return False
        return True
    def references():
        return {p.competency_id for p in c.parts}<=competency_ids and set(c.source_ids)<=source_ids
    checks=[lambda: Candidate.model_validate(c.model_dump()) is not None,
        lambda: len(c.model_dump_json())<=24000 and all(len(r.known_errors)<=20 for r in c.answers.values()),
        typology,identifiers,lambda:set(c.answers)=={p.id for p in c.parts},choices,mathematics,language,references,
        lambda:all(r.correct or c.answers[r.part_id].mode=="open_writing" and r.error_code=="HUMAN_REVIEW" for r in grade(c,{k:v.expected for k,v in c.answers.items()}))]
    results=[]
    for i,check in enumerate(checks):
        try: okay=bool(check())
        except (ValueError,TypeError,KeyError): okay=False
        results.append(Check(step=i+1,name=STEPS[i],passed=okay))
    return PipelineReport(passed=all(r.passed for r in results),checks=results)

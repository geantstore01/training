import random
from datetime import date
from typing import Annotated,Literal
from uuid import UUID
from pydantic import Field,model_validator
from .schemas import Candidate,Model,Short
from .correctors import calculate

class Event(Model):
    label: Short
    date: date

class GenerationInput(Model):
    template: Literal["arithmetic","agreement","chronology"]
    kind: Literal["multiple_choice","fill_blanks","short_text","step_problem","ordering","timeline"]
    competency_id: UUID
    source_ids: Annotated[list[UUID],Field(min_length=1,max_length=12)]
    seed: Annotated[int,Field(ge=0,le=2147483647)]
    events: Annotated[list[Event],Field(max_length=12)] = []

    @model_validator(mode="after")
    def template_kind(self):
        if self.template=="chronology":
            if self.kind!="timeline" or len(self.events)<2 or len({e.date for e in self.events})!=len(self.events): raise ValueError("Chronologie non ambiguë requise")
        elif self.events or self.kind=="timeline": raise ValueError("Événements réservés à la chronologie")
        if self.template=="agreement" and self.kind not in {"fill_blanks","short_text","multiple_choice"}: raise ValueError("Type incompatible")
        return self

def generate(data:GenerationInput):
    rng=random.Random(data.seed)
    a,b,c=[rng.randint(2,30) for _ in range(3)]
    parts=[]; answers={}
    def option_id(): return "o"+format(rng.getrandbits(64),"016x")
    def part(key,question,response_type,expected,mode=None,options=None,errors=None):
        parts.append(dict(id=key,question=question,competency_id=data.competency_id,response_type=response_type,options=options or []))
        answers[key]=dict(mode=mode or response_type,expected=expected,known_errors=errors or {})
    if data.template=="chronology":
        items=list(enumerate(data.events)); rng.shuffle(items)
        ids={i:option_id() for i,e in items}
        opts=[dict(id=ids[i],label=e.label) for i,e in items]
        expected=[ids[i] for i,e in sorted(enumerate(data.events),key=lambda pair:pair[1].date)]
        part("main","Classe les événements du plus ancien au plus récent.","ordering",expected,options=opts)
    elif data.template=="agreement":
        noun,singular,plural=rng.choice([("chats","petit","petits"),("maisons","grande","grandes"),("fleurs","jolie","jolies")])
        question=f"Complète : les {noun} sont {{main}}. Utilise « {singular} » au pluriel."
        if data.kind=="multiple_choice":
            answer_id=option_id()
            opts=[dict(id=answer_id,label=plural),dict(id=option_id(),label=singular)]; rng.shuffle(opts)
            part("main",question,"choice",answer_id,options=opts)
        else:
            part("main",question,"text",plural,mode="grammar",errors={singular:"AGREEMENT_ERROR"})
    elif data.kind=="ordering":
        numbers=rng.sample(range(1,100),5); opts=[dict(id=f"n{i}",label=str(n)) for i,n in enumerate(numbers)]
        expected=[f"n{i}" for i in sorted(range(5),key=lambda i:numbers[i])]
        part("main","Classe ces nombres du plus petit au plus grand.","ordering",expected,options=opts)
    elif data.kind=="step_problem":
        part("subtotal",f"Un groupe reçoit {a} livres puis {b} livres. Combien en reçoit-il ?","number",str(calculate(f"{a}+{b}")))
        part("total",f"Il y a {c} groupes qui reçoivent chacun la même quantité. Combien de livres au total ?","number",str(calculate(f"({a}+{b})*{c}")))
    elif data.kind=="multiple_choice":
        expected=int(calculate(f"{a}+{b}")); values=[expected,expected+1,expected-1,expected+10]
        opts=[dict(id=option_id(),label=str(n)) for n in values]; answer_id=opts[0]["id"]; rng.shuffle(opts)
        part("main",f"Combien font {a} + {b} ?","choice",answer_id,options=opts)
    else:
        part("main",f"Complète : {a} + {b} = {{main}}.","number",str(calculate(f"{a}+{b}")))
    return Candidate(kind=data.kind,instruction="Lis la consigne et prends le temps de réfléchir.",parts=parts,answers=answers,
        source_ids=data.source_ids,hints=[dict(level=1,text="Relis la consigne et repère ce que tu connais déjà.")])

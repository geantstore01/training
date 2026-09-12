"""Versioned, configurable-by-code BKT and SM-2-style scheduling defaults, not a clinical measure."""
from dataclasses import dataclass
from datetime import datetime,timedelta
from decimal import Decimal
import math
from shared.pedagogy import EvaluationLevel

VERSION="bkt-sm2-v1"
PRIOR=0.20

def bkt(prior:float,correct:bool,elapsed_days:float=0)->float:
    if not math.isfinite(prior) or not 0<=prior<=1 or not math.isfinite(elapsed_days) or elapsed_days<0:
        raise ValueError("Invalid mastery state")
    p=max(0.05,prior*math.exp(-math.log(2)*min(elapsed_days,3650)/90))
    slip,guess,learn=0.10,0.20,0.10
    if correct: posterior=p*(1-slip)/(p*(1-slip)+(1-p)*guess)
    else: posterior=p*slip/(p*slip+(1-p)*(1-guess))
    return round(min(0.99999,max(0.00001,posterior+(1-posterior)*learn)),5)

def mastery_level(probability,evidence_count,repetitions):
    if evidence_count==0: return EvaluationLevel.NOT_EVALUATED
    if evidence_count<2: return EvaluationLevel.DISCOVERY
    if probability>=0.95 and evidence_count>=8 and repetitions>=3: return EvaluationLevel.CONSOLIDATED
    if probability>=0.85 and evidence_count>=5: return EvaluationLevel.MASTERED
    if probability<0.40: return EvaluationLevel.FRAGILE
    return EvaluationLevel.IN_PROGRESS

@dataclass(frozen=True)
class Schedule:
    due_at:datetime
    interval_days:int
    ease_factor:Decimal
    repetitions:int

def schedule(now:datetime,correct:bool,previous:Schedule|None=None)->Schedule:
    if now.tzinfo is None: raise ValueError("UTC-aware date required")
    if previous and previous.due_at>now and correct:
        return previous
    old=previous or Schedule(now,0,Decimal("2.5"),0)
    q=5 if correct else 2
    ease=max(1.3,min(3.0,float(old.ease_factor)+0.1-(5-q)*(0.08+(5-q)*0.02)))
    if not correct: interval,repetitions=1,0
    else:
        repetitions=old.repetitions+1
        interval=1 if repetitions==1 else 6 if repetitions==2 else min(365,round(old.interval_days*float(old.ease_factor)))
    return Schedule(now+timedelta(days=interval),interval,Decimal(str(round(ease,3))),repetitions)

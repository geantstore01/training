"""Bounded exact arithmetic and explicit linguistic rubrics. No eval, LLM or fuzzy acceptance."""
import ast
from fractions import Fraction
import re
import unicodedata
from .schemas import AnswerRule, Candidate, PartResult

VERSION="controlled-v1"

class InvalidExpression(ValueError):
    pass

def calculate(value: str) -> Fraction:
    if not isinstance(value,str) or len(value)>128:
        raise InvalidExpression("Expression trop longue")
    source=value.strip().replace(",",".").replace("×","*").replace("÷","/").replace("−","-")
    if not source or not re.fullmatch(r"[0-9.()+*/\s-]+",source) or re.search(r"[0-9]{10}",source):
        raise InvalidExpression("Expression non autorisée")
    def canonical_number(match):
        token=match.group()
        if token.startswith("."): return "0"+token
        whole,separator,fraction=token.partition(".")
        return (whole.lstrip("0") or "0")+separator+fraction
    source=re.sub(r"[0-9]+(?:\.[0-9]*)?|\.[0-9]+",canonical_number,source)
    nesting=0
    for char in source:
        nesting += 1 if char=="(" else -1 if char==")" else 0
        if nesting>12 or nesting<0: raise InvalidExpression("Imbrication excessive")
    try:
        tree=ast.parse(source,mode="eval")
        if sum(1 for _ in ast.walk(tree))>64: raise InvalidExpression("Expression trop complexe")
        def visit(node,depth=0):
            if depth>12: raise InvalidExpression("Imbrication excessive")
            if isinstance(node,ast.Constant) and type(node.value) in (int,float):
                token=ast.get_source_segment(source,node)
                if not re.fullmatch(r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)",token): raise InvalidExpression("Nombre invalide")
                result=Fraction(token)
            elif isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
                result=visit(node.operand,depth+1)*(1 if isinstance(node.op,ast.UAdd) else -1)
            elif isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
                a,b=visit(node.left,depth+1),visit(node.right,depth+1)
                if isinstance(node.op,ast.Add): result=a+b
                elif isinstance(node.op,ast.Sub): result=a-b
                elif isinstance(node.op,ast.Mult): result=a*b
                else: result=a/b
            else: raise InvalidExpression("Opérateur non autorisé")
            if result.numerator.bit_length()>128 or result.denominator.bit_length()>128 or abs(result)>10**12:
                raise InvalidExpression("Calcul hors limites")
            return result
        return visit(tree.body)
    except (SyntaxError,ValueError,ZeroDivisionError,OverflowError,RecursionError) as exc:
        raise InvalidExpression("Expression invalide") from exc

def normalize(value,mode):
    value=unicodedata.normalize("NFC",value).replace("’", "'")
    value=" ".join(value.split())
    if mode=="grammar":value=value.casefold()
    if mode=="formulation":
        value=value.casefold()
        value=re.sub(r"[.,!?;:]", "", value)
    return " ".join(value.split())

def without_accents(value):
    return "".join(c for c in unicodedata.normalize("NFD",value) if not unicodedata.combining(c))

def one_edit(a,b):
    if abs(len(a)-len(b))>1: return False
    if len(a)==len(b): return sum(x!=y for x,y in zip(a,b))==1
    if len(a)>len(b): a,b=b,a
    return any(a==b[:i]+b[i+1:] for i in range(len(b)))

def correct(rule:AnswerRule,response):
    if response is None or response=="" or response==[]: return False,"MISSING_ANSWER"
    if rule.mode=="ordering":
        return (True,None) if isinstance(response,list) and response==rule.expected else (False,"ORDER_ERROR")
    if not isinstance(response,str): return False,"INVALID_FORMAT"
    if rule.mode=="open_writing":return False,"HUMAN_REVIEW"
    if rule.mode=="dictation":
        from .french import dictation_feedback,words
        if words(response)==words(rule.expected):return True,None
        return False,"HUMAN_REVIEW" if dictation_feedback(rule,response)["needs_review"] else "DICTATION_ERROR"
    if rule.mode=="number":
        if rule.decimal_only and not re.fullmatch(r"[+-]?\d+(?:[.,]\d+)?",response.strip()):return False,"INVALID_NUMBER"
        try: okay=calculate(response)==calculate(rule.expected)
        except InvalidExpression: return False,"INVALID_NUMBER"
        return (True,None) if okay else (False,"CALCULATION_ERROR")
    if rule.mode=="choice":
        return (True,None) if response==rule.expected else (False,"CHOICE_ERROR")
    normalized=normalize(response,rule.mode)
    accepted=[normalize(x,rule.mode) for x in [rule.expected,*rule.variants]]
    if normalized in accepted: return True,None
    for wrong,code in rule.known_errors.items():
        if normalize(wrong,rule.mode)==normalized: return False,code
    if any(without_accents(normalized)==without_accents(x) for x in accepted): return False,"ACCENT_ERROR"
    if rule.conjugation_key:return False,"CONJUGATION_ERROR"
    if any(one_edit(normalized,x) for x in accepted): return False,"SPELLING_ERROR"
    return False,"SPELLING_ERROR" if rule.mode=="spelling" else "GRAMMAR_ERROR" if rule.mode=="grammar" else "FORMULATION_NOT_RECOGNIZED"

def grade(candidate:Candidate,answers:dict):
    allowed={p.id for p in candidate.parts}
    if not set(answers)<=allowed: raise ValueError("Partie inconnue")
    return [PartResult(part_id=part.id,correct=result[0],error_code=result[1])
        for part in candidate.parts for result in [correct(candidate.answers[part.id],answers.get(part.id))]]

"""Feedback based on explicit editorial evidence, not a guessed mental state."""
from .correctors import calculate, InvalidExpression
from shared.ai.cm2_policy import INSUFFICIENT_CONTEXT


def display_number(value, prefer_fraction=False):
    if value.denominator == 1:
        return str(value.numerator)
    denominator = value.denominator
    for factor in (2, 5):
        while denominator % factor == 0:
            denominator //= factor
    if prefer_fraction or denominator != 1:
        return str(value)
    from decimal import Decimal, localcontext
    with localcontext() as context:
        context.prec = 150
        return format(Decimal(value.numerator)/Decimal(value.denominator), "f").rstrip("0").rstrip(".").replace(".", ",")


def diagnose(rule, response):
    if not isinstance(response, str) or not response.strip():
        return None
    for mistake in rule.misconceptions:
        try:
            from .correctors import normalize
            matches = calculate(response) == calculate(mistake.response) if rule.mode == "number" else normalize(response,rule.mode) == normalize(mistake.response,rule.mode)
        except InvalidExpression:
            matches = False
        if matches:
            return {"category": mistake.category, "message": "Ce résultat peut venir de cette difficulté. " + mistake.hint}
    return None


def correction(candidate, attempted_parts):
    """Only release parts with a non-empty persisted attempt, even in multipart work."""
    result = []
    for part in candidate.parts:
        if part.id not in attempted_parts:
            continue
        rule = candidate.answers[part.id]
        steps = list(rule.solution_steps)
        if not steps:
            # A bare answer is not a detailed mathematical explanation.
            result.append({"part_id": part.id, "steps": [INSUFFICIENT_CONTEXT], "answer": None})
            continue
        answer = rule.expected
        if rule.mode == "number":
            value = calculate(answer)
            answer = display_number(value, prefer_fraction="/" in rule.expected)
        elif rule.mode == "choice":
            answer = next(o.label for o in part.options if o.id == answer)
        elif rule.mode == "ordering":
            labels = {o.id: o.label for o in part.options}
            answer = " → ".join(labels[key] for key in answer)
        result.append({"part_id": part.id, "steps": steps, "answer": answer,"is_example":rule.mode=="open_writing"})
    return result

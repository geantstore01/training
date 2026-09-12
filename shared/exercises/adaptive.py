"""Deterministic bank selection from observed work, with no mastery claim."""
def choose_next(exercises, seen, current_difficulty, correct, assisted=False):
    unseen = [item for item in exercises if item["id"] not in seen]
    if not unseen:
        return {"exercise_version_id": None, "reason": "bank_exhausted"}
    target = max(1, current_difficulty - 1) if not correct else current_difficulty if assisted else min(5, current_difficulty + 1)
    # Prefer the easier item on a tie. Stable identity makes selection reproducible.
    selected = min(unseen, key=lambda item: (abs(item["difficulty"]-target), item["difficulty"], str(item["id"])))
    reason = "remediation" if not correct and selected["difficulty"] <= current_difficulty else "consolidation" if assisted or not correct else "progression"
    return {"exercise_version_id": selected["id"], "reason": reason}

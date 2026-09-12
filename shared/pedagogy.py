from enum import Enum

class EvaluationLevel(str, Enum):
    NOT_EVALUATED = "non_evalué"
    DISCOVERY = "découverte"
    IN_PROGRESS = "en_cours"
    FRAGILE = "fragile"
    MASTERED = "maîtrisé"
    CONSOLIDATED = "consolidé"

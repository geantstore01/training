"""Deterministic virtual instruments. No arbitrary protocols or generated physics.

These are qualitative teaching models, not measurements of a real experiment.
Every accepted setting belongs to a reviewed finite catalogue.
"""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Chapter = Literal["matiere", "digestion", "circuits", "terre"]

class ScienceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    chapter: Chapter
    setting: str = Field(min_length=1, max_length=40)
    hypothesis: str = Field(min_length=3, max_length=1000)

    @model_validator(mode="after")
    def allowed_setting(self):
        if self.setting not in CASES[self.chapter]:
            raise ValueError("Réglage absent du modèle scientifique validé")
        return self

CASES = {
    "matiere": {
        "fondre": ("Laisser fondre le glaçon virtuel", "solide", "liquide", "Le glaçon devient de l’eau liquide.", "La fusion est le passage de l’état solide à l’état liquide."),
        "geler": ("Refroidir l’eau virtuelle jusqu’à sa congélation", "liquide", "solide", "L’eau liquide devient de la glace.", "La solidification est le passage de l’état liquide à l’état solide."),
        "evaporer": ("Laisser l’eau virtuelle s’évaporer", "liquide", "gazeux", "La quantité d’eau liquide diminue. L’eau passe dans l’air sous forme de gaz invisible.", "L’évaporation est un passage de l’état liquide à l’état gazeux. L’eau n’a pas disparu."),
    },
    "digestion": {
        "bouche": ("Observer la bouche", "aliment", "fragments", "Les dents découpent et écrasent l’aliment. La salive le mouille.", "La mastication transforme les aliments dès la bouche."),
        "estomac": ("Observer l’estomac", "fragments", "bouillie", "Les aliments, arrivés par l’œsophage, sont brassés et mélangés aux sucs digestifs.", "La digestion se poursuit dans l’estomac. Elle ne s’y termine pas."),
        "intestin": ("Observer l’intestin grêle", "bouillie", "nutriments", "La transformation se poursuit. Des nutriments traversent la paroi de l’intestin grêle vers le sang.", "Le sang transporte des nutriments vers les organes. Tout l’aliment ne passe pas dans le sang."),
    },
    "circuits": {
        "ouvert": ("Ouvrir l’interrupteur", "circuit", "off", "La lampe est éteinte. La boucle est interrompue au niveau de l’interrupteur.", "Avec l’interrupteur ouvert, le courant ne circule pas dans cette boucle."),
        "ferme": ("Fermer l’interrupteur", "circuit", "on", "La lampe s’allume. Les deux bornes de la pile sont reliées par la boucle avec la lampe.", "La pile et la lampe en bon état sont reliées par une boucle fermée : le courant peut circuler."),
        "debranche": ("Débrancher un fil, interrupteur fermé", "circuit", "off", "La lampe est éteinte. Un fil est débranché : la boucle est coupée.", "Fermer l’interrupteur ne suffit pas si une autre partie de la boucle est interrompue."),
    },
    "terre": {
        "bas": ("Placer la source lumineuse plus bas", "baton", "longue", "Sur ce modèle, l’ombre du même bâton s’allonge quand la source lumineuse est plus basse.", "Pour comparer, on garde le même bâton et on change seulement la hauteur de la lumière."),
        "haut": ("Placer la source lumineuse plus haut", "baton", "courte", "Sur ce modèle, l’ombre du même bâton raccourcit quand la source lumineuse est plus haute.", "La position de la source lumineuse modifie l’ombre. Une ombre seule ne permet pas de connaître la saison."),
    },
}

def observe(payload: ScienceInput) -> dict:
    label, before, after, observation, conclusion = CASES[payload.chapter][payload.setting]
    return {"chapter":payload.chapter,"setting":payload.setting,"label":label,"before":before,"after":after,
        "observation":observation,"reference_conclusion":conclusion,"model_version":"cm2-science-1",
        "limitation":"Modèle qualitatif simplifié. Les tailles et les durées affichées ne sont pas des mesures réelles."}

def public_cases(chapter: str) -> list[dict]:
    return [{"id":key,"label":value[0]} for key,value in CASES[chapter].items()]

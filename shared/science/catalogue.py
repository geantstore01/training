"""Original micro-lessons, aligned to the 2023 CM column (CM2 2026–2027).

Internal codes are not official identifiers. Editorial review remains mandatory.
"""
from shared.exercises.cm2_pack import choice, error
from .engine import public_cases

SOURCE = "https://www.education.gouv.fr/bo/2023/Hebdo25/MENE2314101A"
PDF = "https://www.education.gouv.fr/sites/default/files/document/Annexe%20%E2%80%93%20Programme%20de%20sciences%20et%20technologie%20du%20cycle%203-365166.pdf"

def q(question, options, answer, steps, mistakes=()):
    result=choice(question, options, answer, steps)
    result["rule"]["misconceptions"]=list(mistakes)
    return result

def written(question, example, steps):
    return {"question":question,"response_type":"text","options":[],"rule":{
        "mode":"open_writing","expected":example,"solution_steps":steps}}

def chapter(key,title,objective,page,section,discovery,explanation,words,example,errors,hints,tasks):
    return {"code":"CM2-SCI-LAB-"+key.upper(),"subject":"sciences","chapter":key,"title":title,
        "objective_index":0,"catalogue_objective":objective,"prerequisites":["Distinguer ce que l’on observe et ce que l’on suppose."],
        "discovery":discovery,"explanation":explanation,
        "method":["Je formule une hypothèse : ce que je pense observer.","Je choisis un seul réglage à modifier.",
            "Je note le résultat sans l’inventer.","Je compare le résultat à mon hypothèse et je justifie ma conclusion."],
        "worked_example":example,"verified_equalities":[],"common_errors":errors,"hints":hints,"tasks":tasks,
        "science":{"chapter":key,"vocabulary":[{"word":w,"definition":d} for w,d in words],
            "source":{"url":SOURCE,"pdf_url":PDF,"page":page,"section":section,"programme_version":"sciences-2023-cm2-2026"},
            "success_criteria":[objective,"Justifier une réponse en s’appuyant sur une observation."],
            "experiment":{"title":title,"objective":objective,"mode":"virtual","materials":["L’instrument virtuel à l’écran et le carnet d’observations."],
                "steps":["Choisis ton réglage.","Écris ce que tu penses observer.","Lance l’observation.","Écris ce que le résultat t’apprend."],
                "safety_rules":["Tout se passe à l’écran. Aucun matériel réel n’est nécessaire.","Ne reproduis pas un montage réel sans les consignes de ton enseignant et un adulte."],
                "hypothesis":"Que penses-tu observer avec ce réglage ?","analysis_question":"Quelle observation justifie ta conclusion ?"},
            "settings":public_cases(key)}}

COURSES = [
    chapter("matiere","L’eau dans tous ses états","Distinguer les états de l’eau et reconnaître un changement d’état réversible.",4,"Propriétés de la matière — cours moyen",
        "Un glaçon fond dans un verre. L’eau a-t-elle disparu ou a-t-elle changé d’état ?",
        "La glace est de l’eau solide. L’eau liquide prend la forme du récipient. La vapeur d’eau est un gaz invisible. Un changement d’état ne transforme pas l’eau en une autre matière. La buée visible est faite de petites gouttes, pas de vapeur invisible.",
        [("Fusion","Passage du solide au liquide."),("Solidification","Passage du liquide au solide."),("Évaporation","Passage progressif d’un liquide à l’état gazeux, à sa surface."),("Réversible","Qui peut se produire en sens inverse.")],
        ["Hypothèse : la glace peut redevenir de l’eau liquide.","Observation : après la fonte, le verre contient de l’eau liquide.","Conclusion : l’eau a changé d’état. On peut retrouver de la glace en la refroidissant suffisamment."],
        ["Croire que l’eau disparaît lorsqu’elle s’évapore.","Confondre vapeur d’eau invisible et buée visible."],
        ["Nomme l’état avant et l’état après le changement.","Demande-toi si c’est toujours de l’eau, même si son aspect change."],
        [q("Un glaçon fond. Quel état obtient-on ?",["Liquide","Solide","L’eau n’existe plus"],0,["Le glaçon était solide.","En fondant, il devient liquide : c’est la fusion."],[error("o2","confusion","Un changement d’état n’est pas une disparition.")]),
         q("Une flaque sèche. Quelle explication convient ?",["L’eau devient de la terre","L’eau passe dans l’air sous forme de gaz","L’eau reste forcément liquide au même endroit"],1,["L’eau s’évapore à la surface de la flaque.","Elle passe dans l’air sous forme de vapeur d’eau invisible."],[error("o0","raisonnement","Observe le changement d’état : la matière reste de l’eau.")]),
         written("Dans le modèle, l’eau liquide devient glace puis redevient liquide. Pourquoi dit-on que ce changement est réversible ?","On retrouve l’état liquide après être passé par l’état solide.",["Exemple à comparer avec ton explication : on obtient successivement eau liquide, glace, puis eau liquide.","Retrouver l’état de départ montre ici la réversibilité."])]),
    chapter("digestion","Le voyage des aliments","Localiser des transformations des aliments et relier la nutrition aux besoins des organes.",9,"Alimentation humaine — besoins alimentaires et nutrition humaine — cours moyen",
        "Un morceau de pain entre dans la bouche. Arrive-t-il entier jusqu’aux organes ?",
        "Les aliments apportent de la matière et de l’énergie à notre corps. Les besoins varient notamment avec la croissance et l’activité. Dans la bouche, les dents broient les aliments. Ils passent par l’œsophage vers l’estomac, puis l’intestin grêle. La digestion les transforme. Des nutriments passent de l’intestin grêle dans le sang, qui les transporte vers les organes.",
        [("Mastication","Action de découper et d’écraser avec les dents."),("Œsophage","Tube qui conduit les aliments de la bouche vers l’estomac."),("Nutriment","Petite substance issue notamment des aliments, utilisable par le corps."),("Organe","Partie du corps qui assure un rôle, comme l’estomac.")],
        ["Hypothèse : la transformation commence avant l’estomac.","Observation du modèle : les dents réduisent déjà l’aliment en fragments dans la bouche.","Conclusion : la digestion commence dans la bouche et continue ensuite dans d’autres organes."],
        ["Penser que tout se passe dans l’estomac.","Croire que des morceaux entiers d’aliments circulent dans le sang."],
        ["Suis le trajet depuis la bouche.","Distingue les aliments dans le tube digestif et les nutriments transportés par le sang."],
        [q("Où les dents commencent-elles à transformer un aliment ?",["Dans la bouche","Dans le sang","Dans l’intestin"],0,["La mastication a lieu dans la bouche.","Les dents découpent et écrasent l’aliment."],[error("o1","vocabulaire","Les dents appartiennent à une partie du tube digestif, pas au sang.")]),
         q("Quel rôle joue le sang après le passage de nutriments à travers l’intestin grêle ?",["Il transporte les aliments entiers","Il transporte des nutriments vers les organes","Il remplace les dents"],1,["Des nutriments traversent la paroi de l’intestin grêle.","Le sang les transporte vers les organes."],[error("o0","confusion","Distingue un morceau d’aliment et un nutriment.")]),
         written("Pourquoi un effort physique peut-il augmenter les besoins alimentaires ? Justifie sans donner de conseil de régime.","Lors d’un effort, les organes en activité utilisent davantage d’énergie.",["Pendant un effort, les muscles travaillent davantage et utilisent de l’énergie.","Les aliments contribuent à fournir de la matière et de l’énergie. Les besoins ne sont pas identiques dans toutes les situations."])]),
    chapter("circuits","Mission : allumer la lampe","Prévoir l’effet d’une ouverture dans un circuit électrique simple à une boucle.",7,"Signal et information — électricité — cours moyen",
        "Une lampe de poche ne s’allume pas. La pile est bonne. Une coupure dans la boucle pourrait-elle l’expliquer ?",
        "Dans notre circuit, la pile fournit de l’énergie à la lampe. Le courant peut circuler si les deux bornes de la pile sont reliées par une boucle complète contenant la lampe. Ouvrir l’interrupteur ou débrancher un fil coupe cette boucle. Nous utilisons seulement un modèle virtuel avec une pile et une lampe en bon état.",
        [("Circuit","Ensemble de composants électriques reliés entre eux."),("Boucle fermée","Chemin continu qui relie les deux bornes de la pile à travers les composants."),("Interrupteur","Composant qui ouvre ou ferme le circuit."),("Borne","Point de connexion d’un composant électrique.")],
        ["Hypothèse : ouvrir l’interrupteur éteindra la lampe.","Observation : dans le modèle, la lampe s’éteint quand l’interrupteur s’ouvre.","Conclusion : l’ouverture interrompt la boucle et empêche le courant d’y circuler."],
        ["Croire qu’un seul fil suffit pour relier la lampe à la pile.","Penser que fermer l’interrupteur répare un autre fil débranché."],
        ["Pars d’une borne de la pile et suis tout le chemin.","Le chemin revient-il à l’autre borne en traversant la lampe, sans coupure ?"],
        [q("Dans le modèle, la boucle est fermée et les composants fonctionnent. Que fait la lampe ?",["Elle s’allume","Elle reste éteinte"],0,["La pile et la lampe sont reliées par une boucle fermée.","Le courant peut circuler : la lampe s’allume."]),
         q("L’interrupteur est fermé mais un fil est débranché. La lampe est éteinte. Pourquoi ?",["La boucle est coupée","Une lampe ne peut jamais fonctionner avec une pile","Le fil débranché renforce le courant"],0,["Le fil débranché crée une interruption.","Fermer l’interrupteur ne rétablit pas cette connexion."],[error("o2","raisonnement","Une coupure empêche le passage du courant dans cette boucle.")]),
         written("Tu compares le même circuit avec l’interrupteur ouvert puis fermé. Pourquoi faut-il garder la même pile et la même lampe ?","Pour ne changer qu’un élément et comparer l’effet de l’interrupteur.",["On garde les autres composants identiques et en bon état.","On peut alors relier la différence observée à l’ouverture ou à la fermeture de l’interrupteur."])]),
    chapter("terre","La Terre, le Soleil et les ombres","Situer la Terre dans le système solaire et comparer des ombres en changeant la position de la lumière.",14,"La Terre dans le système solaire ; lumière et ombres, annexe page 7",
        "Dans la cour, l’ombre d’un arbre change au fil de la journée. Qu’est-ce qui peut modifier sa longueur ?",
        "La Terre est une planète du système solaire. Le Soleil est une étoile : il émet de la lumière. Un objet opaque bloque une partie de cette lumière et produit une ombre. On peut comparer des ombres à différents moments, y compris selon les saisons. Une observation isolée ne suffit pas à expliquer les saisons. L’explication complète de leur alternance sera étudiée en sixième.",
        [("Étoile","Astre qui produit sa propre lumière, comme le Soleil."),("Planète","Astre qui tourne autour d’une étoile et n’émet pas sa propre lumière comme elle."),("Opaque","Qui ne laisse pas passer la lumière."),("Ombre portée","Zone moins éclairée sur une surface derrière un objet qui bloque la lumière.")],
        ["Hypothèse : la hauteur de la source lumineuse modifie l’ombre.","Dans le modèle, on garde le même bâton et le même sol.","Observation : la source plus basse donne une ombre plus longue. Conclusion : la position de la lumière compte."],
        ["Confondre le Soleil, une étoile, et la Terre, une planète.","Déduire une saison d’une seule ombre sans connaître les conditions."],
        ["Repère la source de lumière et l’objet qui la bloque.","Pour comparer deux observations, garde le même objet et change seulement la position de la lumière."],
        [q("Quelle phrase situe correctement la Terre ?",["La Terre est une étoile","La Terre est une planète du système solaire","La Terre produit la lumière du Soleil"],1,["Le Soleil est l’étoile du système solaire.","La Terre est l’une des planètes qui tournent autour de lui."],[error("o0","vocabulaire","Une étoile produit sa propre lumière ; la Terre reçoit celle du Soleil.")]),
         q("Pour comparer l’effet de la hauteur de la lumière sur une ombre, que faut-il faire ?",["Changer le bâton et la lumière à chaque fois","Garder le même bâton et modifier seulement la hauteur de la lumière"],1,["Changer plusieurs éléments empêche de savoir lequel produit l’effet.","On garde le même bâton et le même sol, puis on change la hauteur de la source."],[error("o0","protocole","Une comparaison utile fait varier un seul élément à la fois.")]),
         written("L’ombre du même bâton est plus longue lorsque la lumière est plus basse. Que peux-tu conclure sans inventer la saison ?","La position de la source lumineuse modifie la longueur de l’ombre.",["Les deux observations concernent le même bâton.","Le changement de position de la lumière modifie son ombre. Ces seules données ne permettent pas de connaître la saison."])])
]

BY_CHAPTER={entry["chapter"]:entry for entry in COURSES}

def validate_science_metadata(value: dict) -> dict:
    """Fail closed for generated or modified protocols; human edits require a new catalogue version."""
    chapter=value.get("chapter")
    if chapter not in BY_CHAPTER or value != BY_CHAPTER[chapter]["science"]:
        raise ValueError("Protocole, vocabulaire ou référence hors du catalogue scientifique contrôlé")
    return value

def public_catalogue():
    return [{"code":e["code"],"title":e["title"],"objective":e["catalogue_objective"],**e["science"]} for e in COURSES]

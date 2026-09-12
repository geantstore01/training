"""Original CM2 micro-lessons. Bound to the supplied catalogue, never official by assertion.

Each entry works ONE objective, not the whole competency. Three distinct tasks:
mini-check, guided practice, transfer. Private answers stay in AnswerRule.
"""
from copy import deepcopy
from uuid import UUID
from .correctors import calculate
from .schemas import Candidate
from .pipeline import validate
from .coaching import display_number


def number(question, expression, reasoning, unit="", mistake=None):
    value = calculate(expression)
    expected = display_number(value, prefer_fraction=not unit)
    proof = f"{expression} = {expected}"
    return {"question": question, "response_type": "number", "options": [],
        "rule": {"mode": "number", "expected": expected,
            "solution_steps": [reasoning, proof, f"La réponse est {expected}{(' ' + unit) if unit else ''}. Relis l'unité demandée."],
            "verified_equalities": [proof], "misconceptions": [mistake] if mistake else []}}


def choice(question, labels, answer, reasoning):
    return {"question": question, "response_type": "choice", "options": [{"id":f"o{i}","label":label} for i,label in enumerate(labels)],
        "rule": {"mode": "choice", "expected": f"o{answer}", "solution_steps": reasoning}}


def error(response, category, hint):
    return {"response": str(response), "category": category, "hint": hint}


def course(code, title, objective_index, prerequisites, discovery, explanation, method, example, errors, hints, tasks, equalities=()):
    return {"code": "CM2-MATH-"+code, "title":title, "objective_index":objective_index,
        "prerequisites":prerequisites, "discovery":discovery, "explanation":explanation,
        "method":method, "worked_example":example, "verified_equalities":list(equalities),
        "common_errors":errors, "hints":hints, "tasks":tasks}


COURSES = [
    course("ENTIERS", "Les chiffres ont une place", 1, ["Reconnaître unités, dizaines et centaines."],
        "Une bibliothèque compte 3 245 livres. Le chiffre 2 représente-t-il deux livres ou deux cents livres ? Réfléchis à sa place.",
        "Un chiffre n'a pas toujours la même valeur : sa place indique les unités, dizaines, centaines ou milliers.",
        ["Lis les rangs depuis la droite.", "Donne une valeur à chaque chiffre.", "Additionne les valeurs pour vérifier."],
        ["Dans 3 245, il y a 3 milliers, 2 centaines, 4 dizaines et 5 unités.", "3 000 + 200 + 40 + 5 = 3 245."],
        ["Lire le chiffre sans regarder son rang."], ["Écris les noms des rangs sous les chiffres.", "Une centaine vaut 100 unités ; une dizaine en vaut 10."],
        [number("Dans 2 430 livres, quelle est la valeur du chiffre 4 ?", "4*100", "Le 4 est au rang des centaines.", "livres", error(4,"place_value","Regarde le rang du chiffre, pas seulement le chiffre.")),
         number("Une école compte 3 milliers, 2 centaines et 5 unités de cubes. Combien de cubes ?", "3000+200+5", "Écris chaque groupe avec sa valeur, puis additionne.", "cubes"),
         number("Un compteur affiche 40 607. Quelle est la valeur du chiffre 4 ?", "4*10000", "Le 4 occupe le rang des dizaines de milliers.", "unités")], ["3000+200+40+5=3245"]),
    course("COMPARER-ENTIERS", "Quel nombre est le plus grand ?", 0, ["Lire les rangs d'un nombre entier."],
        "Deux stades accueillent 4 250 et 4 205 personnes. Lequel peut accueillir le plus de monde ?",
        "À nombre de chiffres égal, compare depuis la gauche. Le premier rang différent permet de décider.",
        ["Compare le nombre de chiffres.", "S'il est égal, compare les chiffres depuis la gauche.", "Arrête-toi au premier rang différent."],
        ["4 250 et 4 205 ont les mêmes milliers et centaines.", "Au rang des dizaines, 5 est supérieur à 0 : 4 250 est donc plus grand."],
        ["Commencer par les unités."], ["Aligne les rangs.", "Cherche le premier chiffre différent en partant de la gauche."],
        [number("Une salle a 250 places, une autre 205. Écris le nombre le plus grand.","250","Les centaines sont égales ; 5 dizaines sont plus que 0 dizaine."),
         number("Deux communes ont 7 089 et 7 098 habitants. Écris le plus grand nombre.","7098","Les milliers et centaines sont égaux ; 9 dizaines sont plus que 8 dizaines."),
         number("Deux compteurs affichent 99 999 et 100 002. Écris le plus grand nombre.","100002","Un nombre à six chiffres est supérieur à un nombre à cinq chiffres.")]),
    course("DECIMAUX", "Comparer deux prix", 1, ["Repérer la partie entière et les dixièmes."],
        "Un carnet coûte 2,5 € et un autre 2,35 €. Le prix écrit avec le plus de chiffres est-il forcément le plus élevé ?",
        "Compare d'abord les parties entières, puis les dixièmes, puis les centièmes. Un zéro ajouté à droite de la partie décimale ne change pas le nombre.",
        ["Aligne les virgules.", "Écris les mêmes rangs : 2,5 peut s'écrire 2,50.", "Compare de la gauche vers la droite."],
        ["2,5 € s'écrit aussi 2,50 €.", "Les parties entières sont égales ; 5 dixièmes sont plus que 3 dixièmes : 2,5 € est plus cher."],
        ["Croire que 2,35 dépasse 2,5 parce que 35 dépasse 5."], ["Compare d'abord les parties entières des deux nombres.", "Complète les centièmes manquants avec un zéro, puis compare."],
        [number("Quel prix est le plus élevé : 3,2 € ou 3,15 € ? Écris seulement le nombre.","3.2","3,2 = 3,20 ; 20 centièmes sont plus que 15 centièmes.","euros",error("3.15","place_value","Compare des dixièmes avec des dixièmes.")),
         number("Quel ruban est le plus long : 4,08 m ou 4,8 m ?", "4.8", "4,8 = 4,80 : à partie entière égale, 8 dixièmes dépassent 0 dixième.","m"),
         number("Quel sac est le plus lourd : 6,09 kg ou 6,1 kg ?", "6.1", "6,1 = 6,10 et 10 centièmes dépassent 9 centièmes.","kg")]),
    course("ADDITION-SOUSTRACTION", "Aligner avant d'additionner", 0, ["Connaître les unités, dizaines et centaines."],
        "La bibliothèque reçoit 148 livres puis 76 livres. Comment trouver le nombre total de nouveaux livres ?",
        "Pour additionner, place les chiffres de même rang dans la même colonne. Dix unités forment une dizaine.",
        ["Aligne unités sous unités.", "Additionne depuis les unités.", "Si tu obtiens au moins dix, reporte une dizaine dans la colonne suivante.", "Vérifie l'ordre de grandeur."],
        ["148 + 76 : 8 + 6 = 14 unités. J'écris 4 et je retiens 1 dizaine.", "4 + 7 + 1 = 12 dizaines. J'écris 2 et je retiens 1 centaine.", "1 + 1 = 2 centaines. Total : 224 livres."],
        ["Oublier une retenue.", "Aligner les nombres à gauche."], ["Écris les unités dans une même colonne.", "Après chaque colonne, regarde si tu dois reporter une dizaine."],
        [number("Une boîte contient 23 cubes rouges et 14 bleus. Combien de cubes ?","23+14","On réunit les deux groupes.","cubes"),
         number("Une classe reçoit 157 feuilles puis 68 feuilles. Combien au total ?","157+68","On additionne en tenant compte des retenues.","feuilles",error(215,"procedure","Vérifie si la retenue des unités a été ajoutée aux dizaines.")),
         number("Une école commande 267 cahiers puis 158 cahiers. Combien en tout ?","267+158","Additionne unités, dizaines, centaines, avec les retenues.","cahiers")], ["148+76=224","8+6=14","4+7+1=12"]),
    course("MULTIPLICATION", "Des groupes de même taille", 0, ["Connaître les tables et décomposer un entier."],
        "Il y a 4 boîtes de 23 crayons. Faut-il compter les crayons un par un ?",
        "Multiplier permet de compter plusieurs groupes identiques. Tu peux décomposer un nombre pour faciliter le calcul.",
        ["Repère le nombre de groupes et la quantité par groupe.", "Décompose en dizaines et unités.", "Multiplie chaque partie puis additionne."],
        ["4 × 23 = 4 × 20 + 4 × 3.", "80 + 12 = 92 : les boîtes contiennent 92 crayons."],
        ["Additionner le nombre de boîtes et le nombre de crayons par boîte."], ["Chaque boîte apporte la même quantité.", "Sépare les dizaines et les unités avant de multiplier."],
        [number("3 paquets contiennent chacun 6 cartes. Combien de cartes ?","3*6","On compte 3 groupes de 6 cartes.","cartes",error(9,"operation","Il y a plusieurs groupes identiques : quelle opération les réunit ?")),
         number("4 boîtes contiennent chacune 32 crayons. Combien de crayons ?","4*32","4 × 30 = 120 et 4 × 2 = 8. Réunis les deux résultats.","crayons"),
         number("Une école achète 12 lots de 24 cahiers. Combien de cahiers ?","12*24","10 × 24 = 240 ; 2 × 24 = 48. Additionne les deux quantités.","cahiers")], ["4*23=4*20+4*3","80+12=92"]),
    course("DIVISION", "Partager avec un reste", 1, ["Connaître les tables de multiplication."],
        "On partage 17 billes entre 5 enfants, avec le même nombre pour chacun. Peut-on tout distribuer ?",
        "Dans un partage entier, le quotient est le nombre donné à chacun. Le reste ne suffit pas à donner encore une unité à chacun.",
        ["Cherche le plus grand multiple du diviseur qui ne dépasse pas le total.", "Calcule ce qui reste.", "Vérifie : total = diviseur × quotient + reste.", "Le reste doit être plus petit que le diviseur."],
        ["5 × 3 = 15 ; 17 − 15 = 2.", "Chaque enfant reçoit 3 billes et il reste 2 billes. Vérification : 5 × 3 + 2 = 17 ; 2 est plus petit que 5."],
        ["Garder un reste assez grand pour faire encore un tour."], ["Cherche dans la table du diviseur : c'est le nombre de groupes ou la taille d'un groupe.", "Le reste doit être plus petit que le diviseur. Sinon, tu peux encore partager ou former un groupe."],
        [number("On partage 12 billes entre 3 enfants. Combien chacun reçoit-il ?","12/3","3 × 4 = 12 : chacun reçoit 4 billes.","billes"),
         number("On partage 23 billes entre 4 enfants. Chacun en reçoit 5. Combien reste-t-il ?","23-4*5","4 × 5 = 20 billes sont distribuées ; soustrais ce nombre au total.","billes",error(5,"procedure","La question demande le reste, pas le nombre reçu par chacun.")),
         number("Avec 38 cartes, on fait des paquets complets de 6. Après 6 paquets, combien reste-t-il ?","38-6*6","6 × 6 = 36 cartes sont utilisées. Le reste doit être inférieur à 6.","cartes")], ["5*3=15","17-15=2","5*3+2=17"]),
    course("CALCUL-MENTAL", "Passer par un nombre rond", 0, ["Additionner et soustraire des entiers."],
        "Un panier contient 48 pommes et on en ajoute 19. Comment calculer sans poser l'opération ?",
        "Tu peux remplacer un nombre par un nombre rond voisin, puis compenser exactement la différence.",
        ["Repère un nombre proche d'une dizaine.", "Calcule avec cette dizaine.", "Enlève ou ajoute la différence utilisée."],
        ["19 est égal à 20 − 1.", "48 + 20 = 68, puis 68 − 1 = 67 pommes."],
        ["Utiliser une dizaine sans corriger la différence."], ["19 est proche de 20 ; 29 est proche de 30.", "Si tu ajoutes une unité de trop, enlève-la à la fin."],
        [number("Un panier a 25 pommes. On en ajoute 9. Combien maintenant ?","25+10-1","Ajoute 10 puis retire l'unité ajoutée en trop.","pommes"),
         number("Une boîte a 57 jetons. On en ajoute 19. Combien maintenant ?","57+20-1","Ajoute 20 puis retire 1.","jetons",error(77,"procedure","As-tu compensé l'unité ajoutée en trop ?")),
         number("Une caisse contient 136 livres. On en ajoute 29. Combien maintenant ?","136+30-1","Ajoute 30 puis retire 1.","livres")], ["19=20-1","48+20=68","68-1=67"]),
    course("PROBLEMES", "Organiser un problème en deux étapes", 0, ["Additionner, soustraire et multiplier des entiers."],
        "La classe a 3 boîtes de 12 crayons et distribue 8 crayons. Combien lui en reste-t-il ?",
        "Certains problèmes demandent de trouver d'abord une quantité intermédiaire avant de répondre à la question finale.",
        ["Dis ce que tu cherches à la fin.", "Trouve la quantité de départ.", "Calcule le changement.", "Écris la réponse avec son unité."],
        ["Quantité de départ : 3 × 12 = 36 crayons.", "Après distribution : 36 − 8 = 28 crayons. Il reste 28 crayons."],
        ["Utiliser tous les nombres dans une seule opération au hasard."], ["Quelle quantité faut-il connaître avant de retirer les objets ?", "Calcule d'abord le contenu de toutes les boîtes."],
        [number("2 boîtes contiennent chacune 10 crayons. Combien y a-t-il de crayons avant toute distribution ?","2*10","On compte d'abord tous les crayons.","crayons"),
         number("3 boîtes ont chacune 10 crayons. On distribue 7 crayons. Combien reste-t-il ?","3*10-7","D'abord 3 × 10 = 30 crayons ; ensuite on retire les 7 distribués.","crayons"),
         number("4 boîtes ont chacune 15 craies. On utilise 18 craies. Combien reste-t-il ?","4*15-18","D'abord 4 × 15 = 60 craies ; ensuite on retire les 18 utilisées.","craies")], ["3*12=36","36-8=28"]),
    course("LONGUEURS", "Exprimer une longueur en centimètres", 1, ["Lire une mesure et multiplier par 100."],
        "Un ruban mesure 2 m et 30 cm. Comment écrire toute sa longueur en centimètres ?",
        "Un mètre contient 100 centimètres. Pour réunir des longueurs, exprime-les dans la même unité.",
        ["Repère l'unité demandée.", "Transforme les mètres en centimètres.", "Ajoute les centimètres restants."],
        ["2 m = 200 cm.", "200 + 30 = 230 : le ruban mesure 230 cm."],
        ["Additionner directement 2 et 30 sans convertir."], ["Combien de centimètres y a-t-il dans un mètre ?", "Remplace chaque mètre par 100 cm avant d'additionner."],
        [number("Combien de centimètres dans 3 m ?","3*100","Chaque mètre contient 100 cm.","cm",error(30,"unit","Vérifie le nombre de centimètres contenus dans un mètre.")),
         number("Un ruban mesure 2 m et 45 cm. Quelle longueur en cm ?","2*100+45","Convertis 2 m en 200 cm, puis ajoute 45 cm.","cm"),
         number("Deux rubans de 1 m et 25 cm chacun sont mis bout à bout. Quelle longueur totale en cm ?","2*(100+25)","Un ruban mesure 125 cm. Il y a deux rubans.","cm")], ["2*100=200","200+30=230"]),
    course("MASSES-CAPACITES", "Passer des kilogrammes aux grammes", 1, ["Multiplier par 1 000 et additionner."],
        "Un colis pèse 2 kg et 250 g. La balance affiche seulement des grammes : quel nombre doit-elle montrer ?",
        "Un kilogramme vaut 1 000 grammes. La masse d'un objet peut donc s'écrire avec plusieurs unités équivalentes.",
        ["Repère la masse en kilogrammes.", "Multiplie-la par 1 000.", "Ajoute les grammes restants."],
        ["2 kg correspondent à 2 000 g.", "2 000 + 250 = 2 250 : le colis pèse 2 250 g."],
        ["Confondre grammes et kilogrammes.", "Utiliser des litres pour une masse."], ["Un kilogramme contient mille grammes.", "Convertis d'abord tous les kilogrammes, puis réunis les grammes."],
        [number("Combien de grammes dans 3 kg de farine ?","3*1000","Chaque kilogramme contient 1 000 g.","g"),
         number("Un sac pèse 2 kg et 80 g. Quelle masse en grammes ?","2*1000+80","Convertis 2 kg en grammes, puis ajoute les 80 g.","g",error(280,"unit","Un kilogramme vaut 1 000 g, pas 100 g.")),
         number("Une caisse pèse 4 kg et 500 g. On retire 750 g. Quelle masse reste en g ?","4*1000+500-750","Exprime d'abord toute la masse en grammes, puis retire 750 g.","g")], ["2*1000=2000","2000+250=2250"]),
    course("DUREES", "Calculer une durée en passant par l'heure", 1, ["Lire une heure ; savoir qu'une heure vaut 60 minutes."],
        "Un atelier commence à 14 h 45 et finit à 15 h 20. Combien de temps dure-t-il ?",
        "Pour calculer une durée, avance jusqu'à l'heure suivante, puis jusqu'à l'heure d'arrivée. Les minutes se regroupent par 60.",
        ["Calcule les minutes jusqu'à l'heure suivante.", "Ajoute les minutes après cette heure.", "Vérifie que la durée convient à la situation."],
        ["De 14 h 45 à 15 h : 15 minutes.", "De 15 h à 15 h 20 : 20 minutes. Durée totale : 15 + 20 = 35 minutes."],
        ["Compter 100 minutes dans une heure."], ["Une heure compte 60 minutes.", "Dessine deux sauts : jusqu'à l'heure pleine, puis jusqu'à l'arrivée."],
        [number("Combien de minutes entre 10 h 40 et 11 h ?","60-40","On complète 40 minutes jusqu'à 60 minutes.","minutes"),
         number("Un film commence à 16 h 50 et finit à 17 h 25. Quelle durée en minutes ?","60-50+25","Il reste 10 minutes jusqu'à 17 h, puis encore 25 minutes.","minutes",error(75,"unit","Les minutes se regroupent par 60, pas par 100.")),
         number("Une sortie va de 9 h 35 à 11 h 10. Quelle durée en minutes ?","60-35+60+10","Compte 25 minutes jusqu'à 10 h, une heure entière, puis 10 minutes.","minutes")], ["60-45=15","15+20=35"]),
    course("PERIMETRE", "Faire le tour d'un rectangle", 1, ["Identifier les côtés d'un rectangle et additionner."],
        "On veut entourer un jardin rectangulaire de 8 m sur 5 m avec une ficelle. Que doit-on mesurer ?",
        "Le périmètre est la longueur de tout le contour. Dans un rectangle, les côtés opposés ont la même longueur.",
        ["Repère les quatre côtés.", "Écris la longueur de chaque côté.", "Additionne les quatre longueurs dans la même unité."],
        ["Les côtés du jardin mesurent 8 m, 5 m, 8 m et 5 m.", "8 + 5 + 8 + 5 = 26 : il faut 26 m de ficelle."],
        ["Multiplier longueur et largeur : cela calcule l'aire.", "Compter seulement deux côtés."], ["Suis tout le contour avec ton doigt.", "Le rectangle possède deux longueurs et deux largeurs."],
        [number("Un carré a quatre côtés de 3 cm. Quel est son périmètre en cm ?","4*3","Additionne les quatre côtés égaux.","cm"),
         number("Un rectangle mesure 6 cm sur 4 cm. Quel est son périmètre en cm ?","6+4+6+4","Il faut compter les quatre côtés.","cm",error(24,"operation","As-tu mesuré le contour ou la surface intérieure ?")),
         number("Un jardin mesure 12 m sur 7 m. On laisse une ouverture de 2 m. Quelle longueur de clôture faut-il ?","12+7+12+7-2","Calcule tout le contour, puis retire l'ouverture.","m")], ["8+5+8+5=26"]),
    course("AIRE", "Compter la surface d'un rectangle", 1, ["Compter des carreaux et multiplier."],
        "Un rectangle est rempli de 3 rangées de 5 carreaux de 1 cm². Combien de carreaux couvrent l'intérieur ?",
        "L'aire mesure la surface intérieure. Un rectangle a des rangées de même taille : on peut multiplier leur nombre par le nombre de carreaux d'une rangée.",
        ["Vérifie l'unité de chaque carreau.", "Compte les rangées et les carreaux par rangée.", "Multiplie et écris l'unité d'aire."],
        ["3 rangées de 5 carreaux donnent 3 × 5 = 15 carreaux.", "Chaque carreau représente 1 cm² : l'aire est 15 cm²."],
        ["Additionner les côtés au lieu de compter la surface.", "Écrire cm à la place de cm²."], ["Cherche ce qui remplit l'intérieur, pas le contour.", "Compte une rangée, puis le nombre de rangées identiques."],
        [number("2 rangées de 4 carreaux couvrent une figure. Combien de carreaux ?","2*4","Chaque rangée contient 4 carreaux.","carreaux"),
         number("Un rectangle mesure 7 cm sur 3 cm. Quelle aire en cm² ?","7*3","Le rectangle contient 3 rangées de 7 carrés de 1 cm².","cm²",error(20,"operation","Tu as peut-être calculé le contour. Compte les rangées de carrés.")),
         number("Deux tapis rectangulaires de 4 m sur 3 m sont posés sans se chevaucher. Quelle aire totale en m² ?","2*4*3","Un tapis couvre 12 m². Les deux surfaces s'ajoutent.","m²")], ["3*5=15"]),
    course("FRACTIONS", "Nommer les parts égales", 0, ["Partager une unité en parts égales."],
        "Une tarte est partagée en 4 parts égales. Tu en prends 3. Comment écrire la part de tarte prise ?",
        "Le dénominateur, en bas, indique en combien de parts égales l'unité est partagée. Le numérateur, en haut, indique le nombre de parts prises.",
        ["Vérifie que les parts sont égales.", "Compte toutes les parts de l'unité : c'est le dénominateur.", "Compte les parts prises : c'est le numérateur."],
        ["La tarte a 4 parts égales et 3 sont prises.", "La fraction est 3/4 : trois quarts de la tarte."],
        ["Intervertir le nombre de parts prises et le nombre total de parts."], ["Le nombre du bas décrit le partage de toute l'unité.", "Le nombre du haut compte seulement les parts prises."],
        [number("Une tarte est découpée en 4 parts égales. Quel est le dénominateur ?","4","Le dénominateur compte toutes les parts égales de l'unité."),
         number("Une tablette a 8 parts égales. On en prend 3. Écris la fraction prise avec /.","3/8","3 parts sont prises sur les 8 parts égales de la tablette.",mistake=error("8/3","place_value","Le nombre total de parts de l'unité s'écrit en bas.")),
         number("Un ruban a 10 parts égales. On en colorie 7. Écris la fraction non coloriée.","3/10","10 − 7 = 3 parts ne sont pas coloriées ; le partage reste en 10 parts égales.")]),
    course("PROPORTION", "Revenir au prix d'un objet", 1, ["Diviser et multiplier des entiers."],
        "3 cahiers identiques coûtent 6 €. Sans réduction ni supplément, combien coûtent 5 cahiers ?",
        "Quand chaque objet a le même prix, on peut chercher le prix d'un objet, puis multiplier par la quantité voulue.",
        ["Vérifie que le prix par objet reste le même.", "Divise le prix connu par le nombre d'objets.", "Multiplie le prix d'un objet par la nouvelle quantité."],
        ["Un cahier coûte 6 ÷ 3 = 2 €.", "5 cahiers coûtent 5 × 2 = 10 €."],
        ["Ajouter la différence des quantités au prix."], ["Cherche le prix d'un seul objet.", "Multiplie ensuite ce prix par le nombre d'objets demandé."],
        [number("2 stylos identiques coûtent 6 €. Quel est le prix d'un stylo ?","6/2","On partage le prix total entre les deux stylos.","euros"),
         number("3 carnets identiques coûtent 9 €. Combien coûtent 5 carnets, au même prix chacun ?","9/3*5","Un carnet coûte 3 €. Multiplie ce prix par 5.","euros",error(11,"operation","Ajouter deux carnets ne signifie pas ajouter deux euros. Cherche leur prix.")),
         number("4 billets au même tarif coûtent 28 €. Combien coûtent 7 billets ?","28/4*7","Un billet coûte 7 €. Il faut ensuite compter 7 billets.","euros")], ["6/3=2","5*2=10"]),
]


COURSES += [
    course("FIGURES", "Reconnaître un carré grâce à ses propriétés", 0, ["Repérer un côté et un angle droit."],
        "Un carreau carré est tourné sur une pointe. Est-ce encore un carré ? Comment le vérifier ?",
        "Un carré a quatre côtés de même longueur et quatre angles droits. Le tourner ne change pas ces propriétés.",
        ["Compte les côtés.", "Compare leurs longueurs.", "Vérifie les angles droits avec une équerre."],
        ["Un carreau a quatre côtés de 4 cm et quatre angles droits.", "Il est carré, même si un sommet est placé en haut."],
        ["Décider seulement d'après l'orientation de la figure."], ["Imagine que tu tournes la feuille.", "Vérifie les longueurs ET les quatre angles droits."],
        [choice("Combien de côtés possède un carré ?",["3","4","5"],1,["Le carré est un quadrilatère : il possède quatre côtés."]),
         choice("Une figure a quatre côtés égaux et quatre angles droits. Quel nom est le plus précis ?",["Carré","Triangle","Cercle"],0,["Les quatre côtés égaux et les quatre angles droits sont les propriétés d'un carré."]),
         choice("On tourne un carré sans le déformer. Que devient-il ?",["Il reste un carré","Il devient un triangle","On ne peut plus le nommer"],0,["Tourner ne change ni les longueurs des côtés ni les angles.","La figure reste donc un carré."])]),
    course("CONSTRUCTIONS", "Choisir l'instrument adapté", 0, ["Reconnaître une règle, une équerre et un compas."],
        "Tu dois tracer une carte avec un segment de 5 cm et un angle droit. Un seul dessin à main levée suffit-il ?",
        "La règle graduée mesure des longueurs. L'équerre sert à vérifier et tracer un angle droit. Le compas sert à tracer un cercle ou à reporter une longueur.",
        ["Lis ce que tu dois construire.", "Choisis l'instrument qui réalise cette action.", "Place-le soigneusement et vérifie le tracé."],
        ["Pour un segment de 5 cm, je place le zéro de la règle au premier point et marque le second à 5 cm.", "Pour un angle droit, je place le sommet de l'équerre au point demandé et suis ses deux bords perpendiculaires."],
        ["Commencer la mesure au bord de la règle au lieu du zéro."], ["Est-ce une longueur, un angle droit ou un cercle ?", "Associe chaque action à l'instrument qui la contrôle."],
        [choice("Avec quoi mesurer un segment de 6 cm ?",["Règle graduée","Compas seul","Crayon seul"],0,["Les graduations de la règle permettent de mesurer le segment en centimètres."]),
         choice("Quel instrument permet de vérifier l'angle droit du coin d'une carte ?",["Compas","Équerre","Gomme"],1,["L'équerre possède un angle droit que l'on superpose au coin de la carte."]),
         choice("Tu dois tracer un cercle autour d'un point donné. Quel instrument choisis-tu ?",["Équerre","Règle seule","Compas"],2,["La pointe du compas reste au centre.","L'autre branche trace le cercle à distance constante du centre."])]),
    course("SYMETRIE", "Garder la même distance à l'axe", 1, ["Compter les carreaux d'un quadrillage."],
        "Tu plies une feuille sur une ligne verticale. Un point à gauche laisse une marque à droite. Où apparaît-elle ?",
        "Deux points symétriques se superposent quand on plie sur l'axe. Avec un axe vertical sur un quadrillage, ils sont sur la même ligne et à la même distance de chaque côté.",
        ["Repère l'axe vertical.", "Compte les carreaux entre le point et l'axe.", "Reste sur la même ligne et compte autant de carreaux de l'autre côté."],
        ["Le point A est à 3 carreaux à gauche de l'axe.", "Son symétrique est sur la même ligne, à 3 carreaux à droite. Les deux points sont séparés par 6 carreaux."],
        ["Placer le point du même côté de l'axe.", "Changer de ligne."], ["Le point doit passer de l'autre côté de l'axe.", "Garde la même ligne et la même distance à l'axe."],
        [number("Un point est à 2 carreaux à gauche d'un axe vertical. À combien de carreaux à droite se trouve son symétrique ?","2","Les distances à l'axe sont égales.","carreaux"),
         number("A est à 4 carreaux à gauche de l'axe. Quelle distance sépare A de son symétrique, sur la même ligne ?","4+4","Il y a 4 carreaux pour aller à l'axe, puis 4 pour aller au symétrique.","carreaux"),
         choice("Un point est exactement sur l'axe. Où est son symétrique ?",["Au même endroit","Un carreau à droite","Un carreau à gauche"],0,["Lors du pliage, les points de l'axe ne changent pas de place.","Le symétrique est donc le point lui-même."])], ["3+3=6"]),
    course("ANGLES", "Reconnaître un angle droit", 0, ["Repérer l'ouverture formée par deux côtés."],
        "Le coin d'une feuille forme un angle. Si tu prolonges ses côtés, son ouverture change-t-elle ?",
        "Un angle mesure une ouverture. Un angle droit correspond au coin de l'équerre. La longueur des côtés ne change pas cette ouverture.",
        ["Repère le sommet, où se rencontrent les deux côtés.", "Place le sommet de l'équerre au même endroit.", "Aligne un bord et vérifie si l'autre bord suit le second côté."],
        ["Je superpose l'angle droit de l'équerre au coin d'une feuille rectangulaire.", "Les deux bords coïncident avec les côtés : c'est un angle droit."],
        ["Mesurer la longueur des côtés au lieu de leur ouverture."], ["Regarde l'ouverture entre les deux côtés.", "Compare cette ouverture au coin droit de l'équerre."],
        [choice("Quel instrument sert à reconnaître un angle droit ?",["Balance","Équerre","Chronomètre"],1,["L'équerre possède un angle droit pour comparer les ouvertures."]),
         choice("On prolonge les côtés d'un angle droit sans changer leur direction. L'angle devient-il plus grand ?",["Oui","Non"],1,["Prolonger les côtés ne change pas leur direction ni l'ouverture.","L'angle reste droit."]),
         choice("L'ouverture d'un angle est plus petite que celle de l'angle droit de l'équerre. Est-ce un angle droit ?",["Oui","Non"],1,["Les deux ouvertures ne se superposent pas.","L'angle observé n'est donc pas droit."])]),
    course("REPERAGE", "Lire une case puis se déplacer", 1, ["Distinguer lignes et colonnes d'un quadrillage."],
        "Sur un plan, les colonnes A, B, C vont de gauche à droite et les lignes 1, 2, 3 de haut en bas. Comment aller d'une case à l'autre ?",
        "Une case se repère par sa colonne et sa ligne. Le sens des nombres est donné par le plan : lis toujours ses repères.",
        ["Lis la colonne et la ligne de départ.", "Effectue un déplacement à la fois.", "Relis la colonne et la ligne d'arrivée."],
        ["Je pars de A1. Une case à droite m'amène en B1.", "Une case vers le bas m'amène ensuite en B2."],
        ["Confondre la ligne et la colonne.", "Compter la case de départ comme un déplacement."], ["Un pas à droite change la colonne.", "Un pas vers le bas change la ligne, dans le sens indiqué par le plan."],
        [choice("Colonnes A, B, C de gauche à droite. De A1, un pas à droite mène où ?",["A2","B1","C1"],1,["La colonne A devient B ; la ligne reste 1."]),
         choice("Lignes 1, 2, 3 de haut en bas. De B1, deux pas vers le bas mènent où ?",["B2","C3","B3"],2,["Premier pas : B2. Deuxième pas : B3."]),
         choice("Colonnes A à D de gauche à droite ; lignes 1 à 4 de haut en bas. De A2, deux pas à droite puis un vers le bas mènent où ?",["C3","B3","C2"],0,["Deux pas à droite : A2 → B2 → C2.","Un pas vers le bas : C2 → C3."])]),
    course("TABLEAUX", "Croiser une ligne et une colonne", 0, ["Repérer une ligne et une colonne."],
        "Le tableau d'une bibliothèque indique, pour chaque jour, le nombre de romans et de BD empruntés. Où chercher les BD du mardi ?",
        "Pour lire une case d'un tableau, croise la bonne ligne avec la bonne colonne. Chaque titre indique ce que les nombres représentent.",
        ["Lis les titres des lignes et des colonnes.", "Repère la ligne demandée.", "Suis-la jusqu'à la colonne demandée."],
        ["Colonnes : romans, BD. Ligne lundi : 12, 8. Ligne mardi : 15, 6.", "Pour les BD du mardi, je croise la ligne mardi et la colonne BD : je lis 6 BD."],
        ["Lire la bonne colonne sur la mauvaise ligne."], ["Nomme d'abord la ligne que tu cherches.", "Dans cette ligne, repère la colonne qui correspond à la question."],
        [number("Colonnes : romans, BD. Ligne lundi : 10, 7. Combien de BD ont été empruntées lundi ?","7","Dans la ligne lundi, les BD sont dans la deuxième colonne.","BD"),
         number("Colonnes : romans, BD. Lundi : 10, 7. Mardi : 12, 9. Combien de romans ont été empruntés mardi ?","12","Croise la ligne mardi avec la première colonne, romans.","romans"),
         number("Colonnes : romans, BD. Lundi : 10, 7. Mardi : 12, 9. Combien de BD ont été empruntées en tout ces deux jours ?","7+9","Relève les deux nombres de la colonne BD et additionne-les.","BD")]),
    course("GRAPHIQUES", "Lire la valeur d'une graduation", 0, ["Compter des intervalles et multiplier."],
        "Un diagramme montre les livres lus. Son axe commence à 0 et chaque intervalle vaut 5 livres. Une barre monte de 4 intervalles : représente-t-elle 4 livres ?",
        "La hauteur d'une barre se lit avec l'échelle. Le nombre d'intervalles doit être multiplié par la valeur d'un intervalle.",
        ["Lis le point de départ de l'axe.", "Lis la valeur d'un intervalle.", "Compte les intervalles jusqu'au sommet de la barre."],
        ["L'axe commence à 0. Chaque intervalle vaut 5 livres.", "La barre monte de 4 intervalles : 4 × 5 = 20 livres."],
        ["Compter les intervalles sans lire leur valeur."], ["Lis combien vaut un seul intervalle.", "Compte les intervalles à partir de zéro, puis multiplie par leur valeur."],
        [number("Un diagramme part de 0. Chaque intervalle vaut 2 votes. Une barre monte de 3 intervalles. Combien de votes ?","3*2","Trois intervalles de deux votes correspondent à six votes.","votes"),
         number("Un axe part de 0, avec 5 livres par intervalle. Une barre monte de 6 intervalles. Combien de livres ?","6*5","Il faut multiplier les six intervalles par cinq livres.","livres",error(6,"unit","Un intervalle représente plusieurs livres, pas un seul.")),
         number("Un axe part de 0, avec 10 visiteurs par intervalle. Deux barres montent de 4 et 7 intervalles. Combien de visiteurs de plus pour la seconde ?","7*10-4*10","Les barres représentent 70 et 40 visiteurs. Soustrais leurs valeurs.","visiteurs")], ["4*5=20"]),
]


from .math_extension import build_courses
COURSES += build_courses(course,number,choice,error)


def bind_exercises(entry, competency_id, source_ids):
    """Create candidates for the existing editorial API; no publication side effect."""
    candidates=[]
    for index, task in enumerate(entry["tasks"]):
        candidate=Candidate(kind={"choice":"multiple_choice","ordering":"ordering"}.get(task["response_type"],"short_text"),
            instruction=task["question"],parts=[{"id":"main","question":task["question"],"competency_id":competency_id,
                "response_type":task["response_type"],"options":deepcopy(task["options"]),"visual":deepcopy(task.get("visual"))}],
            answers={"main":deepcopy(task["rule"])},source_ids=source_ids,difficulty=index+1,
            hints=[{"level":i+1,"text":hint} for i,hint in enumerate(entry["hints"])])
        report=validate(candidate,{UUID(str(competency_id))},{UUID(str(value)) for value in source_ids})
        if not report.passed: raise ValueError(f"Invalid course {entry['code']}: {report}")
        candidates.append(candidate)
    return candidates


def bind_lesson(entry, competency, source_ids, exercise_ids):
    """Exact objective from caller-supplied catalogue; missing context fails closed."""
    if competency.get("code") != entry["code"] or len(exercise_ids)!=3:
        raise ValueError("Contexte pédagogique incompatible")
    objective=competency["objectives"][entry["objective_index"]]
    if entry.get("catalogue_objective") and objective!=entry["catalogue_objective"]:
        raise ValueError("L'objectif fourni ne correspond pas à cette leçon")
    body={key:deepcopy(entry[key]) for key in ("prerequisites","discovery","explanation","method","worked_example","verified_equalities","common_errors")}
    if entry.get("science"): body["science"]=deepcopy(entry["science"])
    if entry.get("history"): body["history"]=deepcopy(entry["history"])
    body.update(subject=entry.get("subject","mathematiques"),objective=objective,check_exercise_id=str(exercise_ids[0]),practice_exercise_ids=[str(value) for value in exercise_ids[1:]])
    return {"slug":entry["code"].lower()+"-raisonner-v1","kind":"lesson","title":entry["title"],
        "competency_ids":[str(competency["id"])],"source_ids":[str(value) for value in source_ids],
        "body":{"summary":entry["discovery"][:240],"objectives":[objective],"blocks":[{"kind":"paragraph","text":entry["explanation"]}],"cm2":body}}

"""Original, bounded French CM2 lessons. Repository data supplies checked verb forms.

Objectives below are editorial descriptions, not quotations or official identifiers.
The publishing binder still requires the supplied competency and source identifiers.
"""
from .cm2_pack import course, choice
from .french import conjugate


def text(question, expected, steps, mode="grammar", **extra):
    return {"question":question,"response_type":"text","options":[],
        "rule":{"mode":mode,"expected":expected,"solution_steps":steps,**extra}}


def lesson(code,title,objective,discovery,explanation,example,tasks,hints,method=None):
    entry=course(code,title,0,["Lire une phrase courte."],discovery,explanation,
        method or ["Relis la phrase.","Repère les mots utiles.","Applique la règle et justifie ton choix."],
        example,["Répondre sans chercher un indice dans la phrase."],hints,tasks)
    entry.update(code="CM2-FR-"+code,subject="francais",catalogue_objective=objective)
    # Wrong choices trigger an authored clue, never a generated explanation.
    categories={"NATURES":"classe_fonction","FONCTIONS":"accord","OBJETS":"classe_fonction","ATTRIBUT":"classe_fonction","HOMOPHONES":"homophone","LEXIQUE":"lexique","POLYSEMIE":"lexique"}
    for task in tasks:
        if task["response_type"]=="choice":
            task["rule"]["misconceptions"]=[{"response":o["id"],"category":categories.get(code,"procedure"),"hint":hints[0]} for o in task["options"] if o["id"]!=task["rule"]["expected"]]
        elif code=="HOMOPHONES":
            task["rule"]["misconceptions"]=[{"response":"à" if task["rule"]["expected"]=="a" else "a","category":"homophone","hint":hints[0]}]
    return entry


COURSES=[
 lesson("NATURES","Distinguer classe et fonction","Distinguer la classe du mot et sa fonction dans une phrase",
    "Sur une étiquette, tu lis : « Le chat dort. » Le mot chat désigne un animal. Quel rôle joue-t-il dans cette phrase ?",
    "La classe indique la catégorie du mot : nom, verbe, adjectif… La fonction indique son rôle dans la phrase : sujet, complément… Un nom peut avoir différentes fonctions.",
    ["Dans « Le chien aboie », chien est un nom : c'est sa classe.","Le groupe « Le chien » est le sujet du verbe aboie : c'est sa fonction."],
    [choice("Dans « Le chat dort », quelle est la classe du mot chat ?",["Nom","Sujet","Verbe"],0,["Chat désigne un animal. Sa classe est nom. Sujet est une fonction."]),
     choice("Dans « Nina observe le chat », quelle est la fonction du groupe le chat ?",["Nom","Complément d'objet direct","Sujet"],1,["Nina est le sujet. Le chat complète directement le verbe observe : c'est le complément d'objet direct."]),
     choice("Dans « Le chat observe Nina », quelle est la fonction du groupe Le chat ?",["Complément d'objet direct","Adjectif","Sujet"],2,["C'est le chat qui observe. Le groupe Le chat est sujet. Chat reste un nom."])],
    ["Cherche si on demande une catégorie de mot ou un rôle dans la phrase.","Pour le rôle, repère le verbe et le groupe qui commande son accord."]),
 lesson("FONCTIONS","Retrouver un sujet après le verbe","Identifier le sujet même quand il suit le verbe",
    "Dans un récit, tu lis : « Au loin arrivent deux bateaux. » Les bateaux sont placés après le verbe.",
    "Le sujet commande l'accord du verbe. Il peut être placé après le verbe. Déplace le groupe pour vérifier : « Deux bateaux arrivent au loin. »",
    ["Dans « Sous le toit nichent des oiseaux », le verbe est nichent.","Je peux écrire « Des oiseaux nichent sous le toit ». Le sujet est des oiseaux, au pluriel."],
    [text("Dans « Au loin arrivent deux bateaux », recopie le groupe sujet.","deux bateaux",["On peut écrire : Deux bateaux arrivent au loin. Le sujet est deux bateaux."]),
     text("Dans « Près du mur poussent des fleurs », recopie le groupe sujet.","des fleurs",["Des fleurs poussent près du mur. Le sujet des fleurs commande le pluriel poussent."]),
     choice("Dans « Sur la place jouent les enfants », pourquoi écrit-on jouent ?",["Le mot place est singulier","Le sujet les enfants est au pluriel","Tous les verbes prennent ent"],1,["Le sujet les enfants suit le verbe. Il peut être remplacé par ils. Au présent, jouer prend ici -ent."])],
    ["Repère ce qui se passe : quel est le verbe ?","Essaie de placer le groupe qui commande le verbe au début de la phrase."]),
 lesson("OBJETS","Distinguer COD et COI","Distinguer complément direct et complément indirect du verbe",
    "Tu écris : « Lina regarde un film. Lina parle de ce film. » Le verbe se construit différemment.",
    "Le complément d'objet direct (COD) complète le verbe sans préposition. Le complément d'objet indirect (COI) est introduit par une préposition, comme à ou de. Une préposition est un petit mot qui relie des éléments. Tous les groupes avec une préposition ne sont pas des COI : vérifie leur lien avec le verbe.",
    ["Dans « Léo regarde la mer », la mer est COD de regarde.","Dans « Léo parle de la mer », de la mer est COI de parle."],
    [choice("Dans « Je lis un livre », quelle est la fonction de un livre ?",["COD","COI"],0,["Lire se construit ici directement : lire un livre. Un livre est COD de lis."]),
     choice("Dans « Tu penses à ton ami », quelle est la fonction de à ton ami ?",["COD","COI"],1,["Penser à quelqu'un : la préposition à introduit le complément du verbe. C'est un COI."]),
     choice("Dans « Elle parle de son voyage », quelle est la fonction de de son voyage ?",["Sujet","COD","COI"],2,["Parler de quelque chose : de son voyage est un COI du verbe parle."])],
    ["Observe comment le verbe se construit avec son complément.","Cherche une préposition entre le verbe et le complément étudié."]),
 lesson("ACCORDS","Accorder dans le groupe nominal","Accorder déterminant nom et adjectif",
    "Pour décrire des fleurs, tu écris « une petite fleur », puis tu en vois plusieurs.",
    "Dans le groupe nominal, le nom donne son genre (masculin ou féminin) et son nombre (singulier ou pluriel) au déterminant et à l'adjectif. Dans nos exemples réguliers, on ajoute e au féminin et s au pluriel. Il existe d'autres formes à apprendre.",
    ["Une petite fleur devient des petites fleurs.","Fleurs est féminin pluriel. Petites prend e et s ; le déterminant devient des."],
    [text("Complète avec petit : des … maisons.","petites",["Maisons est féminin pluriel. Petit devient petites : e pour le féminin, s pour le pluriel."],known_errors={"petit":"AGREEMENT_ERROR","petite":"AGREEMENT_ERROR","petits":"AGREEMENT_ERROR"}),
     text("Mets au pluriel tout le groupe : un grand arbre.","des grands arbres",["Arbres est masculin pluriel. Grand prend s. Un devient des."],variants=["de grands arbres"]),
     text("Complète avec vert : les feuilles … .","vertes",["Feuilles est féminin pluriel. L'adjectif vert s'accorde : vertes."],known_errors={"vert":"AGREEMENT_ERROR","verte":"AGREEMENT_ERROR","verts":"AGREEMENT_ERROR"})],
    ["Cherche le nom et son genre.","Le nom désigne-t-il une seule chose ou plusieurs ? Accorde aussi l'adjectif."]),
 lesson("ATTRIBUT","Accorder un attribut du sujet","Reconnaître et accorder un adjectif attribut du sujet",
    "Après une promenade, tu écris : « Les filles sont fatiguées. » L'adjectif décrit le sujet.",
    "Un adjectif attribut du sujet donne une caractéristique du sujet par l'intermédiaire d'un verbe comme être ou sembler. Il s'accorde avec le sujet. Adjectif est sa classe ; attribut du sujet est sa fonction.",
    ["Dans « Les routes sont longues », longues est un adjectif attribut du sujet les routes.","Routes est féminin pluriel : longues prend s."],
    [choice("Dans « Le chat est calme », quelle est la fonction de calme ?",["Sujet","Attribut du sujet","COD"],1,["Calme décrit le chat par le verbe être. Sa fonction est attribut du sujet ; sa classe est adjectif."]),
     text("Complète avec content : Les filles sont … .","contentes",["Le sujet les filles est féminin pluriel. L'adjectif attribut s'accorde : contentes."]),
     text("Complète avec prêt : Les garçons semblent … .","prêts",["Le sujet les garçons est masculin pluriel. L'attribut prêts prend s ; l'accent est conservé."])],
    ["L'adjectif décrit-il le sujet à travers le verbe ?","Remplace le sujet par il, elle, ils ou elles pour vérifier son nombre et son genre."]),
 lesson("PHRASE","Repérer une phrase complexe","Distinguer phrase simple et phrase complexe par les verbes conjugués",
    "Tu écris : « Il pleut et je rentre. » Deux faits sont réunis dans une phrase.",
    "Dans les phrases étudiées ici, une phrase simple contient un seul verbe conjugué. Une phrase complexe en contient plusieurs. Un temps composé, comme a chanté, constitue un seul verbe. Un infinitif, comme partir, n'est pas conjugué.",
    ["« Léa lit. » contient un verbe conjugué : phrase simple.","« Léa lit et Tom dessine. » contient lit et dessine : phrase complexe."],
    [choice("« Le chien dort. » : phrase simple ou complexe ?",["Simple","Complexe"],0,["Un seul verbe est conjugué : dort. La phrase est simple."]),
     choice("« Le chien dort pendant que le chat joue. » : simple ou complexe ?",["Simple","Complexe"],1,["Dort et joue sont deux verbes conjugués. La phrase est complexe."]),
     choice("« Elle a chanté avant de partir. » : simple ou complexe ?",["Simple","Complexe"],0,["A chanté est un seul verbe au passé composé. Partir est à l'infinitif. La phrase est simple."])],
    ["Repère les verbes dont la forme change avec le sujet ou le temps.","Compte un auxiliaire et son participe passé comme un seul verbe conjugué."]),
 lesson("HOMOPHONES","Choisir entre a et à","Distinguer le verbe avoir et la préposition à",
    "Sur une carte, tu écris : « Lina a un cadeau à offrir. » Les deux petits mots se prononcent pareil.",
    "A est une forme du verbe avoir au présent. On peut la remplacer par avait. À est une préposition : le remplacement par avait ne convient pas. Des homophones sont des mots qui se prononcent pareil.",
    ["« Tom a faim » devient « Tom avait faim » : on écrit a.","« Je vais à Paris » ne peut pas devenir « Je vais avait Paris » : on écrit à."],
    [text("Complète par a ou à : Il … un vélo.","a",["Il avait un vélo est possible. A est le verbe avoir au présent."],known_errors={"à":"AGREEMENT_ERROR"}),
     text("Complète par a ou à : Elle va … la piscine.","à",["Elle va avait la piscine ne convient pas. À introduit le groupe la piscine."],known_errors={"a":"ACCENT_ERROR"}),
     text("Complète par a ou à : Mon frère … fini son dessin.","a",["Mon frère avait fini est possible. A est l'auxiliaire avoir dans le passé composé a fini."])],
    ["Essaie de remplacer le mot manquant par avait.","Relis toute la phrase avec avait : garde-t-elle une construction correcte ?"]),
 lesson("LEXIQUE","Retrouver une famille de mots","Relier des mots par leur sens et leur formation",
    "Dans un jardin, le jardinier jardine. Ces mots partagent une partie et une idée.",
    "Des mots d'une même famille partagent une base et un lien de sens. Se ressembler ne suffit pas. Un préfixe se place avant la base ; un suffixe se place après. Jardinier est formé avec jardin et le suffixe -ier.",
    ["Lait, laitier et laiterie appartiennent à la même famille : ils sont liés au lait.","Laine commence de façon proche, mais ne parle pas du lait."],
    [choice("Quel mot appartient à la famille de jardin ?",["Jardinier","Jarre","Jambe"],0,["Jardinier contient jardin et désigne une personne qui s'occupe des jardins."]),
     choice("Quel mot est formé avec le préfixe re- dans le sens de faire encore ?",["Renard","Relire","Repas"],1,["Relire signifie lire encore. Re- est ajouté à lire."]),
     choice("Quel mot ne fait pas partie de la famille de terre ?",["Terrain","Terrien","Terrible"],2,["Terrain et terrien sont liés à terre. Terrible n'a pas ce lien de sens."])],
    ["Cherche la partie commune, puis le sens.","Explique comment les deux mots sont liés ; le début des lettres ne suffit pas."]),
 lesson("POLYSEMIE","Choisir le sens grâce au contexte","Comprendre le sens d'un mot dans son contexte",
    "Tu lis « une feuille tombe », puis « écris sur une feuille ». Le même mot change de sens.",
    "Un mot peut avoir plusieurs sens : c'est la polysémie. Le contexte, c'est ce qui est dit autour du mot. Il aide à choisir le sens qui convient.",
    ["« La souris grignote du fromage » : souris désigne l'animal.","« Je clique avec la souris » : souris désigne l'objet qui commande l'ordinateur."],
    [choice("« Pose ton verre sur la table. » Que signifie verre ici ?",["Une matière seulement","Un récipient pour boire","Une couleur"],1,["On peut poser le récipient sur la table. Le contexte indique un objet pour boire."]),
     choice("« Le pied de la chaise est cassé. » Que signifie pied ?",["Une partie du corps","Un élément qui soutient la chaise","Une chaussure"],1,["Le mot chaise indique que pied désigne son support."]),
     choice("« La pièce dure une heure au théâtre. » Quel sens convient à pièce ?",["Monnaie","Salle","Œuvre jouée sur scène"],2,["Théâtre et dure une heure sont les indices : il s'agit d'une œuvre jouée sur scène."])],
    ["Relis les mots placés autour du mot étudié.","Essaie chaque sens dans la phrase et garde celui qui convient à la situation."]),
 lesson("COMPREHENSION","Justifier une déduction avec le texte","Repérer des indices",
    "« Nora ferme son parapluie et secoue ses bottes mouillées. » Le texte ne dit pas directement quel temps il fait.",
    "Une déduction s'appuie sur des indices du texte. Distingue ce qui est écrit et ce que tu proposes. Certaines interprétations sont possibles sans être certaines. Justifie avec des mots du texte.",
    ["Nora a probablement marché sous la pluie.","Je m'appuie sur parapluie et bottes mouillées. Le texte ne permet pas de connaître sa ville."],
    [choice("« Sam enfile ses gants et souffle sur ses doigts. » Quelle déduction est la mieux appuyée ?",["Sam a probablement froid","Sam habite Paris","Sam a dix ans"],0,["Gants et souffle sur ses doigts sont des indices de froid. Aucune ville ni aucun âge n'est donné."]),
     text("« Inès cache un paquet derrière son dos et sourit en voyant son amie. » Propose une explication appuyée sur un indice.","Elle prépare peut-être une surprise : elle cache un paquet.",["Une surprise est possible grâce au paquet caché et au sourire.","D'autres explications justifiées sont possibles. Compare ton indice avec le texte."],mode="open_writing"),
     text("« La salle devient silencieuse. Le rideau se lève. » Explique ce qui va probablement commencer en citant un indice.","Un spectacle va probablement commencer : le rideau se lève.",["Le rideau qui se lève et le silence permettent de proposer un spectacle.","Le texte ne précise pas lequel. Une autre réponse appuyée sur ces indices doit être relue."],mode="open_writing")],
    ["Cherche un détail réellement écrit dans le texte.","Relie ce détail à ton idée avec parce que, sans ajouter une information absente."]),
 lesson("ECRIT-REDIGER","Écrire puis améliorer un petit récit","Rédiger un texte cohérent",
    "Tu veux raconter une sortie imaginaire à la bibliothèque. Ton lecteur doit comprendre l'ordre des événements.",
    "Un récit raconte des événements liés. Prépare un début, une action et une fin. Garde des personnages faciles à reconnaître. Relis le sens, puis les phrases et les accords. Une proposition de texte n'est pas la seule bonne réponse.",
    ["D'abord, Léa entre dans la bibliothèque. Ensuite, elle choisit un conte. Enfin, elle repart avec son livre.","Elle désigne Léa. Les mots d'abord, ensuite et enfin rendent l'ordre clair."],
    [text("Écris une phrase pour présenter un personnage imaginaire qui arrive à la bibliothèque.","Milo entre dans la bibliothèque pour chercher un conte.",["Une phrase possible présente Milo et le lieu.","Vérifie que ta phrase présente un personnage et une action compréhensible, avec une majuscule et un point."],mode="open_writing"),
     text("Écris deux phrases pour raconter le choix d'un livre par ce personnage.","Milo observe les couvertures. Puis il choisit un conte sur les dragons.",["Les deux actions se suivent. Il désigne Milo.","Relis ton texte : le lecteur peut-il comprendre qui choisit et dans quel ordre ?"],mode="open_writing"),
     text("Écris une fin en deux phrases pour ton récit, puis relis les accords.","Enfin, Milo emprunte le livre. Il rentre chez lui avec le sourire.",["Cette fin termine la sortie. Il renvoie au personnage déjà présenté.","Dans ton texte, vérifie le sens, la ponctuation puis chaque accord sujet-verbe. Fais relire ta version."],mode="open_writing")],
    ["Choisis un personnage imaginaire et une action précise.","Relis ce que tu as déjà écrit : garde le même personnage et relie la suite avec puis ou enfin."],
    ["Prépare l'événement à raconter.","Écris une phrase claire à la fois.","Relis le sens, la ponctuation et les accords."]),
 lesson("DICTEE-RELECTURE","Relire une phrase par catégories","Réviser les accords et l'orthographe d'une phrase",
    "Tu relis une courte phrase copiée ou dictée par un adulte. Plusieurs vérifications peuvent être nécessaires.",
    "Relis par étapes : les accords, la conjugaison, les homophones, le choix des mots (lexique), puis leur écriture (orthographe lexicale). Le correcteur de cette activité classe seulement les mots prévus. Une autre modification demande une relecture humaine. Ici, on s'entraîne à la relecture ; ce n'est pas une dictée audio.",
    ["« Les petit chats joue. » devient « Les petits chats jouent. »","Petits s'accorde avec chats au masculin pluriel. Jouent s'accorde au présent avec les chats, remplaçable par ils."],
    [text("Recopie en corrigeant : Les petit chats jouent.","Les petits chats jouent.",["Chats est masculin pluriel. L'adjectif petits prend s. Jouent est déjà accordé au sujet pluriel."],mode="dictation",dictation_targets=[{"position":1,"category":"accord","hint":"Vérifie le nombre du nom chats et l'accord de son adjectif."}]),
     text("Recopie en corrigeant : Les enfants on des vélo.","Les enfants ont des vélos.",["Ont est le verbe avoir au présent, avec le sujet les enfants. On est un pronom.","Des annonce plusieurs vélos : le nom prend s."],mode="dictation",dictation_targets=[{"position":2,"category":"homophone","hint":"Essaie de remplacer ce mot par avaient."},{"position":4,"category":"accord","hint":"Observe le déterminant des et vérifie le nombre du nom."}]),
     text("Recopie en corrigeant : Les enfants chante dans le jardain.","Les enfants chantent dans le jardin.",["Les enfants peut être remplacé par ils : au présent, chanter devient chantent, terminaison -ent.","Le nom jardin s'écrit avec -in. Jardinier aide à retrouver cette base."],mode="dictation",dictation_targets=[{"position":2,"category":"conjugaison","hint":"Repère le sujet pluriel et la terminaison du présent."},{"position":5,"category":"orthographe_lexicale","hint":"Pense au mot de la même famille jardinier pour écrire le lieu."}])],
    ["Relis d'abord les groupes nominaux : déterminant, nom, adjectif.","Vérifie ensuite le sujet du verbe et les mots qui se prononcent pareil."]),
]


def verb_lesson(code,title,tense,verb,persons,rule,example,ending):
    names=["je","tu","il","nous","vous","ils"]
    tasks=[]
    for person in persons:
        key=f"{verb}|indicatif|{tense}|{person}"
        form=conjugate(key)
        tasks.append(text(f"Écris seulement la forme de {verb} pour le sujet {names[person]}, à l'indicatif {title.lower()}.",form,
            [f"Le sujet est {names[person]} : personne {person%3+1}, {'singulier' if person<3 else 'pluriel'}.",
             f"Le mode est l'indicatif ; le temps est le {title.lower()}.",rule,f"La forme vérifiée est {form}. {ending}"],conjugation_key=key))
    return lesson(code,f"Conjuguer au {title.lower()}",f"Conjuguer {verb} au {title.lower()} de l'indicatif",
        f"Pour raconter une journée, tu peux changer le temps du verbe. Exemple : {example[0]}",rule,example,tasks,
        ["Repère le sujet et remplace-le par le pronom demandé.",f"Vérifie le temps demandé : {title.lower()}. {ending}"],
        ["Identifie le sujet et sa personne.","Vérifie le mode indicatif et le temps demandé.","Cherche la forme apprise, puis vérifie sa terminaison et ses accents."])


COURSES += [
 verb_lesson("PRESENT","Présent","present","être",[0,3,4],"Être est irrégulier au présent : ses formes s'apprennent. L'indicatif est un mode utilisé ici pour dire ce qui se passe.",["Elle est dans la cour.","Le sujet elle correspond à la troisième personne du singulier : être au présent donne est."],"N'enlève pas les accents de la forme apprise."),
 verb_lesson("IMPARFAIT","Imparfait","imparfait","avoir",[0,3,5],"L'imparfait sert notamment à décrire ou à raconter une habitude passée. Avec avoir, la base est av- et les terminaisons sont -ais, -ais, -ait, -ions, -iez, -aient.",["Il avait un cartable bleu.","Il est la troisième personne du singulier : av- et -ait donnent avait."],"Choisis la terminaison correspondant à la personne du sujet."),
 verb_lesson("FUTUR","Futur simple","futur","aller",[0,3,5],"Le futur simple situe ici une action à venir. Aller utilise la base ir- : j'irai, tu iras, il ira, nous irons, vous irez, ils iront.",["Demain, elle ira au parc.","Elle est la troisième personne du singulier : ir- et -a donnent ira."],"Au pluriel, distingue -ons, -ez et -ont."),
 verb_lesson("PASSE-COMPOSE","Passé composé","passe_compose","chanter",[0,3,5],"Le passé composé se construit avec un auxiliaire au présent et un participe passé. Pour chanter dans ces phrases, on utilise avoir et chanté. Sans complément d'objet direct placé avant, chanté ne s'accorde pas avec le sujet.",["Hier, elle a chanté.","A est avoir au présent avec elle ; chanté est le participe passé. A chanté forme un seul verbe conjugué."],"Écris l'auxiliaire et le participe passé, en gardant é dans chanté."),
 verb_lesson("PASSE-SIMPLE","Passé simple","passe_simple","chanter",[2,3,5],"Le passé simple raconte notamment des actions dans les récits écrits. Pour chanter : je chantai, tu chantas, il chanta, nous chantâmes, vous chantâtes, ils chantèrent.",["Le soir venu, elle chanta.","Elle est la troisième personne du singulier : chant- et -a donnent chanta."],"Avec nous et vous, vérifie l'accent circonflexe ; avec ils, l'accent grave."),
 verb_lesson("PLUS-QUE-PARFAIT","Plus-que-parfait","plus_que_parfait","chanter",[0,3,5],"Le plus-que-parfait situe une action avant une autre action passée. Il utilise un auxiliaire à l'imparfait et un participe passé. Pour chanter ici : avoir à l'imparfait suivi de chanté, sans accord avec le sujet car aucun COD ne précède.",["Elle avait chanté avant de rentrer.","Avait est avoir à l'imparfait ; chanté est le participe passé. L'action de chanter précède le retour."],"Vérifie la terminaison de l'auxiliaire à l'imparfait et le é du participe passé."),
]

from .french_extension import build_courses
COURSES += build_courses(lesson,text,choice)

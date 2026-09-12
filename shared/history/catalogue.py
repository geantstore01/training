"""Original editorial CM2 chapters. Never automatically published.

The 2020 history curriculum still applies to CM2 in 2026–27. The 2026
curriculum starts in CM2 in September 2027. Codes are internal identifiers.
Historical documents and modern teaching summaries are explicitly distinguished.
"""
from copy import deepcopy
from shared.exercises.cm2_pack import choice, course
from .schemas import HistoryMetadata

PROGRAMME = "https://eduscol.education.gouv.fr/4791/ressources-d-accompagnement-du-programme-d-histoire-et-geographie-au-cycle-3"
THEMES = [
    {"id":"republique", "title":"Le temps de la République", "subtitle":"Des droits, des symboles, une école"},
    {"id":"industrie", "title":"L’âge industriel en France", "subtitle":"Des machines qui changent la vie"},
    {"id":"guerres-europe", "title":"Des guerres mondiales à l’Union européenne", "subtitle":"Comprendre les conflits et construire la paix"},
]

def source(title, url, page, section):
    return dict(title=title,url=url,page=page,section=section)

REPUBLIC=source("Éduscol — Le temps de la République", "https://eduscol.education.gouv.fr/sites/default/files/document/ra16c3higecm2th1tempsrepublique619873pdf-77115.pdf",3,"L’école primaire au temps de Jules Ferry")
REPUBLIC_EARLY={**REPUBLIC,"page":2,"section":"Les étapes de l’installation de la République"}
REPUBLIC_SYMBOLS={**REPUBLIC,"page":3,"section":"Symboles et commémorations républicaines"}
LAW=source("Sénat — Loi du 28 mars 1882", "https://www.senat.fr/evenement/archives/D42/mars1882.pdf",1,"Article 4")
FERRY=source("Sénat — Jules Ferry : politique scolaire", "https://www.senat.fr/connaitre-le-senat/lhistoire-du-senat/dossiers-dhistoire/jules-ferry-le-president-du-senat-au-mandat-le-plus-court/jules-ferry-politique-scolaire.html",None,"Politique scolaire")
INDUSTRY=source("Éduscol — L’âge industriel en France", "https://eduscol.education.gouv.fr/sites/default/files/document/ra16c3higecm2th2ageindustrielfrance619875pdf-77118.pdf",3,"Énergies et machines ; travail à la mine, à l’usine, à l’atelier")
WARS=source("Éduscol — Des guerres mondiales à l’Union européenne", "https://eduscol.education.gouv.fr/sites/default/files/document/ra16c3higecm2th3franceguerresmondialesue619877pdf-77121.pdf",3,"Comment mettre en œuvre le thème dans la classe ?")
ONAC=source("ONACVG — La Seconde Guerre mondiale", "https://eduscol.education.gouv.fr/sites/default/files/document/onac-vg-seconde-guerre-mondialepdf-96627.pdf",1,"Encadré cycle 3 — CM2")
WAR_CONTEXT=source("Ministère de l’Intérieur — La Seconde Guerre mondiale : le contexte", "https://formation-civique.interieur.gouv.fr/fiches-par-journ%C3%A9e/journ%C3%A9e-2/histoire/les-conflits-mondiaux-et-le-nouvel-ordre-mondial/la-deuxieme-guerre-mondiale-1939-1945-le-contexte/", None, "Le contexte et les étapes du conflit")
EUROPE=source("Union européenne — Histoire de l’UE", "https://european-union.europa.eu/principles-countries-history/history-eu_fr",None,"Les décennies de la construction européenne")

def event(key,year,title,explanation,ref,date=None):
    return dict(id=key.replace("-","_"),year=year,date=date or str(year),title=title,explanation=explanation,source=ref)

def place(name,lat,lon,importance,ref):
    return dict(name=name,latitude=lat,longitude=lon,importance=importance,source=ref)

def document(title,ref,content,questions,*,date="Mars 2016",origin="Ministère de l’Éducation nationale",context="Un document pédagogique rédigé bien après les événements.",shows="Il présente des repères pour comprendre cette période.",limits="Cette synthèse n’est pas un témoignage d’une personne qui a vécu les événements.",kind="synthèse pédagogique institutionnelle",presentation="reformulation"):
    return dict(title=title,type=kind,date=date,origin=origin,context=context,content=content,presentation=presentation,shows=shows,limits=limits,questions=questions,source=ref)

def order(question,events,steps):
    # Deliberately shuffled in the prompt; the canonical answer remains server-side.
    ids=[e["id"] for e in events]
    return dict(question=question,response_type="ordering",options=[dict(id=e["id"],label=e["title"]) for e in reversed(events)],rule=dict(mode="ordering",expected=ids,solution_steps=steps))

def written(question,answer,steps):
    return dict(question=question,response_type="text",options=[],rule=dict(mode="open_writing",expected=answer,solution_steps=steps))

def chapter(key,theme,title,period,objective,discovery,explanation,timeline,vocabulary,doc,tasks,*,figures=None,places=None,causes=None,consequences=None,refs=None,sensitive=False):
    hints=["Repère le document, sa date et les mots de la consigne.","Compare les dates et le sens des mots. Appuie ton explication sur un élément du document."]
    entry=course(key.upper(),title,0,["Lire une date et comparer deux années."],discovery,explanation,
        ["Je repère la date, le lieu et l’origine du document.","Je distingue ce qui est montré de ce que je suppose.","Je replace l’événement sur la frise.","Je justifie ma réponse avec un indice précis."],
        ["Une date situe un événement ; une période dure plusieurs années.","Un document peut expliquer une règle sans prouver que tout le monde l’a immédiatement respectée."],
        ["Confondre une date et une période.","Confondre une cause et une conséquence.","Prendre une règle écrite pour la description de toutes les situations."],hints,tasks)
    entry.update(code="CM2-HIST-"+key.upper(),subject="histoire",chapter=key,catalogue_objective=objective)
    for task in tasks:
        if task["response_type"]=="choice":
            task["rule"]["misconceptions"]=[dict(response=o["id"],category={"ferry":"date","republique":"vocabulaire","industrie":"cause","guerre-14":"vocabulaire","guerre-39":"date","europe":"cause"}.get(key,"document"),hint=hints[0]) for o in task["options"] if o["id"]!=task["rule"]["expected"]]
    meta=dict(chapter=key,theme=theme,period=period,programme_version="histoire-2020-cm2-2026",sensitive=sensitive,
        essential_question=discovery,timeline=timeline,figures=figures or [],places=places or [],
        causes=causes or [],consequences=consequences or [],vocabulary=[dict(word=w,definition=d) for w,d in vocabulary],
        document=doc,sources=refs or [doc["source"]],success_criteria=[objective,"Justifier une réponse avec une information sourcée."],
        remediation=["Reviens aux deux premières dates de la frise.","Dis quel événement vient avant l’autre.","Relis le document et distingue ce qu’il dit de ce qu’il ne permet pas de savoir."])
    entry["history"]=HistoryMetadata.model_validate(meta).model_dump(mode="json")
    return entry

FERRY_EVENTS=[event("gratuite",1881,"Gratuité de l’école primaire publique","La loi du 16 juin supprime les frais de scolarité dans les écoles primaires publiques.",FERRY),event("instruction",1882,"Instruction obligatoire et enseignement laïque","La loi du 28 mars rend l’instruction obligatoire de six à treize ans. L’enseignement religieux est séparé de l’enseignement public.",LAW)]
REPUBLIC_EVENTS=[event("premiere",1792,"Première République","La monarchie est abolie. La France connaît une première République.",REPUBLIC_EARLY),event("troisieme",1870,"Troisième République","Une nouvelle République est proclamée. La République n’a pas été continue depuis 1792.",REPUBLIC_EARLY),event("centenaire",1892,"Centenaire de la République","On célèbre les cent ans de la première République.",REPUBLIC_EARLY)]
INDUSTRY_EVENTS=[event("siecle",1801,"Début du XIXe siècle","Un repère de lecture : l’industrialisation est progressive, pas un événement survenu en une seule journée.",INDUSTRY),event("fin-siecle",1900,"Au tournant du XXe siècle","L’industrie et les transports se sont développés. Le monde rural reste très important en France.",INDUSTRY)]
WW1_EVENTS=[event("debut-14",1914,"Début de la Première Guerre mondiale","Le conflit engage de nombreux pays et leurs empires.",WARS),event("armistice",1918,"Armistice du 11 novembre","Les combats cessent sur le front occidental. Un armistice n’est pas un traité de paix.",WARS)]
WW2_EVENTS=[event("debut-39",1939,"Début de la Seconde Guerre mondiale en Europe","L’Allemagne nazie envahit la Pologne. La France et le Royaume-Uni lui déclarent la guerre.",WAR_CONTEXT),event("france-40",1940,"Défaite et occupation de la France","Le régime de Vichy collabore avec l’Allemagne nazie. Des personnes résistent.",WAR_CONTEXT),event("fin-europe",1945,"Fin de la guerre en Europe","Le 8 mai marque la victoire des Alliés en Europe. La guerre mondiale se termine en septembre.",WAR_CONTEXT)]
EU_EVENTS=[event("schuman",1950,"Déclaration Schuman","Une proposition de coopération pour rendre une nouvelle guerre plus difficile.",EUROPE),event("rome",1957,"Traités de Rome","Six pays fondent la Communauté économique européenne.",EUROPE),event("union",1993,"Naissance de l’Union européenne","Le traité de Maastricht, signé en 1992, entre en vigueur en 1993.",EUROPE)]

COURSES=[
chapter("ferry","republique","L’école primaire au temps de Jules Ferry","Fin du XIXe siècle",
    "Distinguer gratuité, obligation d’instruction et laïcité dans les lois scolaires de 1881 et 1882.",
    "Tu retrouves une ancienne loi sur l’école. Qu’est-ce qui change pour les enfants en 1881 et 1882 ?",
    "Des écoles existaient avant Jules Ferry. En 1881, l’école primaire publique devient gratuite. En 1882, l’instruction devient obligatoire pour les filles et les garçons de six à treize ans. Elle peut être reçue à l’école ou dans la famille selon la loi de l’époque. L’enseignement public devient laïque : il est séparé de l’enseignement religieux. Ces changements aident à former des citoyens, mais ne suppriment pas toutes les inégalités.",
    FERRY_EVENTS,[("Gratuit","Sans frais de scolarité dans l’école primaire publique."),("Instruction","Apprentissage de connaissances et de savoir-faire."),("Laïque","Séparé de l’enseignement religieux dans l’école publique."),("Loi","Règle votée qui s’applique à la société.")],
    document("Que dit la loi de 1882 ?",LAW,"L’instruction primaire est obligatoire pour les enfants des deux sexes",["Qui est concerné par les mots « des deux sexes » ?","Le texte parle-t-il d’instruction ou seulement de présence dans une école publique ?","Pourquoi faut-il lire ce texte dans son contexte de 1882 ?"],date="28 mars 1882",origin="Loi française, article 4, conservée et présentée par le Sénat",context="La Troisième République transforme l’enseignement primaire. La suite de l’article précise les âges et les lieux possibles d’instruction.",shows="La loi impose l’instruction aux filles comme aux garçons.",limits="La loi ne prouve pas que chaque enfant fréquente immédiatement une école, ni que les inégalités disparaissent.",kind="texte de loi",presentation="court extrait"),
    [choice("Quelle mesure concerne 1881 ?",["La gratuité de l’école primaire publique","La création de la première école de France","L’obligation jusqu’à seize ans"],0,["La loi de 1881 instaure la gratuité du primaire public.","L’école existait avant ces lois. Les âges actuels ne doivent pas être projetés en 1882."]),
     order("Remets ces deux lois dans l’ordre chronologique.",FERRY_EVENTS,["1881 vient avant 1882.","La gratuité précède la loi sur l’instruction obligatoire et la laïcité."]),
     written("La loi de 1882 prouve-t-elle que chaque enfant va immédiatement à l’école publique ? Justifie avec une limite du document.","Non. Une obligation d’instruction ne prouve pas la fréquentation de l’école publique par tous.",["Le texte établit une obligation d’instruction.","Il permet aussi l’instruction dans la famille. Il ne décrit pas la vie de chaque enfant.","Ta justification est à relire avec un enseignant ; plusieurs formulations sont possibles."])],
    figures=[dict(name="Jules Ferry",born=1832,died=1893,role="Responsable politique républicain qui porte les lois scolaires.",remember="Il participe à la transformation de l’école primaire.",confusion="Il n’a pas inventé l’école et n’a pas agi seul : les lois sont votées par le Parlement.",event_ids=["gratuite","instruction"],source=FERRY)],
    places=[place("Paris",48.86,2.35,"Lieu des institutions nationales où sont discutées les lois.",FERRY)],
    causes=["Les républicains veulent développer l’instruction et former des citoyens."],consequences=["Les frais de scolarité sont supprimés dans le primaire public.","L’instruction devient obligatoire pour les deux sexes entre six et treize ans."],refs=[REPUBLIC,LAW,FERRY]),
chapter("republique","republique","1892 : pourquoi célébrer un centenaire ?","1792–1892",
    "Situer le centenaire de 1892 et comprendre que la République s’installe progressivement.",
    "Sur une médaille, tu lis 1792–1892. Pourquoi ces deux années sont-elles associées ?",
    "Un centenaire rappelle un événement survenu cent ans plus tôt. En 1892, on célèbre la première République de 1792. Entre ces dates, la France a aussi connu des monarchies et des empires. La Troisième République est proclamée en 1870. Ses symboles contribuent à la faire connaître. Les droits démocratiques se construisent progressivement : tous les adultes ne votent pas encore à cette époque.",
    REPUBLIC_EVENTS,[("République","Organisation politique où le pouvoir n’est pas transmis à un roi par héritage."),("Centenaire","Anniversaire de cent ans."),("Symbole","Signe qui représente une idée ou une communauté.")],
    document("Lire deux dates",REPUBLIC_SYMBOLS,"Les célébrations de 1892 rappellent la naissance de la première République en 1792.",["Quel événement est célébré ?","Combien d’années séparent les deux repères ?","Pourquoi ces dates ne prouvent-elles pas un siècle de République continue ?"]),
    [choice("Que signifie centenaire ?",["Un anniversaire de dix ans","Un anniversaire de cent ans","Un changement de siècle"],1,["Un centenaire est un anniversaire de cent ans."]),order("Classe les trois événements.",REPUBLIC_EVENTS,["1792 précède 1870, qui précède 1892."]),written("Pourquoi ne peut-on pas dire que la France est restée une République sans interruption entre 1792 et 1892 ?","Elle a aussi connu des monarchies et des empires.",["Entre les expériences républicaines, d’autres régimes ont existé.","Célébrer un centenaire ne signifie pas cent années sans interruption."])],
    places=[place("Paris",48.86,2.35,"Un lieu des institutions et des célébrations nationales.",REPUBLIC)],causes=["Les républicains souhaitent faire connaître et accepter la République."],consequences=["Les commémorations et les symboles construisent des repères communs."],refs=[REPUBLIC_EARLY,REPUBLIC_SYMBOLS]),
chapter("industrie","industrie","Machines, ouvriers et villes en mouvement","XIXe siècle",
    "Relier les énergies et les machines aux transformations du travail et des lieux de vie.",
    "Un atelier travaille avec des outils à main. Une usine utilise des machines. Qu’est-ce qui peut changer ?",
    "Au XIXe siècle, le charbon fournit de l’énergie à de nombreuses machines à vapeur. Les usines rassemblent machines et ouvriers. Le chemin de fer facilite les transports. Des villes industrielles grandissent, mais beaucoup de Français vivent encore dans les campagnes. Des femmes, des hommes et des enfants travaillent dans des conditions souvent difficiles. Les transformations sont progressives et différentes selon les lieux.",
    INDUSTRY_EVENTS,[("Énergie","Ce qui permet notamment de faire fonctionner une machine."),("Usine","Lieu où des ouvriers fabriquent des produits à l’aide de machines."),("Ouvrier","Personne qui effectue un travail de fabrication, d’extraction ou de construction."),("Industrialisation","Développement de la production avec des machines et des usines.")],
    document("Une transformation progressive",INDUSTRY,"L’industrialisation transforme les façons de produire. Les villes se développent sans faire disparaître les campagnes.",["Quels lieux de travail sont évoqués dans le cours ?","Les campagnes disparaissent-elles ?","Pourquoi faut-il étudier un lieu précis pour connaître les conditions de travail ?"]),
    [choice("Quelle énergie alimente de nombreuses machines à vapeur ?",["Le charbon brûlé pour chauffer l’eau","Internet","Une pile de téléphone"],0,["Le charbon fournit de la chaleur. L’eau chauffée produit de la vapeur qui peut actionner un mécanisme."]),choice("Quelle relation de cause à conséquence convient ?",["Le développement d’usines attire des travailleurs vers certaines villes","Toutes les campagnes disparaissent en une année","Les téléphones créent les mines au XIXe siècle"],0,["L’emploi industriel contribue à la croissance de certaines villes.","Le changement est progressif et n’efface pas le monde rural."]),written("Pourquoi le développement des usines ne signifie-t-il pas que toute la France vit de la même façon ?","Les activités et les lieux de vie restent différents, notamment entre villes et campagnes.",["Les transformations varient selon les régions et les métiers.","Le monde rural reste important. Compare des situations précises."])],
    places=[place("Le Creusot",46.8,4.43,"Un exemple de ville industrielle étudiable dans le thème.",INDUSTRY)],causes=["L’utilisation de machines et de nouvelles sources d’énergie permet de transformer la production."],consequences=["Des usines et des réseaux de transport se développent.","Les conditions de travail et les paysages changent."],refs=[INDUSTRY]),
chapter("guerre-14","guerres-europe","1914–1918 : combattants et civils","1914–1918",
    "Situer la Première Guerre mondiale et distinguer combattants, civils et armistice.",
    "Un monument porte les dates 1914–1918. Que nous aide-t-il à nous rappeler ?",
    "La Première Guerre mondiale oppose de nombreux pays et leurs empires. Les soldats combattent ; les civils subissent aussi le conflit et participent à l’effort de guerre. Le 11 novembre 1918, un armistice arrête les combats sur le front occidental. Se souvenir des victimes aide à comprendre l’importance de la paix. Un monument local ne raconte pas, à lui seul, toute la guerre.",
    WW1_EVENTS,[("Combattant","Personne qui participe aux combats."),("Civil","Personne qui n’appartient pas aux forces combattantes."),("Armistice","Accord qui arrête les combats."),("Commémorer","Rappeler ensemble un événement et les personnes concernées.")],
    document("Un repère de mémoire",WARS,"L’étude d’un monument aux morts permet de relier une mémoire locale à la Première Guerre mondiale.",["Quel type de lieu de mémoire est cité ?","De quelle guerre parle-t-on ici ?","Pourquoi faut-il d’autres documents pour comprendre tout le conflit ?"]),
    [choice("Que signifie armistice ?",["Un arrêt des combats","Une nouvelle déclaration de guerre","Un type d’usine"],0,["Un armistice arrête les combats. Il ne faut pas le confondre avec un traité de paix."]),order("Classe le début du conflit et l’armistice.",WW1_EVENTS,["1914 vient avant 1918."]),written("Pourquoi faut-il parler aussi des civils pour comprendre cette guerre ?","Les civils subissent le conflit et participent à l’effort de guerre.",["La guerre touche aussi les familles, le travail et les lieux de vie.","On ne peut donc pas la raconter uniquement à travers les combats."])],places=[place("Verdun",49.16,5.38,"Un lieu de combats de la Première Guerre mondiale et de mémoire.",WARS)],causes=["Le conflit mobilise de nombreux pays et leurs empires."],consequences=["Combattants et civils sont durablement touchés.","Des lieux de mémoire rappellent les victimes."],refs=[WARS],sensitive=True),
chapter("guerre-39","guerres-europe","1939–1945 : comprendre et se souvenir","1939–1945",
    "Situer la Seconde Guerre mondiale et distinguer occupation, collaboration et Résistance.",
    "Une frise sépare 1939, 1940 et 1945. Quel événement correspond à chaque repère ?",
    "La Seconde Guerre mondiale débute en Europe en 1939. En 1940, la France est vaincue et une partie du territoire est occupée, puis l’occupation s’étend. Le régime de Vichy collabore avec l’Allemagne nazie. Des personnes résistent, en France et depuis l’extérieur. Les nazis persécutent et assassinent les Juifs d’Europe ainsi que les Roms et les Sinti. Nous étudions ces faits avec respect pour les victimes, sans images violentes. La victoire en Europe a lieu en mai 1945 ; la guerre mondiale finit en septembre.",
    WW2_EVENTS,[("Occupation","Contrôle d’un territoire par une armée étrangère."),("Collaboration","Aide apportée ici par le régime de Vichy à l’Allemagne nazie."),("Résistance","Actions pour s’opposer à l’occupant et au régime de Vichy."),("Persécution","Violences et mesures injustes contre des personnes en raison de leur identité ou de leurs convictions.")],
    document("Ce que nous étudions au CM2",ONAC,"Le document propose de partir des lieux de mémoire. Il invite à étudier la Résistance, la collaboration et les persécutions, puis la construction européenne.",["De quels lieux proches des élèves le document propose-t-il de partir ?","Quelles attitudes pendant la guerre sont citées ?","Pourquoi un programme scolaire n’est-il pas un témoignage de l’époque ?"],date="Document pédagogique contemporain ; date de publication non précisée",origin="Office national des combattants et des victimes de guerre"),
    [choice("Quelle année correspond à la défaite française étudiée ici ?",["1882","1940","1957"],1,["La défaite française et le début de l’occupation se situent en 1940."]),order("Replace ces trois étapes dans l’ordre.",WW2_EVENTS,["1939 précède 1940, puis vient 1945."]),written("Pourquoi faut-il distinguer collaboration et Résistance ?","Collaborer aide l’occupant ; résister consiste à s’y opposer.",["Ces mots désignent des attitudes et des actions différentes.","On ne doit pas attribuer la même attitude à toute une population."])],places=[place("France",46.6,2.4,"Territoire où se déroulent occupation, collaboration et actions de Résistance.",ONAC)],causes=["L’expansion de l’Allemagne nazie conduit au conflit en Europe."],consequences=["Des populations subissent guerre et persécutions.","Après la guerre, la recherche d’une paix durable devient essentielle."],refs=[ONAC,WAR_CONTEXT],sensitive=True),
chapter("europe","guerres-europe","Coopérer pour construire la paix","Depuis 1950",
    "Situer quelques étapes de la construction européenne et expliquer l’objectif de coopération.",
    "Après les guerres, comment d’anciens adversaires peuvent-ils apprendre à travailler ensemble ?",
    "Après la Seconde Guerre mondiale, des pays européens cherchent une paix durable. La déclaration Schuman de 1950 propose une coopération. En 1957, six pays créent la Communauté économique européenne. Le traité de Maastricht est signé en 1992 et entre en vigueur en 1993 : l’Union européenne naît. L’Europe est un continent ; l’Union européenne est une organisation de pays. Les deux ne désignent pas exactement la même chose.",
    EU_EVENTS,[("Coopération","Action de travailler ensemble vers un objectif."),("Traité","Accord conclu entre des États."),("Union européenne","Organisation de pays européens qui mettent en commun certaines décisions.")],
    document("Des étapes, pas une seule date",EUROPE,"La construction européenne avance par plusieurs accords. Les traités de Rome et de Maastricht correspondent à des étapes différentes.",["Quels traités sont évoqués ?","Quel traité entre en vigueur en 1993 ?","Pourquoi distingue-t-on la signature d’un traité et son entrée en vigueur ?"],date="Page institutionnelle contemporaine",origin="Union européenne"),
    [choice("Que cherchent notamment les pays qui coopèrent après la guerre ?",["Une paix durable","Une nouvelle guerre","La suppression de toutes les langues"],0,["La coopération contribue au projet de paix durable."]),order("Classe les trois étapes de la construction européenne.",EU_EVENTS,["1950 : déclaration Schuman. 1957 : traités de Rome. 1993 : Union européenne."]),written("Pourquoi Europe et Union européenne ne sont-elles pas deux noms pour exactement la même chose ?","L’Europe est un continent ; l’Union européenne est une organisation politique de pays.",["Le continent est un espace géographique.","L’organisation regroupe certains pays européens et repose sur des traités."])],places=[place("Rome",41.9,12.5,"Ville où sont signés les traités de 1957.",EUROPE)],causes=["La volonté de construire une paix durable après les guerres."],consequences=["Des pays organisent une coopération économique puis politique."],refs=[EUROPE]),
]
BY_CHAPTER={e["chapter"]:e for e in COURSES}

def validate_history_metadata(value):
    checked=HistoryMetadata.model_validate(value).model_dump(mode="json")
    if checked != BY_CHAPTER.get(checked["chapter"],{}).get("history"):
        raise ValueError("Date, document, lieu, personnage ou référence hors du catalogue historique contrôlé")
    return checked

def public_catalogue():
    # No unreviewed historical lesson or private correction exposed to children.
    return {"programme_version":"histoire-2020-cm2-2026","themes":deepcopy(THEMES),"chapters":[
        {"chapter":e["chapter"],"code":e["code"],"title":e["title"],"theme":e["history"]["theme"],"period":e["history"]["period"]} for e in COURSES]}

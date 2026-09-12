# Mathématiques CM2 : parcours de raisonnement

Cette évolution modifie les services existants et l'espace élève. Le prompt fourni
est conservé dans `shared/ai/cm2_policy.py` et injecté dans les appels du planificateur
pour les mathématiques CM2. Les règles essentielles sont aussi appliquées par le
serveur : contexte lié, calculs exacts, indices progressifs et correction après essai.

## Ce qui fonctionne

- 32 micro-leçons originales, chacune liée à une compétence mathématique du catalogue local,
  avec un objectif ciblé, des prérequis, une découverte concrète, une explication,
  une méthode, un exemple résolu et des erreurs fréquentes.
- 96 questions distinctes : une mini-question et deux exercices progressifs par
  micro-leçon. Les réponses, indices et étapes de correction sont écrits et contrôlés.
- Le lecteur montre une idée à la fois. L'élève écrit une réponse et peut expliquer
  sa démarche ; celle-ci est chiffrée avec la réponse dans le service d'évaluation.
- Une mauvaise réponse correspondant à une erreur éditoriale connue déclenche une
  hypothèse précise (rang, opération, unité ou procédure) et un indice. Un nombre
  isolé ne permet pas d'affirmer avec certitude comment l'élève a raisonné.
- Les indices des exercices relus peuvent être servis sans appel au modèle. Deux
  indices existent pour chaque exercice du nouveau pack. Les contrôles de l'enseignant
  et les consentements du tuteur restent appliqués.
- La correction est demandée séparément, après un essai enregistré. Le serveur
  refuse un essai vide et ne révèle pas la correction d'une partie restée vide.
- Pour les parcours personnels, l'exercice suivant est choisi dans la banque publiée
  de la même compétence : difficulté adaptée au résultat et aux aides, exclusion des
  20 derniers exercices vus. Les missions de l'enseignant conservent leur sélection.
- Après une difficulté, l'élève peut refaire l'exercice guidé deux fois avec les indices.
  Une reprise récente, même après une réussite assistée, n'augmente pas la maîtrise.
  Les mécanismes existants de maîtrise et de révision espacée sont conservés.

Les micro-leçons ne constituent **pas un programme annuel complet**. Par exemple,
« addition-soustraction » travaille ici l'addition, « masses-capacités » la conversion
kg/g, et les constructions vérifient le choix d'instrument, pas la précision d'un tracé.
Les figures, tableaux et graphiques ont encore besoin de tâches visuelles et de
manipulation pour couvrir complètement leurs compétences. Le texte libre de démarche
est enregistré, mais il n'est pas prétendument évalué par une IA dans cette version.

## Utilisation des deux dépôts demandés

Les sources ont été clonées et leur code lu. Aucun de leurs serveurs, modèle,
outil `eval`, bibliothèque d'orchestration ou code source n'est embarqué.

| Source examinée | Apport retenu | Réalisation dans ce projet |
|---|---|---|
| [AI_Powered_Math_Tutoring, course_graph.py](https://github.com/feilaz/AI_Powered_Math_Tutoring/blob/c8d10632ef0a8092582585f40760687e875050b4/course/course_graph.py) | Cours structurés, prérequis explicites, problèmes associés | Leçon structurée avec prérequis et trois versions d'exercices distinctes. Le graphe de compétences existant est conservé ; aucun nouveau prérequis officiel n'est inventé. |
| [AI_Powered_Math_Tutoring, tools.py](https://github.com/feilaz/AI_Powered_Math_Tutoring/blob/c8d10632ef0a8092582585f40760687e875050b4/tools.py) | Vérification mathématique hors du dialogue | Correcteur rationnel borné déjà présent, étendu aux égalités des exemples et des corrections. |
| [MathCrew, web_tutor.py](https://github.com/freesoft/MathCrew/blob/5e01c25ce2389464850a6a019d9e95677f3d3867/web_tutor.py) | Banque, historique récent, analyse d'erreur et reprise progressive | Choix déterministe d'exercice inédit, erreurs connues explicites, indices gradués, reprises sans gain artificiel de maîtrise. |

Il s'agit d'une adaptation des principes au socle FastAPI/Next.js existant, et non
d'une installation de LangGraph ou CrewAI. Aucun nouvel entraînement de modèle n'a
été effectué : c'est l'entraînement pédagogique de l'élève qui est modifié.

## Essayer localement

Depuis `D:\codex\training`, lancer :

```powershell
./scripts/start_cm2_preview.ps1
```

Ouvrir [la recette locale](http://127.0.0.1:19093/tests/cm2-preview/).
Elle utilise les véritables composants React, les 22 micro-leçons, le correcteur
et la sélection d'exercices du projet. Le bandeau indique clairement ses limites :
état anonyme en mémoire, pas de comptes réels, pas de PostgreSQL, pas de modèle distant.
Elle ne prouve pas le déploiement ni le fonctionnement de la base de production.
Les PID sont dans `artifacts/cm2-preview/processes.json` ; arrêter ces deux processus
pour fermer la recette. Les réponses disparaissent à l'arrêt de son API.

## Introduire les contenus dans l'application authentifiée

1. Appliquer la migration `0011_cm2_lesson_links` avec le compte de migration habituel.
   Elle autorise le service de contenu à vérifier le statut et la difficulté des
   exercices liés, sans lui donner accès aux réponses privées.
2. Exporter le catalogue actif CM2 depuis le service curriculum et choisir une source
   pédagogique déjà enregistrée dans l'établissement. Les identifiants de la recette
   locale sont synthétiques et ne doivent pas être importés dans l'école.
3. Produire les charges utiles pour les exercices :

```powershell
.venv/Scripts/python.exe -m scripts.export_cm2_training --catalogue catalogue-cm2.json --source-id UUID_SOURCE --output exercices-cm2.json
```

4. Créer les exercices via `POST /exercises` du service exercise, puis les soumettre
   via `/exercises/{exercise_id}/versions/1/submit`. La relecture indépendante existante
   doit confirmer les consignes, les unités, les indices et la pertinence CM2.
5. Après publication des exercices, écrire un fichier JSON associant chaque code
   de compétence aux trois identifiants de **versions publiées**, dans l'ordre
   mini-question, exercice guidé, transfert. Relancer l'export avec
   `--published versions-publiees.json`. Les leçons obtenues sont validées par le schéma.
6. Créer et soumettre ces leçons via le service content et les faire relire dans le
   circuit existant. Une leçon approuvée apparaît dans le parcours personnel.

L'export est local et ne publie rien. Les étapes éditoriales ne sont pas remplacées
par une fausse signature de relecture. Aucune modification n'a été déployée sur le VPS.

## Vérifications reproductibles

```powershell
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m scripts.generate_contracts
cd apps/web
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
npx.cmd playwright test --config playwright.cm2.config.ts
```

La recette navigateur parcourt les décimaux : réponse erronée `3,15`, diagnostic,
correction `3,2` après tentative, deux indices, puis transfert inédit sans indice.
Elle contrôle aussi l'absence de débordement mobile et l'accessibilité du bilan.
Les tests PostgreSQL/Redis restent explicitement ignorés lorsque
`EDU_TEST_INTEGRATION=1` et l'environnement Compose de test ne sont pas disponibles.

## Atelier visuel et dix leçons supplémentaires

L'accueil mathématique comprend six domaines : nombres, calculs, mesures,
géométrie, données et problèmes. La recherche accepte les accents ou leur absence.
Deux outils de découverte permettent de colorier des parts égales et de modifier
un rectangle en observant son aire et son périmètre. Ils ne créent ni tentative
ni score : ce sont des manipulations libres.

Les dix nouveaux ateliers portent sur la soustraction décimale, la fraction d'une
quantité, les fractions décimales, le rangement des décimaux, les contenances,
la monnaie, l'estimation, le reste d'une division, aire/périmètre et le calcul à
partir de données. Ils ajoutent trente exercices originaux, portant le total à 96.
Les exercices de rangement utilisent des éléments déplaçables au clavier ou à
la souris. Les exercices visuels incluent de véritables bandes et quadrillages,
avec une description textuelle accessible.

Le validateur compare aussi la réponse à la géométrie du dessin : fraction
colorée, aire ou périmètre selon la consigne. Une discordance empêche la validation.
Dans les trois exercices de conversion en écriture décimale, une fraction écrite
avec une barre ne suffit pas : une écriture décimale est requise. Les calculs
continuent à employer des fractions exactes, sans dépendre du calcul d'un LLM.
Les réponses privées ne sont pas livrées avec les schémas. La correction complète
en mathématiques reste conditionnée à une tentative enregistrée.

La migration `0014_cm2_math_workshops` ajoute uniquement les nouveaux objectifs ;
elle conserve les anciennes versions. Son retour arrière conserve les lignes pour
ne pas rompre d'éventuelles références publiées. Le script
`python -m scripts.build_math_workshops` régénère son SQL sans écrire dans une base.
L'exporteur `scripts.export_cm2_training` inclut les trente-deux cours et exige le
contexte pédagogique correspondant pour préparer les nouvelles leçons.

Le [livret Éduscol CM2 2026](https://eduscol.education.gouv.fr/sites/default/files/document/2026-livret-accompagnement-mathematiques-cm2-128556.pdf)
et la [page d'accompagnement du programme](https://eduscol.education.gouv.fr/5712/ressources-d-accompagnement-du-programme-de-mathematiques-au-cycle-3)
ont été consultés. Le livret associe manipulations, représentations et verbalisation
au travail sur les fractions et les problèmes. Il présente aussi les probabilités,
qui ne sont pas encore couvertes ici. Cette extension ne constitue donc toujours
pas un programme annuel exhaustif.

Les deux dépôts supplémentaires cités dans le document joint,
[Academic RAG Assistant](https://github.com/ZohaibCodez/academic-rag-assistant) et
[AI_Tutor](https://github.com/098765d/AI_Tutor), ont été examinés comme références
d'architecture. Aucun nouveau moteur RAG, fournisseur IA ou service de ces dépôts
n'est installé par cette extension. Les contenus restent originaux et utilisent
les services existants ; le document joint n'est pas considéré comme une source
officielle, et ses numéros de page d'exemple ne sont pas repris comme références.

Vérifications de cette version : 258 tests Python réussis, 82 tests dépendant des
services ignorés, 5 tests unitaires d'interface, 8 parcours navigateur maths/français,
compilation Next.js et contrôle TypeScript. Les manipulations, filtres, dessins,
corrections protégées et l'accessibilité ordinateur/mobile ont été contrôlés.

Accès direct à l'aperçu local :
`http://127.0.0.1:19093/tests/cm2-preview/?subject=mathematiques`.
Il utilise les contenus et correcteurs réels avec des essais éphémères. Il ne
prétend pas avoir ingéré ces documents dans une base vectorielle active ni avoir
entraîné un modèle. Aucun déploiement distant n'a été réalisé.

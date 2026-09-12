# Module 4 — Exercices et évaluation

Les deux services FastAPI exposent leurs schémas Pydantic v2 et contrats OpenAPI.
Ils réutilisent l’authentification, les ACL Redis et l’isolation par école des
modules précédents. La correction est locale et déterministe : aucun LLM ni
service cloud n’intervient dans la génération livrée ou la notation interne.

## Génération contrôlée

Trois modèles de génération sont disponibles avec une graine reproductible :

- `arithmetic` : additions, problème en deux étapes et classement numérique ;
- `agreement` : accords adjectivaux à partir d’un petit lexique contrôlé ;
- `chronology` : classement d’événements datés fournis par un enseignant/créateur.

Ils produisent les six typologies : `multiple_choice` (QCM), `fill_blanks`
(texte à trous), `short_text` (réponse courte textuelle ou numérique), `step_problem`,
`ordering` et `timeline`. Les identifiants des bonnes options de QCM ne sont pas
constants. Chaque partie correspond à une compétence précise ; une même tentative
peut donc travailler plusieurs compétences sans attribuer toutes ses erreurs à
chacune d’elles.

Les événements historiques et les références de source sont déclarés par l’équipe
pédagogique ; aucun fait historique n’est inventé ni prétendu vérifié automatiquement.
Un créateur peut également soumettre un exercice complet avec `/exercises` : les
mêmes contrôles s’appliquent. Il ne peut pas envoyer du code Python ou des règles
exécutables au moteur.

### Dix étapes effectives

Le rapport enregistré avec chaque version contient un résultat par étape :

1. Validation complète du schéma Pydantic.
2. Limites de taille du candidat et des listes de diagnostics.
3. Cohérence entre typologie et parties ; trous identifiés et problèmes à plusieurs étapes.
4. Identifiants de parties, niveaux d’aide et sources sans doublons.
5. Correspondance exacte entre parties et règles de correction privées.
6. Options distinctes, bonne option existante et permutation complète pour les classements.
7. Règles numériques analysables par le moteur rationnel borné.
8. Règles linguistiques cohérentes et absence de diagnostic contredisant une réponse acceptée.
9. Compétences existantes et sources appartenant à l’école.
10. Autocorrection de chaque réponse de référence par le correcteur effectif.

Une étape en échec empêche la création de la version. Le rapport complet peut
être consulté via `/validate` et les endpoints éditoriaux. PostgreSQL exige dix
contrôles réussis pour une version utilisant le correcteur `controlled-v1`.

Ces contrôles ne démontrent pas à eux seuls la justesse sémantique d’un énoncé.
La cohérence entre énoncé, réponse, compétence et programme doit être contrôlée
lors de la relecture humaine. Les petites familles de génération livrées ne sont
pas un générateur universel couvrant déjà tout le programme CM1–CM2.

## Correcteurs

### Mathématiques

Le moteur emploie `fractions.Fraction` et une visite explicite de l’arbre syntaxique
Python. Il calcule exactement avec les entiers, décimaux et fractions et prend en
charge `+`, `-`, `*`, `/`, parenthèses, virgule décimale, signes et symboles ×/÷.
Ainsi `0,5`, `1/2` et `0.1+0.4` sont équivalents. Les zéros initiaux sont acceptés.

Il n’utilise ni `eval`, ni `sympify`, ni un parseur de chaînes exécutable. Les
expressions sont limitées à 128 caractères, 64 nœuds, douze niveaux d’imbrication,
neuf chiffres consécutifs et des intermédiaires bornés. Fonctions, variables,
puissances, accès à des objets, exposants scientifiques et divisions par zéro
sont refusés. Les unités doivent être annoncées dans la consigne ; ce module
n’effectue pas encore de conversion dimensionnelle automatique.

Le choix d’un interpréteur arithmétique restreint évite notamment les précautions
liées aux parseurs généraux : la [documentation SymPy](https://docs.sympy.org/latest/modules/parsing.html)
indique que `parse_expr` utilise `eval` et n’est pas adapté aux entrées non assainies.
SymPy n’est pas une dépendance de cette livraison.

### Français

Chaque partie possède un mode explicite : `spelling`, `grammar` ou `formulation`.
Les accents sont conservés, les apostrophes Unicode harmonisées et les espaces
normalisés. Orthographe et grammaire restent sensibles à la casse et aux accents.
Les variantes admises doivent être déclarées dans la grille de correction.

Le mode `formulation` tolère en plus la casse et la ponctuation finale/interne
courante (.,!?;:), mais n’invente pas d’équivalence sémantique. Une formulation
inconnue retourne `FORMULATION_NOT_RECOGNIZED` et invite à une vérification humaine.
Elle ne modifie pas la probabilité de maîtrise. L’enseignant peut enrichir la grille
dans une nouvelle version ; l’historique des tentatives antérieures reste immuable.

Les diagnostics incluent accents, orthographe, accord, conjugaison, calcul, choix,
ordre, réponse manquante et format invalide. Les diagnostics d’accord et de
conjugaison sont associés à des erreurs connues dans la grille validée, pas déduits
par un correcteur grammatical général. Une proximité orthographique sert à proposer
un diagnostic, jamais à accepter automatiquement une faute.

## Validation humaine et versions

Le cycle des exercices conserve les statuts du socle :
`draft → in_review → published → retired`. Une décision `rejected` ou
`changes_requested` ramène à `draft`. Le titre d’un rôle administratif seul ne
permet pas d’approuver : le relecteur doit être `teacher` ou `content_creator`,
actif, différent de l’auteur et confirmer sa relecture.

Le prompt, les réponses privées, les paramètres du correcteur et le rapport sont
immuables dès la création de la version. Une modification crée une version nouvelle,
avec `base_version` obligatoire pour détecter les écritures obsolètes. Seul l’auteur
crée les versions et les soumet. La publication d’une nouvelle version retire les
anciennes dans la même transaction ; la version précédente reste disponible pendant
la préparation du brouillon. Les nouvelles tentatives requièrent une version publiée.
Une tentative déjà démarrée garde sa version et reste corrigeable après son retrait.

Les anciens types techniques du socle sont conservés en base. Les API du module 4
n’exécutent que les versions explicitement liées au correcteur contrôlé connu ;
elles refusent de deviner un correcteur pour une version héritée incompatible.

### API exercise-service

Préfixe : `/services/exercise-service`. Toutes les routes métier requièrent un JWT.

| Méthode | Chemin | Accès / effet |
|---|---|---|
| POST | `/validate` | Enseignant/créateur : rapport des dix contrôles |
| POST | `/generate` | Enseignant/créateur : générer un brouillon |
| POST | `/exercises` | Enseignant/créateur : candidat rédigé manuellement |
| GET | `/exercises` | Catalogue publié, paginé, filtrable par compétence |
| GET, POST | `/exercises/{id}/versions` | Historique éditorial / nouvelle version |
| GET | `/exercises/{id}/versions/{n}` | Version publiée, DTO sans corrigé |
| GET | `/exercises/{id}/versions/{n}/editorial` | Équipe pédagogique : règles privées et rapport |
| POST | `/exercises/{id}/versions/{n}/check-answer` | Enseignant/créateur : tester une grille |
| POST | `/exercises/{id}/versions/{n}/submit` | Auteur : soumettre |
| POST | `/exercises/{id}/versions/{n}/reviews` | Relecteur indépendant : décision |
| POST | `/exercises/{id}/versions/{n}/archive` | Auteur ou administrateur : retirer une publication |

Les élèves et parents n’accèdent ni au corrigé privé, ni aux brouillons, ni à
l’endpoint de test d’une réponse. Le prompt public est construit avec un modèle
Pydantic explicite ; aucun `answer_spec` n’est sérialisé vers les élèves.

## Tentatives et historique

L’élève ouvre une session, démarre une tentative avec une clé d’idempotence UUID,
puis soumet ses réponses indexées par identifiant de partie. L’identité de l’élève
vient exclusivement du JWT ; un enseignant ou parent ne soumet pas une réponse à
sa place. Une seule session active est réutilisée par les créations concurrentes.

Un verrou transactionnel par élève sérialise les écritures sans donner au compte
SQL assessment le droit de modifier le profil élève. La soumission enregistre
atomiquement les réponses, le résultat, les preuves de maîtrise et les échéances.
Une répétition de la même requête renvoie le résultat conservé ; des réponses
différentes sur une tentative terminée provoquent 409. Une clé de démarrage
réutilisée pour une autre session/version provoque également 409.

Les réponses sont chiffrées avec AES-256-GCM, un contexte authentifié école/tentative/
partie et une clé versionnée. Le condensat d’idempotence est un HMAC, pas un hash
public permettant de deviner une réponse courte. Les journaux techniques ne
recopient pas les réponses. La consultation des réponses est auditée.

Chaque historique renvoie les dates, la version utilisée et le résultat qualitatif
conservé. Le détail restitue aussi le prompt figé et les réponses de l’élève après
contrôle d’accès. Les tentatives soumises, réponses et preuves ne sont pas modifiées
en place. La politique de conservation, l’export global et l’effacement RGPD complet
restent à définir au niveau de l’exploitation ; ce module ne les prétend pas acquis.

Les aides sont demandées sur une tentative ouverte. Le serveur mémorise le niveau
réellement consulté, sans accepter un niveau d’aide déclaré par le client.

## Maîtrise probabiliste et répétition espacée

L’algorithme versionné `bkt-sm2-v1` combine une mise à jour inspirée de Bayesian
Knowledge Tracing avec une planification de type SM-2. Les paramètres de départ
sont explicites dans `app/algorithms.py`, pas entraînés ni validés statistiquement
sur des élèves français : prior 0,20, devinette 0,20, erreur malgré maîtrise 0,10,
transition d’apprentissage 0,10. Une décroissance temporelle paramétrée avec une
demi-vie de 90 jours et un plancher de 0,05 précède la mise à jour.

La probabilité conditionnelle est calculée par Bayes selon la réussite, puis une
transition d’apprentissage est appliquée. Référence fondatrice :
[Corbett et Anderson, Knowledge Tracing (1995)](https://perso.liris.cnrs.fr/pierre-antoine.champin/2014/m2iade-ia2/_static/893CorbettAnderson1995.pdf).
Les choix supplémentaires de vieillissement, seuils et protection contre les
répétitions sont des paramètres d’ÉDUCAPILOTE, pas des résultats de cet article.

Une observation est appliquée une fois par compétence et tentative. Les parties
associées à cette compétence doivent toutes être réussies pour constituer une
réussite autonome. Refaire la même version sur la même compétence dans les vingt
heures suivant une observation appliquée n’ajoute pas de preuve. Les tentatives
aidées et formulations non reconnues sont conservées sans mise à jour de maîtrise.
La raison (`independent`, `repeated`, `assisted`, `unrecognized`) est persistée.

Les échéances passent typiquement à un jour, six jours, puis un intervalle multiplié
par la facilité bornée. Une réussite avant l’échéance n’allonge pas l’intervalle ;
une erreur réinitialise la répétition à un jour. Le maximum est 365 jours. Ces
règles ne garantissent pas à elles seules une mémorisation à long terme.

Les six états publics restent ceux du module 3. L’état `maîtrisé` demande au moins
cinq observations et une probabilité interne ≥ 0,85 ; `consolidé` demande huit
observations, ≥ 0,95 et au moins trois répétitions espacées réussies. Les API
publiques n’exposent ni probabilité, ni score, ni pourcentage, ni classement d’élèves.
Elles renvoient des états, des retours par étape et la prochaine date de révision.

L’analyse des erreurs regroupe les codes par compétence réelle de la partie et
signale leur récurrence. Les requêtes rejouées ne créent pas de doublons. Les
enseignants ne voient que leurs élèves affectés, les parents leurs liens vérifiés,
et les administrateurs les élèves de leur école.

### API assessment-service

Préfixe : `/services/assessment-service`.

| Méthode | Chemin | Fonction |
|---|---|---|
| POST | `/sessions` | Ouvrir/réutiliser la session de l’élève |
| POST | `/sessions/{id}/complete` | Terminer sa session |
| POST | `/attempts` | Démarrer une tentative idempotente |
| GET | `/attempts/{id}/hints/{level}` | Consulter et comptabiliser une aide |
| POST | `/attempts/{id}/submit` | Corriger et enregistrer une fois |
| GET | `/attempts/{id}` | Détail autorisé, prompt et réponses historiques |
| GET | `/students/{id}/attempts` | Historique paginé |
| GET | `/students/{id}/mastery` | États et dates de révision ; `due_only=true` pour les échéances |
| GET | `/students/{id}/errors` | Types d’erreurs récurrents, pagination |

## Exploitation

La migration 0004 ajoute les preuves de maîtrise et les champs de résultat et
d’idempotence aux tentatives : 41 tables métier, 42 avec Alembic. Les anciennes
migrations sont conservées. Une rétrogradation refusant la perte de données
propres au module 4 est fournie ; les essais de downgrade se font en base jetable.

Exercise et assessment possèdent chacun un utilisateur Redis et un rôle SQL.
Tous deux lisent les sessions JWT mais ne peuvent pas les révoquer ou les modifier.
Seul assessment reçoit la clé PII nécessaire aux réponses ; aucun ne reçoit la
clé privée JWT. Le réseau interne n’autorise aucun appel cloud.

```bash
cd /stockage/training
python3 scripts/init_security_secrets.py
bash scripts/test_module4.sh
# Vérification ciblée possible :
bash scripts/test_module4.sh tests/test_exercise_integration.py -x
bash scripts/verify_migrations.sh
docker compose -f docker-compose.dev.yml build exercise-service assessment-service migrate
docker compose -f docker-compose.dev.yml up -d --no-build
docker compose -f docker-compose.dev.yml restart proxy
bash scripts/verify_restore.sh
python3 scripts/smoke.py
```

Le script de test utilise une base temporaire et Redis DB 15 avec des clés dédiées.
Il ne publie pas les exercices synthétiques de test dans la base active. Les
sources et compétences doivent être saisies et validées par l’équipe pédagogique.
Les contrats JSON complets figurent dans les dossiers des services et Swagger
reste accessible via le tunnel SSH du socle.

# Sciences CM2 — station d’exploration

MVP ajouté à l’application existante : quatre chapitres, onze configurations d’instruments qualitatifs, douze exercices (huit QCM et quatre justifications libres). Le parcours fonctionne sans modèle distant. Les observations sont calculées par un catalogue déterministe ; ce ne sont pas des mesures physiques ni des animations produites par une IA.

## Ouvrir le résultat

[Station sciences locale](http://127.0.0.1:19093/tests/cm2-preview/?subject=sciences).

Si l’aperçu n’est pas déjà lancé, depuis `D:\codex\training` :

```powershell
& scripts/start_cm2_preview.ps1
```

L’aperçu utilise les vrais contenus, schémas, correcteurs et instruments, mais un serveur de recette anonyme. Les essais disparaissent au redémarrage. Il ne simule pas une authentification de production, des embeddings disponibles ou une validation humaine déjà faite.

## Ce que fait l’élève

1. Choisir matière, vivant, circuit ou Terre.
2. Choisir un réglage et écrire une hypothèse avant de lancer l’observation.
3. Lire le résultat déterministe et écrire une conclusion. Deux indices sont disponibles.
4. Comparer sa conclusion à celle du modèle, télécharger son essai, le reprendre depuis le carnet ou changer de réglage.
5. Suivre la leçon en étapes, puis une mini-question et deux exercices progressifs. Les réponses restent privées côté serveur ; la correction est accessible après tentative ou demande explicite.

Une justification libre est signalée « à relire », sans note arbitraire ni mise à jour de maîtrise. Les réponses exactes des QCM utilisent le suivi et la recommandation existants. Avec trois exercices par chapitre, la banque peut être épuisée : l’interface le dit, elle n’invente pas une progression infinie.

Les carnets de production sont chiffrés, isolés par école et par élève, visibles aux parents vérifiés et enseignants autorisés. Conservation de trente jours, purge par le worker existant, effacement par l’élève et suppression en cascade si son profil est supprimé. L’API retourne les cent observations les plus récentes non expirées. Le mode dyslexie, l’agrandissement et la synthèse vocale du parcours existant sont réutilisés ; la synthèse distante n’est pas disponible dans l’aperçu anonyme.

## Référentiel exact

Pour le CM2 en 2026–2027, le programme de sciences de **2023** demeure applicable. Le programme publié en 2026 s’applique au CM2 à partir de 2027–2028. [Calendrier Éduscol](https://eduscol.education.gouv.fr/6878/ressources-d-accompagnement-du-programme-de-sciences-et-technologie-au-cycle-3), [BO de 2023](https://www.education.gouv.fr/bo/2023/Hebdo25/MENE2314101A).

Les références de page désignent l’annexe PDF, numérotée depuis sa première page. Les codes `CM2-SCI-LAB-*` sont internes, pas des identifiants officiels.

| Chapitre | Périmètre du MVP | Annexe |
|---|---|---|
| Matière | États de l’eau, fusion, solidification, évaporation, réversibilité | page 4, colonne CM |
| Alimentation et digestion | Transformation des aliments et transport des nutriments ; besoins liés à l’activité | page 9, colonne CM |
| Circuit | Pile, lampe, interrupteur ; effet d’une coupure dans une boucle | page 7, colonne CM |
| Terre et saisons | Terre dans le système solaire ; observation d’ombres ; limites des conclusions | pages 14 et 7, colonne CM |

Le mécanisme complet des saisons est identifié dans l’annexe comme un objectif de sixième. Le MVP ne le présente pas comme une exigence évaluée de CM2. Il ne couvre pas encore tous les objectifs annuels des quatre domaines.

## Dépôts : intégrations réelles et limites

| Dépôt demandé | Usage effectif |
|---|---|
| [SparkSTEM](https://github.com/ScienceGear/SparkSTEM) | Architecture laboratoire/ressource externe examinée. Inspiration pour séparer instrument local et simulation liée. Aucun code copié : aucune licence racine repérée dans la révision auditée ; ses contenus avancés ne sont pas repris. |
| [rag-tutor](https://github.com/KiavashBahreini7/rag-tutor) | Mode socratique et réflexion de fin de séance examinés, inspiration pédagogique attribuée. Son comptage de questions comme maîtrise et ses clés côté navigateur ne sont pas repris. Aucun moteur de récupération documentaire robuste trouvé dans le HTML examiné : ce dépôt ne remplace pas pgvector. |
| [phetsims](https://github.com/phetsims) | Organisation, pas paquet unique. Lien français fonctionnel vers le circuit PhET depuis l’atelier. Chargement seulement à l’ouverture explicite du site externe. Aucune redistribution des simulations. |
| [openzim/phet](https://github.com/openzim/phet) | Adaptateur de livraison hors ligne : vecteur d’arguments documenté `phet2zim`, exporté en manifeste. Pas de téléchargement massif ni de ZIM prétendument installé. L’installation reste optionnelle. |
| [classquiz](https://github.com/mawoka-myblock/classquiz) | **Sept classes de contrat amont réellement intégrées**, sous MPL-2.0. Les huit questions fermées sont exportées et validées avec `QuizInput`, au format de l’éditeur ClassQuiz. Serveur multijoueur non démarré. |
| [science-questions](https://github.com/joelgrus/science-questions) | **Exclu du corpus** : son README décrit des questions volontairement absurdes (« bogus »). Aucun de ses contenus n’est enseigné. |
| [ai-rag-for-education](https://github.com/reneenoble/ai-rag-for-education) | Fonction de recherche lexicale adaptée sous MIT, sans son corpus commercial. Elle sélectionne les trois extraits CM2 pertinents dans la génération locale de brouillon ; ne remplace pas la recherche hybride/pgvector existante. |

Les commits et licences sont recensés dans [THIRD_PARTY.md](THIRD_PARTY.md). Aucun de ces dépôts ne constitue à lui seul un programme CM2 français validé.

## Architecture et fichiers complets

```text
shared/science/
  catalogue.py         quatre leçons, vocabulaire, sources, indices, exercices
  engine.py            schémas stricts et onze observations déterministes
  source_extract.py    rectangles CM du PDF officiel, vérifiés par SHA-256
  generation.py        génération locale et validation d’un brouillon
  retrieval.py         recherche lexicale issue de Renee Noble
  integrations.py      ClassQuiz et plan openZIM/PhET
  vendor/              contrat ClassQuiz et licence MPL-2.0
shared/ai/
  science_policy.py, science_lesson_prompt.py, science_correction_prompt.py
services/assessment-service/app/science.py    API carnet et instruments
services/retrieval-service/app/               ingestion et recherche hybride
services/content-service/app/                versions, sources, revue indépendante
migrations/versions/0015_cm2_science_labs.py
migrations/sql/0015_cm2_science_labs.sql
apps/web/src/components/
  science-library.tsx, science-lab.tsx, science-instrument.tsx
  science-workshop.css
tests/test_science_training.py
apps/web/tests/browser/cm2.spec.ts
```

Le module étend PostgreSQL/FastAPI/Redis/pgvector/Next existants. Il ajoute `science_runs` (notes chiffrées, identifiant d’idempotence, observation, dates, clés étrangères composites, RLS) et autorise `sciences` dans les documents RAG. Il ne duplique pas l’authentification, les règles de consentement, les évaluations ou les services de cours.

## APIs et workflow éditorial

Les chemins ci-dessous sont ceux du service assessment ; le frontend les appelle via `/api/assessment/...`.

| Méthode | Chemin | Effet |
|---|---|---|
| GET | `/science/catalogue` | Paramètres et protocoles publics, session requise |
| POST | `/science/runs` | Hypothèse obligatoire, réglage autorisé, observation et carnet |
| POST | `/science/runs/{id}/conclusion` | Conclusion de l’élève propriétaire, sans score automatique |
| GET | `/science/notebook/{student_id}` | Accès élève, parent vérifié ou enseignant autorisé |
| DELETE | `/science/notebook/{student_id}` | Effacement de son carnet par l’élève |

L’ingestion utilise `/documents/ingest`, `/documents/{id}/submit` et `/documents/{id}/review` du service retrieval. Les UUID de documents RAG et de sources éditoriales sont distincts ; ne pas les interchanger.

```powershell
.venv/Scripts/python.exe -m scripts.prepare_science_sources --output artifacts/science-sources
.venv/Scripts/python.exe -m scripts.export_science_integrations --output artifacts/science-exports
```

Le premier outil a téléchargé et extrait le PDF officiel. Il conserve seulement les rectangles de la colonne CM pour les chapitres concernés. Son empreinte est `a6b2a8a97a1027c6debe8df87c168b1d1b0bcff2d44f4cc16b799ee01bc33218`. Toute modification du document bloque ce profil jusqu’à nouvelle vérification. Les Markdown et leur manifeste restent des **brouillons à relire**. PDF/HTML/Markdown sont acceptés par l’extracteur ; les imports réseau restent limités aux domaines institutionnels autorisés.

`artifacts/science-exports/ingestion-requests.json` contient les quatre requêtes réutilisables dans l’API authentifiée. Après ingestion et revue, la recherche sémantique utilise seulement les documents approuvés, dans leur période de validité et le bon niveau/matière. Les embeddings nécessitent le modèle et PostgreSQL en fonctionnement.

Pour préparer les leçons et exercices liés au catalogue de l’école :

```powershell
.venv/Scripts/python.exe -m scripts.export_cm2_training --subject sciences --catalogue artifacts/catalogue-cm2.json --source-id UUID_SOURCE_EDITORIALE --published artifacts/exercices-publies.json --output artifacts/sciences-cours.json
```

Remplacer `UUID_SOURCE_EDITORIALE` par une source enregistrée. Le fichier `exercices-publies.json` associe chaque code à trois UUID de versions publiées, dans l’ordre mini-question, exercice guidé, exercice autonome. Sans ce fichier, seuls les brouillons d’exercices sont exportés. Rien n’est publié automatiquement.

Pour un brouillon reformulé par un modèle Ollama installé localement :

```powershell
.venv/Scripts/python.exe -m scripts.generate_science_draft --context artifacts/contexte-sciences-approuve.json --model NOM_DU_MODELE_INSTALLE --output artifacts/sciences-brouillon-ia.json
```

Le contexte contient exactement `chapter`, `competency`, `source_ids`, `exercise_ids`, `passages`. Chaque passage contient `source_id`, `body`, `status: approved`, `level: CM2`, `subject: sciences`. Ce fichier est un export éditorial fiable, jamais une déclaration fournie par l’élève. Le modèle peut reformuler deux paragraphes ; protocoles, calculs, objectifs, exercices et références sont protégés. Les validations automatiques contrôlent structure et périmètre, **pas la vérité sémantique de toute phrase nouvelle**. Une revue humaine indépendante demeure requise. L’appel Ollama réel n’a pas été exécuté dans cette recette.

Les fichiers `classquiz-*.json` sont des **payloads QuizInput pour l’API d’éditeur**, pas des archives `.classquiz`. Avec le serveur amont : ouvrir une session d’édition (`editor/start?edit=false`), puis envoyer le payload à `editor/finish?edit_id=...` avec le jeton d’édition obtenu. Vérifier le préfixe API de l’instance. Aucun envoi à une instance externe n’a été effectué.

## Installation complète et vérification

Depuis la racine, avec Python 3.11+, Node installé et Docker Desktop en mode conteneurs Linux :

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.lock -r requirements-test.lock
.venv/Scripts/python.exe scripts/init_secrets.py
.venv/Scripts/python.exe scripts/init_security_secrets.py
npm --prefix apps/web ci
docker compose -f docker-compose.dev.yml config --quiet
docker compose -f docker-compose.dev.yml up -d --build
docker compose -f docker-compose.dev.yml ps -a
```

La migration Alembic du Compose inclut désormais `0015_cm2_science_labs`. Suivre également le README racine pour l’initialisation du compte administrateur, les autorisations de sources et la configuration Ollama. Les secrets existants ne doivent pas être remplacés.

```powershell
.venv/Scripts/python.exe -m pytest -q
npm --prefix apps/web run typecheck
npm --prefix apps/web test
npm --prefix apps/web run test:cm2
```

Les tests navigateur lancent leurs propres serveurs : arrêter l’aperçu local avant cette commande, puis le relancer avec le script dédié. La validation Compose, les tests sans base et les parcours navigateur ont été exécutés. Le daemon Docker est arrêté ici : migration réelle, RLS PostgreSQL, purge planifiée et échanges avec le modèle ne sont pas déclarés validés en environnement complet.

Résultats du 11 septembre 2026 : 279 tests Python réussis, 83 tests d’intégration ignorés faute d’environnement Compose ; 6 tests frontend réussis ; 11 parcours Playwright réussis, dont les trois nouveaux parcours sciences. Contrôles Axe et débordement horizontal réussis à 1440 px et 390 px. Le démarrage ponctuel de Docker ayant relancé des services d’autres projets, Docker a été arrêté de nouveau ; aucun conteneur de la stack éducative n’a été lancé.

## Revue avant usage en classe

Faire relire le contenu scientifique, les justifications libres, les exemples et le découpage de source par un enseignant. Vérifier les licences PhET avant toute redistribution/hébergement des simulations ; ici seul un lien est proposé. Conserver les notices MPL/MIT des fichiers intégrés. Les expériences sont entièrement virtuelles : aucun protocole domestique avec flamme, secteur, produit dangereux ou ingestion n’est proposé.

## Mise à jour — déploiement VPS du 11 septembre 2026

La version comprenant les sciences et l’histoire a depuis été déployée sur `192.168.1.10:/stockage/training`. Les 385 tests complets, dont PostgreSQL et les contrôles d’accès, passent sur une base isolée du VPS. La migration active est `0016_cm2_history_workshops`. Le Docker local Windows reste distinct ; il n’a pas été relancé. Voir `docs/DEPLOYMENT_CM2_VPS_2026-09-11.md` pour le périmètre réellement activé et les contenus encore à relire.

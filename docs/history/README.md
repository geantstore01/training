# Atelier du temps — Histoire CM2

MVP intégré à Éducapilote : trois thèmes, six chapitres originaux, dix-huit exercices. Le parcours complet de démonstration est **L’école primaire au temps de Jules Ferry**. Il comporte une lecture guidée, les lois de 1881 et 1882, un court extrait authentique de l’article 4 de la loi de 1882, une frise interactive, une fiche de Jules Ferry, une localisation, un QCM, un classement et une justification libre à relire.

## Programme et sources

Pour le CM2 de septembre 2026 à août 2027, l’histoire reste régie par le programme 2020. Éduscol confirme que le programme publié le 28 mai 2026 ne s’applique au CM2 qu’en 2027–2028 : https://eduscol.education.gouv.fr/4791/ressources-d-accompagnement-du-programme-d-histoire-et-geographie-au-cycle-3

La version consolidée actuellement liée par Éduscol est https://eduscol.education.gouv.fr/media/100806/download?attachment= . Le lien 289890 fourni dans la demande contient un encodage d’apostrophe incorrect et n’a pas été retenu comme téléchargement vérifié. Les trois fiches thématiques CM2 liées par Éduscol sont utilisées avec titre, URL, page et section. Les codes CM2-HIST-* sont internes, jamais présentés comme des identifiants officiels.

Le PDF ONACVG fourni et son ancien lien `/document/44404/download` représentent une **carte des programmes scolaires**, pas une frise ni une archive de guerre. Le dossier le décrit explicitement comme un document pédagogique contemporain. Il ne reprend pas les colonnes du lycée comme objectifs CM2. Les données des dépôts de quiz ne constituent jamais des sources historiques.

Les cartes du MVP sont des localisations approximatives sur une grille géographique, sans frontières historiques. Les portraits sont des fiches nominatives, sans image prétendant représenter un visage historique. Les frises affichent un ordre ; leur espacement n’est pas une échelle de durée. Les textes institutionnels reformulés sont signalés comme tels. Le seul court extrait de loi est distinct d’une reformulation.

## Architecture réellement utilisée

```text
shared/history/
  catalogue.py         six cours, sources, événements, personnes, documents, exercices
  schemas.py           modèles Pydantic et contrôles chronologiques
  ingestion.py         découpage DeepTutor et extraction traçable d’entités candidates
  generation.py        brouillon déterministe et reformulation Ollama contrôlée
  integrations.py      exports ClassQuiz, Interactive-Quiz-Maker et quizli
  vendor/              découpeur DeepTutor, licence Apache-2.0
shared/ai/history_*_prompt.py
services/content-service/app/history.py       préparation éditoriale, relecture adulte
services/assessment-service/app/history.py    catalogue de navigation authentifié
services/retrieval-service/app/               ingestion, pgvector, filtres de chapitre
apps/web/src/components/history-*.tsx         bibliothèque, exploration, relecture enseignant
migrations/versions/0016_cm2_history_workshops.py
scripts/{build_history_catalogue,export_history_review,prepare_history_sources}.py
tests/test_history_training.py
```

Le projet possède déjà FastAPI, Next.js, PostgreSQL/pgvector, Redis, une abstraction IA, Ollama, des tâches serveur et Docker Compose. Le module les étend. Il ne démarre pas sept autres applications et ne crée pas une seconde base d’élèves. Le stockage documentaire versionné est conservé dans PostgreSQL ; MinIO/S3 n’est pas nécessaire au MVP et n’est pas annoncé installé.

| Besoin du prompt | Stockage effectif |
| --- | --- |
| Élèves, parents, classe | `students`, liens parent/enfant et inscriptions existants |
| Thèmes, chapitres, compétences | `subjects`, `curriculum_domains`, `competencies` et versions de leçons |
| Événements, personnages, lieux, documents | JSONB `lesson_versions.body.cm2.history`, schéma Pydantic strict et comparaison au catalogue versionné |
| Sources | `content_sources`, `lesson_sources`, `rag_documents` et `rag_passages` |
| Exercices, réponses privées, indices | tables d’exercices existantes, sans solution dans le prompt public |
| Tentatives, erreurs, maîtrise, prochaine révision | tables d’évaluation existantes et protections RLS |
| Relecture | revues humaines indépendantes existantes ; aucune signature fabriquée |

La migration ajoute six compétences et `rag_documents.history_chapter` avec contrôle de niveau/matière. Les documents historiques recherchés par le tuteur sont filtrés **avant** classement lexical et vectoriel par école, approbation, dates de validité, CM2, histoire et chapitre. Les identités et données d’élèves ne sont pas envoyées aux exports tiers.

## API

Les contrats OpenAPI sont générés dans chaque `services/*/openapi.json`.

- `GET assessment/history/catalogue` : titres/thèmes seulement, authentification requise.
- `GET content/history/review-catalogue` : dossiers et corrections réservés aux enseignants, créateurs et administrateurs.
- `POST content/history/drafts/prepare` : chapitre, compétence réelle, sources de l’école et éventuellement trois identifiants d’exercices ; retourne des propositions sans publication.
- `POST retrieval/documents/ingest` : PDF, HTML ou Markdown HTTPS institutionnel ; préciser `subject=histoire`, `level=CM2`, `history_chapter` et les pages.
- `GET retrieval/documents/{id}/history-entities` : propositions d’entités et offsets des passages, réservés au personnel.
- `POST retrieval/search` : recherche interne avec `history_chapter`, documents approuvés uniquement.
- Les API existantes de contenu/exercices assurent création, soumission et relecture indépendante. Les API `assessment/attempts`, `hints`, `correction`, `next`, `students/{id}/mastery` et `errors` assurent entraînement et suivi. Les bilans parent/enseignant restent ceux du projet.

L’extraction reconnaît des années et les noms déjà décrits dans le chapitre. Elle ne prétend pas découvrir automatiquement des relations de causalité dans un document arbitraire. Une cooccurrence de mots n’est pas déclarée fait historique. Les modèles peuvent reformuler deux paragraphes, jamais changer le document, la frise, les sources ou les exercices ; les faits de la reformulation restent à contrôler humainement.

## Commandes

Depuis la racine du projet, avec les dépendances Python installées :

```bash
python -m scripts.build_history_catalogue
python -m scripts.prepare_history_sources
python -m scripts.export_history_review
python -m scripts.generate_contracts
python -m pytest -q tests/test_history_training.py
npm --prefix apps/web run typecheck
npm --prefix apps/web test
npm --prefix apps/web run test:cm2
```

Sur Windows, utiliser `.venv/Scripts/python.exe` à la place de `python`. Playwright CM2 utilise Edge ; il démarre ses propres serveurs locaux, donc arrêter l’aperçu avant ce test. Relancer ensuite `powershell -File scripts/start_cm2_preview.ps1`, puis ouvrir `http://127.0.0.1:19093/tests/cm2-preview/?subject=histoire`. L’aperçu est une démonstration locale avec essais éphémères, jamais le service à exposer en production.

Sur le VPS existant, conserver secrets, configuration, comptes, fichiers runtime et base. Après sauvegarde et tests sur une base isolée :

```bash
cd /stockage/training
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml run --rm --no-deps migrate alembic upgrade head
# Remplacer les seuls services applicatifs du projet ; conserver l’infrastructure existante.
docker compose -f docker-compose.dev.yml up -d --no-deps --wait web content-service exercise-service assessment-service curriculum-service retrieval-service ai-router-service tutor-service notification-service notification-worker
```

Le Compose choisi correspond à celui déjà exploité sur ce VPS. Ne pas supprimer les conteneurs « orphelins » de supervision : ils appartiennent à sa configuration complémentaire. Les tests d’intégration utilisent une base éphémère et ne doivent jamais charger leurs fixtures dans `educapilote`.

## Publication et limites du MVP

Les six nouveaux dossiers restent des propositions à relire. Le déploiement du code et des compétences n’équivaut pas à une approbation des leçons. L’espace enseignant propose **Relire les nouveaux dossiers d’histoire** ; les fichiers complets sont aussi dans `artifacts/history-review`. Les guerres et persécutions nécessitent expressément la validation adulte demandée dans le prompt. Les réponses libres sont proposées à relecture ; elles ne produisent pas une maîtrise automatique ni un diagnostic certain de la pensée de l’enfant.

Les exercices sont progressifs et classés par difficulté. Les erreurs identifiables relèvent de la chronologie, de la date, du vocabulaire ou du document selon l’exercice ; une justification libre ne permet pas au moteur déterministe de déduire toutes les catégories possibles. L’absence de source pertinente provoque le refus pédagogique prévu. Ce MVP ne prétend pas couvrir tous les sous-chapitres de l’année.

Pour une reformulation avec un modèle disponible dans Ollama : `python -m scripts.generate_history_draft --context contexte-valide.json --model NOM_DU_MODELE --output brouillon.json`. Le fichier de contexte opérateur contient exactement `chapter`, `competency`, `source_ids`, `exercise_ids`, `passages` ; les passages doivent provenir du corpus approuvé du même chapitre, avec `status`, `level`, `subject`, `chapter`, `source_id`, `body`. Cette commande ne reçoit pas de messages d’élèves et ne publie rien. La disponibilité du modèle dépend de la configuration du serveur.

L’outil opérateur `scripts/stage_history_content.py` importe réellement les sources téléchargées, leurs vecteurs et les 18 versions d’exercices en brouillon. Il vérifie les empreintes, le manifeste, la compétence et le propriétaire éditorial ; il ne crée aucune approbation. Son mode par défaut est une simulation ; `--apply` applique l’import. Réexécuter l’import saute les snapshots et slugs existants. Les traces opérateur ont un acteur nul, afin de ne pas faire passer l’import automatique pour une action humaine de relecture.

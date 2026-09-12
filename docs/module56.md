# Modules 5 et 6 — Ollama, RAG et Capitaine Savoir

Les trois services utilisent les JWT et sessions révocables du module 2. Le tenant vient du JWT et les nouvelles tables sont protégées par RLS forcée. Les élèves passent par `tutor-service` ; `/plan` et `/search` exigent en plus le secret interservices `X-Edu-Internal`, absent du navigateur.

## Modèles et connexion au VPS

Le routeur appelle le daemon Ollama déjà connecté sur le VPS, via `http://ollama-host:11434/api/chat`. Aucun identifiant du compte Ollama n'est copié dans le dépôt ou dans les conteneurs. Modèle retenu : **gpt-oss:120b-cloud**, disponible et testé sur ce serveur, pour le choix d'une démarche pédagogique. Ce choix n'est pas un classement comparatif de tous les modèles.

Les embeddings restent **locaux** : `educapilote-embeddinggemma:v1`, copie nommée du modèle `embeddinggemma:latest` existant, 768 dimensions, digest `85462619ee721b466c5927d109d4cb765861907d5417b9109caebc4e614679f1`. Ne pas écraser cet alias : créer un autre nom et réingérer le corpus si les poids changent. La recherche exclut les passages encodés avec un autre nom de modèle.

Sur un nouvel hôte Ollama :

```bash
ollama pull embeddinggemma
ollama cp embeddinggemma:latest educapilote-embeddinggemma:v1
ollama signin
ollama pull gpt-oss:120b-cloud
```

Le VPS actuel possède déjà les modèles et la connexion. Le réseau backend reste interne. Seuls retrieval et ai-router ont un nom d'hôte vers le daemon existant. Retrieval rejoint aussi le réseau de sortie pour télécharger les documents officiels. La configuration d'écoute générale d'Ollama, utilisée par les autres projets du VPS, n'est pas modifiée.

Ollama Cloud ne garantit pas les structured outputs : le service demande du JSON puis **valide strictement** le résultat Pydantic, les actions autorisées et l'identifiant de source. Une sortie libre, un champ supplémentaire ou une source inventée sont refusés. Références : [Ollama Cloud](https://docs.ollama.com/cloud), [sorties structurées](https://docs.ollama.com/capabilities/structured-outputs), [modèle cloud](https://ollama.com/library/gpt-oss:120b-cloud), [embeddings](https://docs.ollama.com/api/embed).

## Ingestion et validation documentaire

Les documents RAG ont leur propre registre versionné (`rag_documents`, `rag_passages`, `rag_reviews`). Les anciennes références `content_sources` restent utilisées par les leçons et exercices ; leur simple existence ne les rend pas publiables dans le RAG.

| Endpoint retrieval | Usage |
|---|---|
| `POST /documents/ingest` | Télécharger, extraire, découper et encoder un brouillon |
| `GET /documents/{id}` | Inspecter la provenance et le statut |
| `GET /documents/{id}/passages` | Relire tous les passages extraits avant validation |
| `POST /documents/{id}/submit` | Soumettre son brouillon |
| `POST /documents/{id}/review` | Décision d'un autre enseignant/créateur |
| `POST /documents/{id}/archive` | Retirer un document approuvé de la recherche |
| `POST /search` | Recherche interservices, JWT + secret requis |

Exemple de corps d'import PDF, à adapter après lecture du document :

```json
{
  "url": "https://www.education.gouv.fr/sites/default/files/programme-de-math-matiques-pour-le-cycle-3-439827.pdf",
  "title": "Programme de mathématiques — extrait à relire",
  "level": "CM1",
  "subject": "mathematiques",
  "programme_version": "BO-2025-16-MENE2504620A",
  "effective_from": "2025-09-01",
  "effective_until": null,
  "page_selection": [5, 6]
}
```

`page_selection` utilise les numéros de pages physiques du PDF, à partir de 1 ; liste vide = toutes les pages. Cette sélection permet d'isoler les sections d'un programme couvrant plusieurs niveaux. L'enseignant doit vérifier **le niveau de chaque passage**, la matière, les dates et la qualité d'extraction ; l'importateur ne peut approuver son propre document. Le domaine officiel ne suffit pas à prouver qu'un texte est le programme applicable : un projet de programme, par exemple, ne doit pas être validé comme programme en vigueur.

La relecture exige explicitement :

```json
{"decision":"approved","reason_code":"programme_verified","confirmed_human_review":true}
```

Workflow : `draft → pending_review → approved → archived`. Un rejet revient à `draft`. Le texte, les vecteurs et la provenance sont immuables ; réimporter crée une nouvelle version. Archiver explicitement les versions remplacées. Les validations sont historisées et protégées contre la modification.

Téléchargements : HTTPS sur `education.gouv.fr`, `www.education.gouv.fr`, `eduscol.education.gouv.fr`, certificat vérifié, IP publique épinglée, aucun suivi de redirection. PDF/HTML/texte UTF-8 seulement, 2 Mo maximum, 100 pages PDF maximum, sélection de 30 pages maximum, texte extrait de 100 000 caractères maximum. Un document scanné sans texte est refusé : aucun OCR simulé. L'extraction PDF tourne dans un processus limité en CPU/mémoire et en durée. Les passages sont bornés à 1 800 caractères, avec découpage aux phrases et paragraphes, puis calcul réel des embeddings par lots.

Les nouveaux programmes de français/mathématiques s'appliquent au CM1 depuis 2025 et au CM2 depuis la rentrée 2026 ; les dates sont conservées par document. Vérification à partir du [Bulletin officiel](https://www.education.gouv.fr/bo/2025/Hebdo16/MENE2504620A). Pour l'histoire, vérifier séparément le niveau et l'année dans les [ressources Éduscol](https://eduscol.education.gouv.fr/4791/ressources-d-accompagnement-du-programme-d-histoire-et-geographie-au-cycle-3).

## Recherche hybride

`/search` reçoit `query`, `level` (`CM1`/`CM2`), `subject` (`francais`/`mathematiques`/`histoire`) et `limit` (1–8). Le niveau et la matière sont dérivés de la tentative par le tuteur.

Les filtres tenant, niveau, matière, statut `approved`, dates d'application et modèle d'embeddings précèdent les classements. PostgreSQL fournit `plainto_tsquery('french',...)` et `ts_rank_cd` ; pgvector fournit la distance cosinus. Les 32 premiers candidats de chaque branche sont fusionnés par Reciprocal Rank Fusion, constante 60. La branche vectorielle exclut les distances > 0,65, seuil technique à évaluer sur un corpus pédagogique relu.

Les index GIN et HNSW sont créés. La requête actuelle calcule **exactement sur le sous-corpus filtré matérialisé**, pour éviter les pertes de résultats dues au post-filtrage ANN. Elle ne prétend donc pas exploiter HNSW pour ce chemin d'exécution. C'est adapté à un corpus scolaire limité ; mesurer et partitionner avant un corpus massif. Aucune réponse hors filtres, même si le nombre de résultats devient nul.

## Tuteur et protection des réponses

`POST /turns` reçoit uniquement :

```json
{"attempt_id":"UUID_DE_TENTATIVE_ACTIVE","request_id":"UUID_UNIQUE","message":"Je ne sais pas comment commencer.","plus_aide":false}
```

L'élève doit posséder la tentative et une session active ; l'exercice doit référencer des compétences compatibles avec son niveau. Aucun champ de modèle, prompt système ou niveau libre n'est accepté.

| Niveau | Démarche maximale |
|---|---|
| 0 | Reformuler la consigne |
| 1 | Identifier informations et objectif |
| 2 | Représenter par dessin, liste ou tableau |
| 3 | Relier à une méthode étudiée |
| 4 | Décomposer en petites étapes |
| 5 | Vérifier sa démarche |
| 6 | Amorcer une méthode partielle, sans calculer ni compléter la réponse |

La première interaction reste au niveau 0, même avec `plus_aide=true`. Chaque demande suivante peut augmenter d'un seul niveau. Le modèle peut choisir une action moins avancée. Les phrases sont construites par le serveur à partir d'un catalogue contrôlé : le LLM choisit une action et une source, **il ne rédige pas librement les explications affichées**. Ce périmètre privilégie l'accompagnement de la démarche ; ce n'est pas un professeur conversationnel générant toute explication disciplinaire.

Les sept champs demandés sont toujours présents : `message_pedagogique`, `type`, `niveau_aide`, `question_suivante`, `erreur_detectee`, `action_recommandee`, `safety_status`. `erreur_detectee` est une hypothèse de démarche, pas une correction. Les diagnostics chiffrés et les corrigés privés ne sont pas transmis. Le rôle SQL tutor ne peut pas lire `answer_spec` ni les réponses chiffrées de l'élève.

« Donne-moi la réponse » produit un refus socratique sans appel cloud. Les messages dangereux déclenchent la protection locale. Sans source validée ou avec une réponse fournisseur invalide, le tuteur renvoie explicitement `indisponible`/`fallback` sans inventer une explication. L'historique est accessible via `GET /attempts/{id}/history` pour la tentative active de l'élève.

Une demande répétée avec le même `request_id` et le même contenu rejoue la réponse enregistrée ; un changement de contenu produit 409. Deux aides concurrentes sont arbitrées au moment de l'enregistrement. Le même verrou que celui de l'évaluation protège la mise à jour de `max_hint_level` : une aide ne peut être enregistrée après soumission. Les appels externes se font hors transaction SQL ; une course peut consommer deux appels cloud, mais ne crée pas deux aides pour la même clé.

## Consentements, erreurs et exploitation

Avant une interaction, safety applique le consentement `ai_local` et l'assentiment. Avant chaque contenu envoyé au cloud, le routeur applique aussi `ai_cloud`, masque les PII et analyse les extraits. Il n'existe pas de champ client `already_sanitized` ni de chemin de chat générique. Le tuteur ne transmet jamais de corrigé.

Les erreurs fournisseur (authentification, modèle absent, quota, délai, JSON invalide, réponse trop grande) ne renvoient aucun corps fournisseur. Trois échecs ouvrent un circuit local au processus pendant 30 secondes. Les appels sont limités par utilisateur et à **200 appels par école/jour UTC** par défaut, quota Redis prélevé avant l'appel, sans nouvelle tentative automatique. C'est une limite de nombre d'appels, pas une garantie de coût en euros. `cost_eur=NULL` signifie coût non fourni ; aucun tarif fictif n'est enregistré.

Traces : codes, modèle, latence, compteurs de tokens et sources choisies, sans messages bruts. `tutor_turns` et `ai_interactions` expirent après 7 jours. Les tours expirés sont exclus de l'historique et nettoyés à l'usage ; exécuter régulièrement `scripts/purge_expired.py` avec le compte de maintenance pour purger les tenants inactifs aussi.

```bash
python3 scripts/init_security_secrets.py
docker compose -f docker-compose.dev.yml up -d postgres redis
python3 scripts/configure_ollama_host.py
docker compose -f docker-compose.dev.yml up -d --build
bash scripts/test_module56.sh
bash scripts/verify_migrations.sh
python3 scripts/smoke.py
docker compose -f docker-compose.dev.yml exec -T ai-router-service python -m scripts.smoke_ollama
docker compose -f docker-compose.dev.yml exec -T retrieval-service python -m scripts.smoke_document
```

Les tests Pytest d'intégration utilisent une base jetable, PostgreSQL/Redis et les vrais endpoints internes. Le téléchargement et Ollama y sont remplacés explicitement par des doubles déterministes. Les deux derniers scripts effectuent séparément de vrais appels externes, sans données d'enfants et sans publier de corpus.

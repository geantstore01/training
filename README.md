# ÉDUCAPILOTE — modules 1 à 10

Le [module Sciences CM2](docs/science/README.md) ajoute une station interactive, quatre chapitres, douze exercices, un carnet scientifique chiffré et des intégrations ClassQuiz/PhET. Son dossier précise les dépôts réellement réutilisés, le référentiel 2023 applicable, les commandes et les limites de validation.

Le [parcours mathématiques CM2](docs/cm2-training.md) ajoute 22 micro-leçons,
66 questions, des indices progressifs, une correction après tentative et une sélection
d'exercices adaptée aux résultats. Le guide distingue la recette locale, les tests
effectués et les étapes nécessaires avant publication dans une école.

Socle CM1–CM2 : 15 processus FastAPI indépendants, PostgreSQL 17 + pgvector,
Redis, Nginx, schéma central SQLAlchemy 2.0 et migration Alembic transactionnelle.
Les 15 services disposent désormais de leurs API métier, contrats OpenAPI et tests.
Un worker de notifications et quatre workflows n8n complètent les services.

Voir le [guide du module 2](docs/module2.md) pour les endpoints, les rôles,
les consentements, le filtrage et la création du premier administrateur.

Le [guide du module 3](docs/module3.md) décrit le graphe de compétences, les
versions et la validation humaine des contenus.

Le [guide du module 4](docs/module4.md) décrit les exercices, leur correction et
le suivi de maîtrise sans notes publiques.

Le [guide des modules 5 et 6](docs/module56.md) décrit Ollama Cloud, le RAG
validé et le tuteur socratique.

Le [guide des modules 7 et 8](docs/module78.md) décrit les classes, tableaux de bord,
la modération, la lecture vocale et les automatisations.

Le [guide des modules 9 et 10](docs/module910.md) décrit les espaces web élève, parent et enseignant.

## Arborescence

```text
apps/web/               # Next.js, TypeScript strict, Tailwind, shadcn/ui
services/
  auth-service/          user-service/          class-service/
  curriculum-service/    content-service/       exercise-service/
  assessment-service/    tutor-service/         retrieval-service/
  speech-service/        notification-service/  analytics-service/
  admin-service/         safety-service/        ai-router-service/
  # Chaque dossier contient app/main.py, app/__init__.py, openapi.json, README.md
shared/
  app.py                 # sondes live/ready effectives
  config.py              # secrets par fichiers, configuration Pydantic
  dto.py                 # DTOs publics stricts
  security/              # JWT, sessions, autorisations, chiffrement
  pedagogy.py             # six niveaux de maîtrise
  db/models.py           # 53 modèles SQLAlchemy, types PostgreSQL natifs
  db/session.py          # contexte tenant limité à la transaction
migrations/
  env.py
  versions/0001_initial.py
  versions/0002_access_safety.py
  versions/0003_curriculum_content.py
  versions/0004_exercise_assessment.py
  versions/0005_ai_rag_tutor.py
  sql/0001_schema.sql    # DDL figé, indépendant des modèles futurs
  sql/0001_security.sql  # RLS, triggers, droits et niveaux CM1/CM2
  sql/0001_down.sql
infra/
  Dockerfile
  postgres/init.sh
  redis/{redis.conf,start.sh}
  nginx/{nginx.dev.conf,nginx.prod.conf}
scripts/                 # secrets, contrats, export SQL, sauvegarde, purge
tests/                   # unitaires et intégration PostgreSQL réel
docs/                    # schéma, exploitation, sécurité et validation
docker-compose.dev.yml
docker-compose.prod.yml  # configuration autonome Traefik + observabilité
requirements.lock
requirements-test.lock
infra/images.lock.json    # empreintes des images de base vérifiées
pyproject.toml
alembic.ini
.env.example
```

## Démarrage sur le VPS

```bash
cd /stockage/training
python3 scripts/init_secrets.py
python3 scripts/init_security_secrets.py
docker compose -f docker-compose.dev.yml config --quiet
docker compose -f docker-compose.dev.yml up -d --build
docker compose -f docker-compose.dev.yml ps -a
curl --fail http://127.0.0.1:18088/services/auth-service/health/ready
python3 scripts/smoke.py
```

La génération de secrets est idempotente et n'affiche aucune valeur. PostgreSQL
et Redis n'ont **aucun port hôte**. Les volumes portent le préfixe `educapilote_`.
Le réseau backend est interne. Le routeur utilise le daemon Ollama du VPS ;
retrieval dispose aussi d’une sortie pour les téléchargements officiels.
Le proxy de développement écoute sur `127.0.0.1:18088` par défaut.

Depuis un poste distant, ouvrir un tunnel SSH :

```bash
ssh -L 18088:127.0.0.1:18088 root@192.168.1.10
```

Puis ouvrir `http://localhost:18088/services/auth-service/docs`.
Le mot de passe SSH n'est enregistré dans aucun fichier du dépôt.

## Tests et contrats

```bash
# Suite complète dans une base PostgreSQL jetable et avec Redis réel.
bash scripts/test_module56.sh

# Développement local
python -m venv .venv
# Activer .venv selon le système
python -m pip install -r requirements.lock -r requirements-test.lock -r requirements-safety.lock
python -m pytest -q
python -m scripts.generate_contracts
```

Sans `EDU_TEST_INTEGRATION=1`, les tests PostgreSQL sont explicitement ignorés.
Les tests IA utilisent des doubles réseau explicitement signalés ; les scripts
smoke_ollama.py et smoke_document.py vérifient séparément les appels réels.
Chaque service possède son contrat `services/<nom>/openapi.json` ; le contrat
actif est aussi disponible sous `/services/<nom>/openapi.json`.

## Production

Le module 11 fournit un Compose **autonome**, Traefik avec ACME TLS-ALPN-01,
Prometheus/Grafana/Loki/Alloy, la télémétrie filtrée et les sauvegardes chiffrées.
Voir [déploiement](docs/deploiement-production.md) et [checklists](docs/checklists-production.md).
Ne pas superposer les fichiers dev et prod : ils utilisent les mêmes volumes du projet.
L'observabilité seule peut être ajoutée au déploiement privé avec
`docker-compose.dev.yml` + `docker-compose.observability.yml`.

```bash
# Après configuration du domaine, du routage 443 et des secrets de sauvegarde :
bash scripts/deploy_production.sh
```

Le DNS, le certificat public, les décisions RGPD et la recette humaine restent des
conditions d'ouverture. Les secrets Compose sont des fichiers hôte protégés,
pas un coffre chiffré.

Les conteneurs applicatifs tournent en UID 10001, avec système de fichiers en
lecture seule, capacités supprimées, limites mémoire/CPU et journaux bornés.
Le compte de migration est séparé des 15 comptes de service. Nginx ne monte
pas le socket Docker. Les applications démarrent après succès d'Alembic.
Les images de base sont figées par digest ; les dépendances Python et leurs
dépendances transitives sont figées dans les fichiers requirements*.lock.

Références techniques consultées :
[PostgreSQL RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html),
[SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/orm/declarative_mixins.html),
[pgvector](https://github.com/pgvector/pgvector).

Parcours pédagogiques : [mathématiques CM2](docs/cm2-training.md) et
[français CM2, provenance des cinq dépôts et limites de la recette](docs/cm2-french-training.md).

# Validation du module 1 — 10 septembre 2026

Environnement testé : VPS `192.168.1.10`, dépôt `/stockage/training`.
Copie de travail locale : `D:\codex\training`.

## Résultats

| Vérification | Résultat |
|---|---|
| Pytest sur PostgreSQL réel | **28 tests réussis**, aucun ignoré |
| Modèles SQLAlchemy ↔ schéma migré | Aucun écart Alembic détecté |
| Révision initiale | `0001_initial`, 38 tables métier + alembic_version |
| Migration sur base jetable | upgrade → check → downgrade → upgrade → check réussi |
| Isolation tenant | RLS forcée, absence de contexte, FK composites et tentative inter-tenant vérifiées |
| Permissions | Login SQL applicatif réel, refus DDL/TRUNCATE, audits immuables et réponses cachées au tutor vérifiés |
| Contenus | Revue indépendante, refus d'auto-approbation, rejet d'une ancienne approbation et immutabilité vérifiés |
| Données pédagogiques | Cohérence session/élève, refus d'exercice brouillon, plages probabilistes et graphe sans cycles vérifiés |
| Consentement | Autorité parentale vérifiée, preuve immutable et retrait irréversible vérifiés |
| RAG | Distance vectorielle et recherche française exécutées avec succès |
| Proxy | 15 sondes ready réussies et 15 contrats OpenAPI identiques aux fichiers livrés |
| TLS | Configuration Nginx et handshake HTTPS validés avec certificat localhost éphémère |
| Sauvegarde/restauration | Dump gzip restauré dans une base séparée ; propriétaires, 39 tables et seeds contrôlés |
| Données résiduelles | 0 tenant ; bases temporaires de migration/restauration supprimées |

La suite affiche deux avertissements de dépréciation provenant des dépendances
Starlette/httpx/AnyIO de test ; aucun échec. Les doubles de panne sont limités aux
tests unitaires. Les tests d'intégration utilisent PostgreSQL 17 et pgvector réels.

## Versions effectivement exécutées

- Python 3.11.16
- PostgreSQL 17.11
- pgvector 0.8.6
- Redis 7.4.11
- Nginx 1.30.4
- Docker Engine 28.5.1, Docker Compose 2.40.3

Les empreintes des images sont dans `infra/images.lock.json`. Les versions des
librairies Python sont dans `requirements.lock` et `requirements-test.lock`.

## Commandes de reproduction

```bash
cd /stockage/training
docker compose -f docker-compose.dev.yml --profile test run --build --rm test
bash scripts/verify_migrations.sh
bash scripts/verify_restore.sh
sudo bash scripts/verify_tls.sh
python3 scripts/smoke.py
```

L'installation active est celle de développement, liée à `127.0.0.1:18088`.
Le test TLS n'a pas exposé le proxy publiquement ni installé un certificat de
production. L'ouverture publique nécessite le certificat réel et l'overlay
documenté. Ce rapport valide le module infrastructure ; il ne valide pas les
fonctionnalités métier ou une conformité RGPD complète.

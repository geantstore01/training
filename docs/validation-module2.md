# Validation du module 2 — 10 septembre 2026

Environnement : VPS 192.168.1.10, dépôt /stockage/training, Docker Compose.

- `bash scripts/test_module2.sh` : **93 passed**, aucun test ignoré, 50,96 s.
  Deux avertissements de dépréciation Starlette/httpx/AnyIO, aucune erreur.
  Base PostgreSQL jetable, comptes SQL applicatifs réels, Redis ACL réel,
  modèle français spaCy local. Les pannes injectées sont explicitement des tests.
- Alembic : migration vers `0002_access_safety`, aucune dérive des modèles.
  Rétrogradation puis réapplication validées dans une base isolée.
- Sauvegarde et restauration validées dans une base isolée :
  `backups/educapilote-20260910T142447Z-2347983.sql.gz` ; 39 tables métier
  et la table Alembic, propriétaires et révision contrôlés.
- Déploiement auth/user/safety/migrate et redémarrage du proxy terminés avec code 0.
- Les 15 services répondent prêts ; leurs contrats OpenAPI correspondent aux fichiers.
- Via Nginx : auth/me et user/me renvoient 401 sans session ; safety/analyze
  refuse également une requête anonyme. JWKS et politique de consentement : 200.
- Base active : révision 0002, zéro utilisateur et zéro tenant. Les fixtures ne
  sont pas introduites dans la base active. Aucun administrateur par défaut.

Les tests couvrent notamment rotation concurrente, rejeu et révocation des sessions,
isolation entre écoles, RBAC, relations parent/élève et affectations enseignant,
chiffrement contextualisé, historique immuable, retraits parent et élève, droits
Redis, filtrage PII et menaces, ainsi que le refus de traitement en cas de panne.
Ils ne démontrent pas une détection exhaustive des menaces ni une conformité RGPD
à eux seuls. Le périmètre et les limites sont détaillés dans [module2.md](module2.md).

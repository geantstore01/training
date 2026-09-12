# Validation du module 3 — 10 septembre 2026

Environnement : VPS 192.168.1.10, dépôt /stockage/training, Docker Compose.

- Suite complète : **123 tests réussis**, aucun test ignoré, 128,15 secondes.
  Deux avertissements de dépréciation Starlette/httpx/AnyIO, sans erreur.
  PostgreSQL et Redis réels, comptes SQL de chaque service, ACL réelles ;
  fixtures confinées à une base jetable.
- Exécution locale : 74 réussis, 49 intégrations explicitement ignorées sans le VPS.
- Graphe : parcours amont/aval, frontière de profondeur, états de maîtrise,
  accès individuel, filtres par programme/niveau/date, cycles et écritures concurrentes.
- Contenus : trois types, brouillons invisibles aux élèves, revue indépendante,
  rejet, nouveau tour, versioning, remplacement atomique, archives, décisions
  concurrentes, ancienne version en attente, isolement entre écoles et droits Redis.
- Les tests des modules précédents restent réussis. Les fixtures accentuées ont
  été remises en UTF-8 après détection d’une lecture avec l’encodage Windows.
- Alembic : upgrade 0003, aucune dérive SQLAlchemy ; downgrade complet et nouvelle
  application vérifiés dans une base isolée. Les migrations 0001 et 0002 conservent
  leur contenu antérieur (comparaison avec l’archive du module 2).
- Déploiement curriculum/content/migrate et redémarrage du proxy : code de sortie 0.
- Les quinze services répondent prêts et leurs OpenAPI correspondent aux fichiers.
- Via Nginx, les catalogues de compétences et contenus renvoient 401 sans JWT ;
  les contrats des deux services indiquent la version 0.3.0.
- Sauvegarde restaurée et contrôlée :
  `backups/educapilote-20260910T144416Z-2458937.sql.gz`, 40 tables métier et Alembic.
- Base active : révision `0003_curriculum_content`, zéro utilisateur, zéro leçon,
  matières `francais`, `mathematiques`, `histoire` initialisées.

Le code et les tests ne constituent pas un catalogue national exhaustif prévalidé.
Les compétences doivent être référencées et validées par les responsables du
référentiel, et chaque contenu doit suivre son workflow humain avant publication.
Voir [module3.md](module3.md) pour le contrat, les droits et les limites.

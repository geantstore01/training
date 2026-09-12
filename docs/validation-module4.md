# Validation du module 4 — 10 septembre 2026

Environnement : VPS 192.168.1.10, dépôt /stockage/training, Docker Compose.

- Suite complète : **176 tests réussis**, aucun test ignoré, 184,08 secondes.
  Deux avertissements de dépréciation Starlette/httpx/AnyIO, sans erreur.
- Exécution locale : 116 réussis, 60 intégrations explicitement ignorées sans le VPS.
- Les 53 nouveaux tests couvrent les correcteurs et les paramètres BKT/SRS,
  les six typologies, les dix contrôles, l’exposition des DTOs, la validation
  humaine, les sessions, les aides, le chiffrement et les tentatives idempotentes.
- PostgreSQL réel avec les rôles applicatifs, Redis réel avec ACL, fixtures en
  bases jetables. Les tests des trois modules antérieurs restent réussis.
- Concurrence : une même soumission est comptabilisée une fois ; deux exercices
  distincts corrigés simultanément préservent leurs deux preuves de maîtrise.
- Les essais rapprochés et aidés ne gonflent pas la maîtrise ; les formulations
  non reconnues n’entraînent pas de mise à jour probabiliste.
- L’historique conserve le résultat qualitatif, le prompt figé et les réponses
  autorisées. Les clés de correction, scores et probabilités restent privés.
- Alembic : migration 0004 conforme aux modèles ; downgrade complet et nouvelle
  application vérifiés en base isolée. Les migrations 0001 à 0003 conservent leur
  contenu antérieur, comparé à l’archive du module 3.

Les tests ne valident pas statistiquement le modèle de maîtrise sur une population
CM1–CM2. Les paramètres sont des valeurs de départ documentées, à calibrer avant
une interprétation pédagogique forte. La correction française applique une grille
explicite, pas une compréhension générale du langage. Voir [module4.md](module4.md).

## Déploiement vérifié

- Exercise, assessment et migrate construits ; déploiement terminé avec code 0.
- Les quinze services répondent prêts et leurs OpenAPI correspondent aux fichiers.
- Via Nginx, le catalogue d’exercices et la création de session refusent les
  requêtes anonymes en 401 ; les deux contrats indiquent la version 0.4.0.
- Sauvegarde restaurée et contrôlée :
  `backups/educapilote-20260910T150949Z-2612970.sql.gz` ; 41 tables métier et Alembic.
- Base active : révision `0004_exercise_assessment`, zéro utilisateur, zéro exercice
  et zéro tentative. Aucune fixture n’a été publiée dans la base active.

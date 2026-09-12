# Recette des modules 7 et 8

Vérifications effectuées le 10 septembre 2026 sur le VPS `192.168.1.10`, dépôt `/stockage/training`.

- Suite complète VPS : **243 réussis** en 407,80 secondes. La suite complémentaire inclut deux nouveaux scénarios, soit **245 tests distincts validés** au total.
- Tests locaux : **168 réussis**, 77 tests d'intégration réservés à PostgreSQL/Redis ignorés localement.
- Suite métier complémentaire sur PostgreSQL/Redis réels : **13 réussis**. Classes, groupes, missions, autorisations parent/enseignant, drapeaux, rapports idempotents, génération par lot, compte révoqué, consentement vocal, authentification des automatisations, alertes et purge.
- Migration Alembic : montée complète, absence de dérive, retour à zéro, réapplication et nouvelle comparaison réussis dans une base éphémère.
- Synthèse eSpeak NG réelle : WAV mono, **119 074 octets, 59 515 trames, 22 050 Hz**, produit en mémoire. Le test unitaire de l'endpoint utilise un double explicitement nommé ; le contrôle du moteur utilise le vrai binaire.
- n8n 2.38.6 : **quatre workflows importés**, service démarré, `/healthz` répond `ok`. Workflows inactifs, sans credentials utilisateur ; leur déclenchement de bout en bout n'a pas été exécuté sans compte d'établissement.
- Les **15 services** répondent à leur sonde PostgreSQL/Redis à travers Nginx et leurs contrats OpenAPI correspondent exactement aux fichiers du dépôt.
- Base active : `0006_school_operations`, **52 tables métier + alembic_version**, aucun utilisateur de test ajouté.
- Sauvegarde et restauration isolée validées : `backups/educapilote-20260910T181319Z-3592454.sql.gz`, avec contrôle des 53 tables et de leur propriétaire.
- Worker démarré sans redémarrage au contrôle ; traitement réel des jobs couvert dans la base de test isolée.

Les deux avertissements Pytest concernent des dépréciations Starlette/httpx/AnyIO. Aucun courriel SMTP ni transcription STT n'est revendiqué. Les rapports sont disponibles dans la boîte interne ; la procédure de configuration n8n figure dans `module78.md`.

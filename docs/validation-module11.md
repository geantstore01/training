# Rapport de validation — module 11

Vérifications réalisées le 10 septembre 2026 sur `/stockage/training`, VPS
192.168.1.10. Aucune fixture de compte élève n'a été ajoutée à la base active.

## Contrôles effectivement exécutés

| Contrôle | Résultat |
|---|---|
| Compose autonome production + overlay observabilité | Syntaxe validée par Docker Compose ; domaine fictif utilisé uniquement pour le rendu, sans demande ACME |
| 15 services après reconstruction/déploiement | Readiness PostgreSQL/Redis positive et 15 contrats OpenAPI identiques aux fichiers livrés |
| Frontend après déploiement | Connexion, redirection protégée, session opaque, rejet CSRF, blocage route interne et nonce CSP validés |
| Tests observabilité finaux | **11 réussis** localement et dans l'image de test Linux |
| Régression complète finale | **259 tests réussis**, aucun ignoré, 353,13 secondes ; 4 avertissements de dépréciation de bibliothèques de test |
| Prometheus | 15 cibles API et toutes les cibles d'infrastructure accessibles ; dépendances PostgreSQL/Redis disponibles |
| Alertes | 9 règles valides ; tests promtool de déclenchement service/dépendance en panne et absence d'alerte service sain réussis |
| Grafana | Dashboard provisionné et API authentifiée accessibles sur loopback |
| Loki/Alloy | Ingestion d'un véritable événement HTTP technique vérifiée via l'API Grafana/Loki ; champs limités à la liste autorisée |
| Confidentialité technique | Tests d'absence d'identité, corps, cookie, token et chemin brut dans métriques/logs/Sentry ; transport SDK Sentry en mémoire testé |
| Rétention locale | Test de suppression des fichiers techniques expirés et préservation des fichiers récents/non concernés |
| Résilience du logging | Une erreur d'écriture des logs ne casse pas la réponse applicative |
| GPU | RTX 4070 12 282 MiB accessible depuis le conteneur Ollama ; runtime sain, sans téléchargement de modèle supplémentaire |
| Sauvegarde chiffrée | Dump compressé/chiffré age créé, checksum SHA-256 et métrique de succès générés |
| Restauration | Backup `educapilote-20260910T195330Z-4133716.sql.gz.age` déchiffré et restauré : 54 tables/propriétaires et révision `0007_student_controls` validés |
| Nettoyage de recette | Base isolée `edu_restore_20260910195354_4136206` supprimée après validation ; base active inchangée |
| Maintenance systemd | Les deux timers sont actifs ; exécutions backup/host-metrics terminées avec `Result=success`, code 0 |
| TLS Traefik | Handshake TLS et routage réel vers Next.js validés avec certificat local explicitement réservé au test ; route métriques absente côté public |

Les tests Sentry n'ont transmis aucun événement à un tiers. Le test d'alertes utilise
des séries synthétiques promtool et n'a pas interrompu PostgreSQL/Redis en production.
Le test TLS n'a ni contacté Let's Encrypt ni configuré un faux domaine public.

La première exécution globale a atteint la limite mémoire de 1,5 Go du conteneur
de test et a été interrompue par le noyau. La limite de ce conteneur a été portée
à 4 Go, car il charge plusieurs applications/modèles dans un seul processus.
Les limites mémoire des services de production n'ont pas été augmentées.
La relance complète a terminé avec les 259 tests réussis ; la migration de la base
isolée et `alembic check` ont également réussi, sans changement de schéma requis.

## État déployé

Les 15 services, web et worker fonctionnent avec la télémétrie backend ; Prometheus,
Grafana, Loki, Alloy, Node Exporter et le relais Sentry tournent. Le profil Ollama
local a été démarré et contrôlé, mais le routeur conserve l'Ollama hôte connecté au
compte Cloud existant. Les modèles/authentifications de l'hôte n'ont pas été modifiés.

L'accès applicatif reste privé sur 127.0.0.1:18088. Prometheus et Grafana sont
publiés uniquement sur 127.0.0.1:19090 et 127.0.0.1:13000. Le Nginx hôte sur 80
n'a pas été modifié. Aucun Traefik public n'est démarré sans domaine.

## Points non validés / conditions d'ouverture

- Domaine, DNS/NAT public et e-mail ACME non fournis : aucun certificat public émis,
  aucun test de renouvellement réel et aucune recette du cookie Secure en production.
- DSN Sentry non fourni : relais désactivé pour les envois ; projet/région/contrat
  et livraison externe restent à vérifier.
- Clé de déchiffrement conservée localement pour la recette : export dans un coffre
  hors VPS et copie de sauvegarde hors site non réalisés.
- Aucun destinataire d'astreinte n'est configuré ; alertes visibles dans Prometheus.
- Pas de certification RGPD/OWASP/WCAG, de pentest indépendant, de scan CVE complet,
  de test de charge représentatif ou de recette humaine avec mineurs.
- L'AIPD, les décisions du responsable de traitement, les contrats Cloud et les
  procédures complètes d'exercice des droits restent à valider dans la checklist.

## Reproductibilité

Principaux scripts : `scripts/verify_observability.py`, `scripts/verify_traefik.sh`,
`scripts/smoke.py`, `scripts/smoke_web.py`, `scripts/restore_postgres.sh` et
`tests/test_observability.py`. Les scénarios d'alertes sont dans
`infra/monitoring/alerts.test.yml`.

Logs d'exécution sur le VPS : `/tmp/edu11-build-tests.log`,
`/tmp/edu11-targeted-tests.log`, `/tmp/edu11-regression.log` et `/tmp/edu11-final-build.log`.

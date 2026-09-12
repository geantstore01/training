# ÉDUCAPILOTE — déploiement et exploitation

## Périmètre

`docker-compose.prod.yml` est **autonome** et généré par `scripts/generate_production.py`.
Il contient les 15 microservices, Next.js, le worker, PostgreSQL/pgvector, Redis,
Traefik, Prometheus, Grafana, Loki, Alloy, Node Exporter et le relais Sentry.
Le profil `local-ollama` ajoute un serveur Ollama GPU. Les images tierces sont
verrouillées par digest dans `infra/production-images.lock.json`.

Le projet Compose reste `educapilote` : les volumes PostgreSQL et Redis existants
sont réutilisés. **Ne pas lancer un second projet contre ces volumes, ne pas faire
`down -v`, ne pas fusionner les fichiers dev et prod et ne pas utiliser
`--remove-orphans`**, car n8n est géré séparément.

La configuration déployée en attendant le domaine est
`docker-compose.dev.yml` + `docker-compose.observability.yml`. Le site reste privé
sur 127.0.0.1:18088. La configuration publique expose seulement Next.js et son BFF ;
les API internes, métriques et consoles ne sont pas routées par Traefik.
Le proxy Nginx conservé sur loopback permet les diagnostics/API opérateur.

## Préparation du VPS

Prévoir Docker Engine + Compose, Python 3, `age`, `flock`, un disque surveillé et
une horloge synchronisée. Sur ce VPS, `/stockage/training`, 64 Go RAM et une RTX 4070
12 Go ont été constatés. La carte est partagée avec d'autres applications ; les
limites Docker de mémoire système ne limitent pas la VRAM. Le port 80 appartient
au Nginx hôte et reste intact.

```bash
cd /stockage/training
python3 scripts/init_production.py
python3 scripts/generate_production.py  # requiert PyYAML, uniquement si sources modifiées
```

Le générateur de production lit le Compose dev. Après modification de la topologie
dev, régénérer la production et valider les deux configurations. Les fichiers de
secrets existent sous un répertoire 0700 ; les fichiers montés dans les conteneurs
sont lisibles par leurs UID. Aucun secret ne doit être inclus dans Git ou une archive.

## Domaine, TLS et mise en service

Reporter les variables de `.env.production.example` dans le `.env` **existant**,
sans écraser les réglages Ollama/JWT. Un domaine réel et un e-mail ACME sont requis.
Faire pointer les enregistrements A/AAAA vers une adresse joignable ; retirer tout
AAAA non fonctionnel. Si le serveur est derrière NAT, transférer le **TCP public
443 vers Traefik**. TLS-ALPN-01 n'a pas besoin du port 80, mais exige l'accès direct
au 443 pour le challenge. Un proxy qui termine TLS avant Traefik doit être adapté.

1. Garder le serveur ACME **staging** pendant la vérification DNS/NAT. Le certificat
   staging n'est pas reconnu par les navigateurs : ce n'est pas la mise en production.
2. Exécuter `docker compose -f docker-compose.prod.yml config --format json |
   python3 scripts/check_production.py` et corriger les erreurs avant le déploiement.
3. Exécuter `bash scripts/deploy_production.sh`. Il construit, sauvegarde, applique
   Alembic puis démarre les services. Un échec interrompt le script.
4. Après succès staging, arrêter seulement Traefik, déplacer `runtime/acme/acme.json`
   dans une sauvegarde privée, régler `EDU_ACME_CA=https://acme-v02.api.letsencrypt.org/directory`
   puis recréer Traefik. Ne pas réutiliser l'état staging comme certificat public.
5. Vérifier avec `curl --fail --head https://VOTRE_DOMAINE/connexion`, sans `-k`, et
   un navigateur : chaîne reconnue, CSP, absence de contenu mixte et cookie
   `edu_session` Secure/HttpOnly/SameSite=Strict après connexion.

Le renouvellement ACME est automatique tant que DNS/routage/disque fonctionnent.
Le dossier `runtime/acme` appartient à UID 10001, mode 0700 ; `acme.json` doit rester
0600. Aucun socket Docker n'est monté dans Traefik. Il n'expose pas de dashboard.
Le TLS public et les parcours en conditions réelles doivent être testés avant
d'ouvrir l'accès aux élèves. La checklist distingue ces validations des tests locaux.

## Ollama GPU et compte Cloud existant

Par défaut le routeur et les embeddings utilisent **l'Ollama hôte déjà connecté**,
via `EDU_OLLAMA_URL=http://ollama-host:11434` et `EDU_OLLAMA_HOST_IP`.
Le compte n'est ni copié dans une image ni remplacé. Le modèle cloud existant reste
`gpt-oss:120b-cloud`, les embeddings locaux restent le modèle validé du module 5.
Vérifier la passerelle avec `scripts/configure_ollama_host.py` si le réseau change.

Pour un serveur conteneurisé indépendant :

```bash
docker compose -f docker-compose.prod.yml --profile local-ollama up -d ollama
docker compose -f docker-compose.prod.yml exec ollama ollama list
```

Le runtime NVIDIA Container Toolkit est requis. Le port 11434 n'est pas publié.
Ce profil ne télécharge aucun gros modèle et n'importe aucune authentification.
Avant de basculer `EDU_OLLAMA_URL=http://ollama:11434`, installer les modèles exacts,
effectuer les smoke tests et connecter explicitement le compte si le Cloud doit
passer par ce runtime. Sans cela, conserver l'hôte. Le profil utilise un volume
`ollama_data` distinct et ne perturbe pas le daemon hôte.

## Observabilité et accès opérateur

```bash
ssh -N -L 13000:127.0.0.1:13000 -L 19090:127.0.0.1:19090 root@192.168.1.10
```

Grafana : http://127.0.0.1:13000, utilisateur `admin`, mot de passe dans
`secrets/grafana_password` à consulter localement de façon confidentielle.
Prometheus : http://127.0.0.1:19090. Ne pas publier ces ports. Grafana utilise le
transport SSH ; le cookie Secure est donc désactivé pour ce point d'accès HTTP local.
Configurer Secure et une origine HTTPS si l'accès Grafana change.

Le dashboard « ÉDUCAPILOTE — Exploitation » est provisionné automatiquement :
services disponibles, latence p95, erreurs 5xx, CPU/RAM/disque du VPS, GPU, appels et
tokens IA, âge du backup, journaux filtrés. La charge serveur est celle du **VPS
entier**, pas uniquement de cette application. Node Exporter a une vue en lecture
seule sur l'hôte ; il n'a pas de port public ni de socket Docker.

Les prix IA sont vides par défaut. Renseigner **les deux** valeurs
`EDU_AI_INPUT_EUR_PER_MILLION` et `EDU_AI_OUTPUT_EUR_PER_MILLION` pour afficher une
estimation. Elle exclut abonnements, forfaits et usages dont les tokens ne sont
pas retournés ; elle n'est pas une facture. Les compteurs se réinitialisent au
redémarrage, les graphiques utilisent `rate`/`increase`. Les quotas d'appels Redis
et les consentements continuent d'être appliqués indépendamment du monitoring.

Les alertes Prometheus couvrent services/dépendances indisponibles, 5xx, latence,
disque, RAM et backup périmé. Elles sont consultables dans Prometheus ; **aucune
notification d'astreinte externe n'est configurée**, faute de destinataire/canal.

Rétention : Prometheus 15 jours / plafond 2 Go ; Loki 7 jours avec compacteur ;
fichiers techniques 7 jours calendaires, 3 fichiers de 5 Mo par service et par jour.
Le timer hôte purge ces fichiers. Le plafond local théorique est environ 1,6 Go.
Alloy lit exclusivement ces fichiers applicatifs, pas les logs d'autres projets.
Les logs Docker de diagnostic restent bornés à 3 × 10 Mo et ne sont pas envoyés
à Loki ; ils doivent rester réservés aux opérateurs.

La télémétrie HTTP ne contient que service, route **gabarit**, méthode, statut,
durée et identifiant technique aléatoire. Ni IP, école, élève, prompt, réponse,
URL complète, cookie, autorisation ni paramètres SQL ne sont collectés. Les logs
techniques ne remplacent pas les journaux d'audit métier stockés sous RLS.

## Sentry

`sentry-forwarder` est un relais séparé avec sortie réseau ; les services n'ont
pas besoin d'un SDK qui inspecte leurs requêtes. `secrets/sentry_dsn` est vide par
défaut. Après choix du projet Sentry, de sa région, de sa rétention et validation
contractuelle, écrire le DSN dans ce fichier et **recréer** le relais.

Le relais transmet seulement les 5xx avec un message fixe, le nom de service et
le code HTTP. Le filtre `before_send` reconstruit l'événement depuis une liste
autorisée. Les intégrations automatiques, breadcrumbs, traces, variables locales,
profils et sessions sont désactivés. Aucun SDK navigateur/session replay.
Ce mode permet le suivi et regroupement des erreurs, **pas une stacktrace riche**.
Le transport est best effort ; il n'est pas une file d'audit garantie. DSN vide :
aucun événement envoyé et les offsets avancent, donc pas d'envoi rétroactif.

## Sauvegarde, restauration et reprise

Une sauvegarde SQL cohérente `pg_dump` est compressée puis chiffrée en streaming
avec `age`. Aucun dump clair intermédiaire n'est écrit. `backup_production.sh`
échoue si la clé destinataire manque. Il écrit un SHA-256, une métrique de succès,
emploie un verrou et conserve les backups chiffrés 14 jours.

Provision initiale, si aucune clé n'existe :

```bash
umask 077
age-keygen -o secrets/backup_identity
age-keygen -y secrets/backup_identity > secrets/backup_recipient
```

Exporter la clé privée dans un coffre hors du VPS et une copie chiffrée des secrets
applicatifs (clés PII/JWT, rôles DB, configuration, ACME). La clé privée locale
permet les tests, mais **ne constitue pas une séparation de sécurité**. Après
validation hors site, retirer la copie privée du VPS selon la politique retenue.
Ne jamais perdre les clés PII : le dump seul ne suffit pas à déchiffrer les profils.

```bash
EDU_COMPOSE_FILE=docker-compose.dev.yml bash scripts/backup_production.sh
EDU_COMPOSE_FILE=docker-compose.dev.yml bash scripts/restore_postgres.sh \
  backups/encrypted/LE_FICHIER.sql.gz.age secrets/backup_identity
```

La restauration crée `edu_restore_...`, valide 54 tables/propriétaires et la
révision `0007_student_controls`, puis la conserve pour inspection. En échec, elle
supprime uniquement cette base temporaire. Elle **n'écrase jamais** `educapilote`.
Sur un nouveau serveur, initialiser d'abord les rôles et secrets PostgreSQL.
Le dump n'inclut pas les mots de passe des rôles, Redis, ACME ou les modèles.

Pour une reprise réelle : isoler l'accès, arrêter web/services/worker, sauvegarder
l'état restant, restaurer et inspecter la base isolée, effectuer une bascule
contrôlée de `EDU_DB_NAME` pour tous les services et les outils, redémarrer puis
exécuter la recette. Invalider les sessions auth/web Redis avant réouverture et
rejouer les effacements/consentements intervenus après la date de sauvegarde.
Cette opération implique une interruption et une validation opérateur ; aucun
script ne supprime automatiquement la base active.

Les unités `infra/systemd/educapilote-*` exécutent un backup quotidien à 02:15 UTC
et la collecte GPU/purge chaque minute. Elles ciblent le même projet existant via
le fichier dev, ce qui permet la maintenance sans variables de domaine.
Installer les unités, faire `systemctl daemon-reload`, puis activer les deux timers.
Contrôler régulièrement une restauration et les horodatages de succès.
Objectif initial : RPO 24 h ; **RTO non engagé**, à mesurer avec un volume réaliste.

Une copie hors site chiffrée, un compte de stockage et une politique d'immuabilité
restent à configurer. Les sauvegardes locales seules ne protègent pas d'une perte
totale du VPS. Les anciens backups de développement ne sont pas convertis ni
supprimés automatiquement.

## Validation et retour arrière

```bash
python3 scripts/smoke.py
python3 scripts/smoke_web.py
bash scripts/test_module78.sh
docker compose -f docker-compose.dev.yml -f docker-compose.observability.yml exec -T \
  prometheus promtool check config /etc/prometheus/prometheus.yml
```

Voir `docs/validation-module11.md` pour les résultats réellement obtenus.
`python3 scripts/package_release.py` prépare une archive des sources avec manifeste
SHA-256, sans secrets, données, dépendances installées ni fichiers de runtime.
Conserver les images précédentes et un backup avant migration. Ce module n'ajoute
pas de migration SQL ; revenir aux images précédentes reste possible sans
downgrade. Revenir au mode privé exige de rétablir l'origine HTTP et les cookies
adaptés, puis de recréer web. Ne pas tenter un downgrade de données improvisé.

Après remplacement de fichiers bind-mountés par extraction d'archive, **recréer
les conteneurs concernés** : un simple reload peut conserver l'ancien inode.

## Références

- [Traefik ACME et TLS-ALPN-01](https://doc.traefik.io/traefik/reference/install-configuration/tls/certificate-resolvers/acme/)
- [Prometheus : histogrammes](https://prometheus.github.io/client_python/instrumenting/histogram/)
- [Grafana : ingestion Loki avec Alloy](https://grafana.com/docs/loki/latest/send-data/alloy/)
- [SDK Sentry Python : paramètres de collecte](https://getsentry.github.io/sentry-python/api.html)
- [CNIL : systèmes d'IA dans l'éducation](https://www.cnil.fr/fr/education-mise-en-place-systeme-ia)

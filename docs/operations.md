# Exploitation

## Démarrage et santé

```bash
docker compose -f docker-compose.dev.yml up -d --build
docker compose -f docker-compose.dev.yml ps -a
docker compose -f docker-compose.dev.yml logs --tail=100 migrate
```

`migrate` doit sortir à zéro ; postgres, redis et les 15 services doivent être
sains avant le démarrage du proxy. Un healthcheck Docker ne redémarre pas à lui
seul un processus vivant mais défaillant : la supervision de production devra
alerter et appliquer la politique de rétablissement définie par l'opérateur.

Le nom de projet est `educapilote`. Ne pas changer ce nom sur une installation
existante sans migrer les volumes. Aucun service existant du VPS n'est réutilisé.
Les budgets mémoire configurés totalisent environ 6,4 Gio au maximum hors tests,
et la consommation réelle doit être mesurée pour dimensionner l'hôte.

## Migrations

```bash
docker compose -f docker-compose.dev.yml run --rm migrate alembic current
docker compose -f docker-compose.dev.yml run --rm migrate alembic check
docker compose -f docker-compose.dev.yml run --rm migrate alembic upgrade head
bash scripts/verify_migrations.sh
```

La migration est transactionnelle et sérialisée par verrou consultatif. Les
extensions et rôles sont initialisés au premier démarrage d'un volume vierge.
Changer les fichiers secrets ensuite ne change pas les mots de passe SQL : une
rotation nécessite ALTER ROLE puis mise à jour coordonnée des secrets et services.

`alembic downgrade base` supprime les tables et données du module ; réserver cette
commande aux bases de test jetables. Les extensions et rôles de bootstrap restent
présents. Ne jamais modifier une migration appliquée : ajouter une révision.

## Sauvegarde

```bash
bash scripts/backup.sh
bash scripts/verify_restore.sh
```

La sortie est un dump SQL gzip privé dans `backups/`, avec propriétaires et ACL.
Le pipeline échoue si pg_dump ou gzip échoue. Déplacer ensuite la sauvegarde vers
un stockage protégé, chiffré et séparé, avec une durée de conservation approuvée.
Conserver aussi hors dépôt les secrets et les clés de chiffrement applicatives.
Le dump de données n'est pas à lui seul une sauvegarde complète des accès.

## Exercice de restauration dans une base séparée

Exécuter avec le nom d'une base de restauration neuve, jamais sur la base active :

```bash
docker compose -f docker-compose.dev.yml exec -T postgres createdb -U postgres educapilote_restore
docker compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d educapilote_restore -v ON_ERROR_STOP=1 -c 'CREATE EXTENSION vector'
gzip -dc backups/<sauvegarde>.sql.gz | docker compose -f docker-compose.dev.yml exec -T postgres psql -U postgres -d educapilote_restore -v ON_ERROR_STOP=1
```

Le dump restaure les tables, données, propriétaires, droits, triggers et politiques.
Les rôles doivent exister avant restauration : ils sont déjà présents lors d'un
exercice sur le même cluster. Sur une instance neuve, reproduire d'abord le
bootstrap et les secrets. Restreindre aussi CONNECT sur la base restaurée comme
dans le bootstrap. Ne pas lancer Alembic avant restauration d'un dump complet.
La reprise complète doit être répétée sur une instance isolée.

## Purge des traces

```bash
docker compose -f docker-compose.dev.yml run --rm migrate \
  python -m scripts.purge_expired --tenant <uuid-tenant>
```

Les dates d'expiration sont définies à l'écriture selon la politique validée.
La commande est explicite et ne planifie pas de tâche automatique. Les audits
restent immuables pour les comptes métier ; seul le compte de maintenance purge
les lignes expirées du tenant fourni.

## Vérification TLS isolée

```bash
sudo bash scripts/verify_tls.sh
```

Ce test crée un certificat éphémère pour localhost, valide Nginx et vérifie un
handshake HTTPS sur un port local dynamique. Le conteneur et le certificat sont
supprimés en fin de test. Le proxy actif n'est pas modifié. Ce certificat de test
ne sert jamais à une publication réelle.

## Module 2

Initialiser les secrets supplémentaires avec `python3 scripts/init_security_secrets.py`
avant de construire les images. La procédure de création d’école et du premier
administrateur est dans [module2.md](module2.md). Aucun compte par défaut n’est créé.
Exécuter `bash scripts/test_module2.sh` pour les 93 tests dans une base jetable.
Sauvegarder séparément les fichiers de clés JWT et PII ; les anciens identifiants
de clés restent nécessaires à la vérification et au déchiffrement des données.
La migration 0002 refuse une rétrogradation qui ferait perdre des données nouvelles.

## Module 3

Le graphe national et les contenus versionnés sont décrits dans [module3.md](module3.md).
Exécuter `bash scripts/test_module3.sh` pour la suite actuelle dans une base jetable.
Les nouveaux secrets `redis_curriculum` et `redis_content` sont générés par le
script de secrets existant ; aucune clé PII ou de signature privée n’est montée
dans ces deux services. La migration courante est `0003_curriculum_content`.

## Module 4

Le moteur d’exercices et l’évaluation sont décrits dans [module4.md](module4.md).
Les nouveaux secrets Redis sont créés avec le script existant, sans écrasement.
Assessment reçoit la clé de chiffrement des réponses ; exercise reçoit seulement
les clés publiques JWT et la clé de limitation. La migration courante est 0004.
Utiliser `bash scripts/test_module4.sh` pour la suite actuelle en base jetable.
Les réponses et preuves de maîtrise sont historiques : définir une politique de
conservation et un parcours d’effacement complet avant collecte de données réelles.

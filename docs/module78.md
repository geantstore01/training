# Modules 7 et 8 — suivi, administration et accessibilité

Les cinq services utilisent les JWT révocables, les rôles et l'isolation PostgreSQL par établissement des modules précédents. Chaque dossier `services/<service>/openapi.json` contient son contrat intégral. Les API sont exposées sous `/services/<service>` ; la documentation interactive se trouve à `/docs` sous ce préfixe.

## Classes et progression

| Service | Endpoints principaux |
|---|---|
| class | `POST/GET /classes`, `POST /classes/{id}/students`, `DELETE /classes/{id}/students/{student_id}` |
| class | `POST/GET /classes/{id}/groups`, `PUT /classes/{id}/groups/{group_id}` |
| class | `POST/GET /classes/{id}/missions`, `POST /classes/{id}/missions/{mission_id}/archive`, `GET /missions/today` |
| analytics | `GET /dashboard`, `GET /students/{id}/dashboard`, `GET /classes/{id}/dashboard` |
| admin | `GET /moderation/pending`, `GET /safety/events`, `POST /safety/events/{id}/review`, `GET /feature-flags`, `PUT /feature-flags/{key}` |
| speech | `POST /synthesize` |
| notification | `POST /jobs`, `GET /jobs/{id}`, `GET /inbox`, `POST /inbox/{id}/read`, `POST /automation/jobs` |

Un enseignant ne gère que ses classes ; les administrateurs restent limités à leur établissement. Les missions utilisent uniquement des versions d'exercices publiées, du niveau de la classe. Un groupe ne peut contenir que des élèves inscrits. Après désinscription, les missions et groupes concernés deviennent inaccessibles à l'élève. Les exercices archivés ne sont plus proposés dans les missions du jour.

Les tableaux de bord présentent les compétences acquises, à retravailler et en apprentissage, ainsi que les tentatives terminées. Ils ne renvoient ni probabilité de maîtrise, ni score, ni classement. Le temps est une **estimation issue des sessions closes** : intervalles recoupés, chevauchements fusionnés, plafond de 30 minutes par session. Ce n'est pas une mesure du temps d'attention. Les compétences reflètent l'état actuel ; les sessions et tentatives sont filtrées sur la période demandée.

## Administration

Le back-office livré est une API documentée par OpenAPI, sans interface graphique spécifique. La file de modération réunit leçons, exercices et documents RAG. Chaque entrée indique `review_path` vers l'endpoint de validation du service propriétaire : les règles de relecture humaine et de séparation auteur/relecteur restent appliquées par ces services.

La supervision de sécurité expose des catégories, niveaux de gravité, actions et identifiants, sans texte brut de conversation. Les décisions de revue sont immuables. Les drapeaux `missions`, `speech` et `notifications` sont propres à chaque établissement ; une modification exige `expected_revision` pour éviter d'écraser une décision concurrente.

## Voix locale

Le client transmet l'identifiant d'un exercice publié. Le service lit sa consigne avec **eSpeak NG, voix française**, après vérification du consentement parental et de l'assentiment de l'élève pour la voix. La réponse est un WAV avec `Cache-Control: no-store`. Le texte passe sur l'entrée standard du processus ; l'audio reste en mémoire. Aucun fichier audio temporaire n'est créé, donc aucun nettoyage différé n'est nécessaire.

La transcription STT, optionnelle dans la demande, n'est pas activée et aucun endpoint fictif n'est fourni. La voix eSpeak est une synthèse fonctionnelle, moins naturelle qu'une voix neuronale.

## Notifications et traitements durables

Les rapports hebdomadaires sont livrés dans la **boîte de notifications interne** des parents dont le lien de responsabilité est vérifié et actif. Aucun courriel n'est envoyé : aucun serveur SMTP n'a été fourni. Une révocation du lien supprime immédiatement l'accès aux notifications correspondantes.

Un rapport couvre la semaine UTC précédente pour les activités et inclut l'état actuel des compétences. Les alertes enseignants détectent au moins trois tentatives de faible réussite ou deux sollicitations d'aide élevée sur sept jours ; leur texte ne révèle pas de note. Les destinataires sont les enseignants actuellement affectés. Les notifications expirent après 30 jours.

`notification-worker` utilise les jobs transactionnels PostgreSQL et une file de réveil Redis. Le registre SQL permet de reprendre après indisponibilité de Redis ou redémarrage du worker. Une enveloppe globale ne contient que les identifiants du job et de l'établissement ; chaque traitement utilise ensuite une transaction sous RLS. Les droits du demandeur sont revalidés à l'exécution. Les effets métier et l'état final sont validés ensemble. Les erreurs sont réessayées cinq fois au maximum avec temporisation ; seul leur code de classe est conservé.

Les clés d'idempotence évitent de rejouer une demande. Les rapports et alertes ont également une unicité par destinataire, élève, type et période. Les lots comprennent au plus dix exercices : génération déterministe, dix contrôles, stockage en **brouillon**, puis validation humaine habituelle. Les rapports sont bornés à 1 000 élèves accessibles par job ; au-delà, le job échoue explicitement.

La purge supprime les traces arrivées à échéance, les notifications expirées et les jobs terminés depuis 30 jours. Elle ne supprime pas les comptes, consentements ni preuves pédagogiques. Les interactions encore référencées par un événement de sécurité sont conservées jusqu'à expiration de ce dernier. Ce mécanisme de rétention ne remplace pas une procédure complète d'exercice des droits RGPD.

## n8n

`docker-compose.n8n.yml` fournit une instance séparée, avec image fixée par digest et volume persistant. Elle écoute seulement sur `127.0.0.1:15678`. Les quatre fichiers `workflows/n8n/*.json` sont importables : rapports le lundi à 8 h, alertes les jours de semaine à 17 h, purge à 3 h, lots sur webhook. Le fuseau des déclencheurs est Europe/Paris. Tous sont livrés **inactifs**, sans secrets, sans sauvegarde des données d'exécution.

```bash
docker compose -f docker-compose.n8n.yml --profile automation run --rm n8n import:workflow --separate --input=/workflows
docker compose -f docker-compose.n8n.yml --profile automation up -d
```

Accès distant par tunnel : `ssh -L 15678:127.0.0.1:15678 root@192.168.1.10`, puis `http://localhost:15678`. Créer le compte propriétaire n8n lors du premier accès. La configuration HTTP locale désactive le cookie sécurisé ; une exposition publique exige un reverse-proxy HTTPS et sa réactivation.

Chaque automatisation doit être liée à un compte actif de l'établissement. Après création de ce compte via le bootstrap existant, provisionner sa clé (remplacer les UUID et choisir les tâches compatibles avec ses rôles) :

```bash
docker compose -f docker-compose.dev.yml run --rm --no-deps --user 0 \
  -v "$PWD/secrets/automation_keys:/work/automation_keys" \
  -e EDU_AUTOMATION_KEYS_FILE=/work/automation_keys \
  migrate python -m scripts.create_automation_key \
  --school UUID_ETABLISSEMENT --user UUID_COMPTE \
  --kinds weekly_reports difficulty_alerts privacy_purge
```

Le registre n'affiche aucun secret dans les logs. Dans n8n, configurer le credential **Educapilote automatisation établissement** en Header Auth : nom `X-Edu-Automation`, valeur de la clé du registre protégé `secrets/automation_keys`. Configurer séparément **Educapilote webhook entrant** avec un secret d'appel distinct. Affecter ces credentials aux nœuds importés avant activation. Dupliquer les workflows et leurs credentials pour chaque établissement ; ne pas partager une clé entre écoles.

Pour un lot, appeler le webhook de production du workflow actif avec son en-tête d'authentification et un JSON contenant `idempotency_key` (UUID) et `generations` (schémas du service exercise). Les autres webhooks imposent leur type de tâche. Désactiver un compte bloque ses traitements ; retirer sa clé du registre révoque l'intégration.

## Installation et vérification

```bash
python3 scripts/init_security_secrets.py
docker compose -f docker-compose.dev.yml build
bash scripts/backup.sh
docker compose -f docker-compose.dev.yml run --rm migrate alembic upgrade head
docker compose -f docker-compose.dev.yml up -d --wait
bash scripts/test_module78.sh
bash scripts/verify_migrations.sh
bash scripts/verify_restore.sh
python3 scripts/smoke.py
docker compose -f docker-compose.dev.yml exec -T speech-service python - < scripts/smoke_speech.py
```

La migration `0006_school_operations` ajoute sept tables, dont six sous RLS forcée, et les permissions nécessaires aux nouveaux services. Le monorepo contient 52 tables métier. La recette de développement reste liée aux interfaces locales ; la mise en production publique nécessite les paramètres TLS et d'exploitation décrits dans le guide d'infrastructure.

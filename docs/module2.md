# Module 2 — accès, profils et sécurité

## Architecture livrée

Les trois applications FastAPI sont dans `services/auth-service/app`,
`services/user-service/app` et `services/safety-service/app`. Chaque service
dispose de ses schémas Pydantic, routes et contrat `openapi.json`.
Les primitives communes sont dans `shared/security/` ; les entités restent dans
`shared/db/models.py`. La migration `0002_access_safety` complète la migration
initiale, qui n'a pas été réécrite. Le schéma contient désormais **39 tables métier**.

Une école est la frontière d'autorisation : `school_id` dans les API et JWT vaut
`tenant_id` dans le schéma historique. PostgreSQL impose `schools.id = tenant_id`
et une seule école par tenant. Une base historique avec un autre découpage est
refusée par la migration jusqu'à ce que son mapping soit explicitement corrigé.
Aucun header envoyé par le client ne peut sélectionner une autre école.

## Authentification

| Méthode et chemin auth-service | Accès et effet |
|---|---|
| POST `/login` | `school_id`, login pseudonyme et mot de passe ; retourne un couple de jetons |
| POST `/refresh` | Consomme une fois le refresh token et émet un nouveau couple |
| POST `/logout` | Révoque la session du bearer courant |
| POST `/logout-all` | Incrémente la version de sécurité du compte et invalide toutes ses sessions |
| POST `/password` | Vérifie l'ancien mot de passe, remplace le hash et invalide toutes les sessions |
| GET `/me` | Identité technique, école, rôles et session authentifiés |
| GET `/.well-known/jwks.json` | Clés publiques RSA ; aucune clé privée |

Les JWT d'accès sont signés **RS256**, avec `kid`, issuer, audience, expiration,
`nbf`, `iat`, `jti`, `sub`, `school_id`, `roles`, `sid`, `ver` et un type `access`.
Leur durée par défaut est de cinq minutes. Les algorithmes et types inattendus
sont refusés. Seul auth-service monte la clé privée. Les deux autres services
ne disposent que du jeu de clés publiques.

Les refresh tokens sont opaques et aléatoires. Redis ne stocke que leurs SHA-256,
dans une famille de session à durée absolue de sept jours. La rotation et la
détection de réutilisation utilisent un script Lua atomique. La réutilisation
d'un ancien token connu révoque toute sa famille, y compris les JWT déjà émis.
Un token aléatoire incorrect ne révoque pas une session légitime. Deux refresh
concurrents du même token entraînent une seule réussite puis la révocation de la
famille : le client doit sérialiser ses rafraîchissements. Au plus 1 000 rotations
par famille ; ensuite une nouvelle connexion est requise.

Chaque requête protégée vérifie la famille Redis, le statut courant du compte,
sa version de sécurité et ses rôles en base. Une déconnexion, un verrouillage ou
un changement de mot de passe bloque les requêtes suivantes sans attendre la
fin du JWT. Une requête déjà autorisée et en cours ne peut pas être rappelée.
Une panne de dépendance renvoie 503 ; aucun mode dégradé n'accepte le JWT seul.

Les mots de passe sont hachés en Argon2id (64 Mio, trois passes, parallélisme 2).
Le nombre de calculs concurrents est borné à deux par processus. Les nouveaux
mots de passe ont 12 à 128 caractères, sans imposer de règles de composition
peu adaptées aux phrases de passe. Le login a un format pseudonyme, sans email.

Les limites distribuées incluent cinq tentatives de connexion par compte/minute,
60 par adresse source/minute et 20 refresh par session/minute. Les clés de compteur
sont dérivées par HMAC, sans login ni adresse IP en clair. Derrière un proxy non
déclaré de confiance à Uvicorn, l'adresse source est celle du proxy : la limite
est alors partagée. Ne jamais accepter aveuglément un header IP du client.

Les jetons sont retournés en JSON pour des clients API utilisant Authorization
Bearer. Ce module ne crée pas de cookies de session. Les réponses métier sont
`Cache-Control: no-store`. Les erreurs de validation ne recopient pas les valeurs
rejetées. Les corps sont limités à 32 Kio, et le texte safety à 6 000 caractères.

## Rôles et profils

Les seuls rôles acceptés sont `student`, `parent`, `teacher`, `school_admin`,
`content_creator` et `sys_admin`. Les anciens rôles du socle sont migrés :
guardian → parent, moderator → content_creator, tenant_admin → sys_admin.

| Rôle | Autorisations du module |
|---|---|
| student | Son profil, ses préférences, ses accords et l'analyse de son texte |
| parent | Profils des enfants liés et vérifiés, préférences et ses propres consentements |
| teacher | Profils/préférences des élèves de ses classes avec inscription actuellement valide |
| school_admin | Gestion des comptes et profils de son école, vérification/révocation des liens parentaux |
| content_creator | Son compte et l'analyse de contenu sans contexte élève ; pas de lecture de dossiers élèves |
| sys_admin | Fonctions administrateur de son école et provisionnement explicite d'une nouvelle école |

Le rôle sys_admin n'est pas un bypass RLS permettant de lire tous les enfants.
Son JWT demeure lié à une école. La création d'une école est une route dédiée
qui génère son identifiant côté serveur. La création de sys_admin est réservée
au provisionnement opérateur, jamais à une demande HTTP d'élévation de rôle.

| Méthode et chemin user-service | Fonction |
|---|---|
| GET `/me` | Compte courant et références de profils |
| POST, GET `/accounts` | Créer/lister les comptes de l'école ; listes paginées |
| PATCH `/accounts/{id}` | Verrouiller/réactiver ou réinitialiser un mot de passe ; sessions invalidées |
| POST `/schools` | Provisionner une école et son school_admin, pour sys_admin |
| GET `/students` | Liste paginée limitée aux droits du demandeur |
| GET `/students/{id}` | Profil pseudonyme autorisé |
| GET `/students/{id}/identity` | Identité déchiffrée d'un élève autorisé, lecture auditée |
| PATCH `/students/{id}` | Mise à jour administrative de l'identité, du pseudonyme ou du niveau |
| PUT `/students/{id}/preferences` | Préférences d'affichage et de lecture, sans données médicales |
| POST `/guardian-links` | Enregistrer une vérification d'autorité parentale par l'administrateur |
| POST `/guardian-links/{id}/revoke` | Révoquer le lien sans supprimer l'historique |
| GET `/consent-policy` | Notice versionnée et finalités séparées |
| POST `/students/{id}/consents` | Accord ou refus du parent authentifié et lié |
| POST `/students/{id}/consents/withdraw` | Nouvel événement de retrait |
| GET `/students/{id}/consents` | Historique paginé ; le parent ne lit que ses déclarations |
| POST `/me/assents` | Accord/retrait de l'élève authentifié, dans un registre distinct |
| GET `/students/{id}/permissions` | État effectif pour ai_local, ai_cloud et voice |

Les profils élèves portent un prénom et un nom chiffrés, un pseudonyme et CM1/CM2.
Les emails, identités, références de vérification et preuves de consentement sont
chiffrés par **AES-256-GCM**, avec nonce aléatoire et enveloppe versionnée. L'AAD lie
le ciphertext à l'école, au propriétaire et à la finalité du champ. Une copie de
ciphertext dans un autre dossier ne peut pas être déchiffrée. Seuls user-service
et safety-service montent les clés PII ; aucune clé ne figure dans le dépôt.

La vérification parentale est une opération humaine : l'administrateur contrôle
l'autorité du représentant hors de l'API puis enregistre une référence chiffrée.
Le code impose son rôle et conserve l'attribution ; il ne prétend pas vérifier
automatiquement une pièce d'identité ou la réalité juridique de cette autorité.
Un lien révoqué n'est pas réactivable par l'API, afin de ne pas réactiver d'anciens
accords implicitement.

## Consentements

Les nouvelles entrées sont append-only jusque dans PostgreSQL : UPDATE et DELETE
sont interdits, y compris par trigger. Accord, refus et retrait restent des
événements distincts avec auteur, notice, finalité, preuve chiffrée, révision et
référence à l'événement précédent. Les insertions concurrentes d'un même flux
sont sérialisées. Les preuves historiques du module 1 sont conservées comme
entrées `legacy`, en lecture seule.

La politique choisie pour les aides optionnelles exige un dernier accord valide
de **chaque représentant lié et vérifié**, plus l'accord de l'élève, pour la
version actuelle de la notice. Un retrait, un accord expiré ou une nouvelle notice
ferme l'accès correspondant. C'est une politique produit conservatrice, pas une
affirmation qu'un nombre donné de représentants est exigé dans tous les cas.
L'administrateur ne peut pas enregistrer un consentement parental via son JWT.

Le registre apporte les mécanismes et preuves techniques ; la détermination des
bases légales, la qualité de la vérification humaine et les autres obligations
RGPD restent à valider par le responsable de traitement. La CNIL décrit le
[consentement](https://www.cnil.fr/fr/les-bases-legales/consentement) et l'accord
conjoint pour certains services en ligne proposés aux
[moins de 15 ans](https://www.cnil.fr/fr/recommandation-4-rechercher-le-consentement-dun-parent-pour-les-mineurs-de-moins-de-15-ans).

## Safety : dix couches exécutées

POST `/analyze` demande un bearer, un texte, un éventuel student_id et une
destination local/cloud. Le student_id est imposé depuis le JWT pour un élève ;
un parent/enseignant doit fournir un contexte auquel il a réellement accès.

| Couche | Contrôle |
|---|---|
| 1 | Taille, Unicode de contrôle, normalisation bornée et charges encodées |
| 2 | Tentatives de suppression ou contournement des instructions |
| 3 | Imitation des rôles système/développeur et marqueurs de jailbreak |
| 4 | Demandes de coordonnées, secrets et données personnelles |
| 5 | Exécution d'outils, code et requêtes d'exfiltration |
| 6 | Contenus sexuels explicites et sollicitations inappropriées |
| 7 | Instructions dangereuses, armes et violence |
| 8 | Détresse, automutilation et signalements de harcèlement |
| 9 | Haine, insultes et demandes d'humiliation |
| 10 | Pseudonymisation PII, contrôle résiduel et accord requis avant sortie transmissible |

La détection combine règles françaises/anglaises, variantes normalisées et NER
français local `fr_core_news_sm` 3.8.0. Les noms connus du profil autorisé et de
l'école sont masqués même lorsque le NER ne les reconnaît pas. Marqueurs :
`[STUDENT_ID]`, `[SCHOOL_ID]`, `[EMAIL]`, `[PHONE]`, `[ADDRESS]`, `[ORGANIZATION]`,
`[IDENTIFIER]`, `[URL]`. Aucune table de correspondance ni portion brute détectée
n'est retournée ou journalisée.

La réponse contient decision (`allow`, `redact`, `block`), sanitized_text,
les dix résultats et des compteurs. **Si la décision est block, sanitized_text
est null.** Une défaillance du moteur renvoie 503, sans texte non filtré.
Un cas de détresse produit un message fixe adapté à l'enfant et
`requires_adult_support=true` ; ce drapeau ne signifie pas qu'une notification
a déjà été envoyée. Les événements ne contiennent que codes, UUID et expiration.

La reconnaissance des noms propres et les règles de menace peuvent avoir des
faux positifs et des faux négatifs. Ce système est une pseudonymisation, pas une
garantie d'anonymisation universelle ni un classifieur sémantique exhaustif.
Les futurs services IA devront appeler ce point de contrôle au moment de chaque
requête et transmettre uniquement sanitized_text après succès. La décision est
un état instantané, pas une autorisation réutilisable après un retrait.
Aucun appel IA/cloud n'est exécuté par le module 2.

Le modèle est distribué sous LGPL-LR, téléchargé lors du build depuis sa
[publication officielle](https://github.com/explosion/spacy-models/releases/tag/fr_core_news_sm-3.8.0),
avec SHA-256 fixé dans requirements-safety.lock. Voir les
[modèles français spaCy](https://spacy.io/models/fr).

## Secrets et déploiement

```bash
cd /stockage/training
python3 scripts/init_secrets.py
python3 scripts/init_security_secrets.py
docker compose -f docker-compose.dev.yml up -d --build
```

Le second script nécessite cryptography (présent dans les images du module).
Il n'écrase jamais les fichiers existants et ne montre aucune valeur. Les fichiers
sont dans un dossier hôte 0700 et montés seulement dans leurs services destinataires.
Redis utilise trois comptes ACL distincts. user et safety ne peuvent pas modifier
les familles de sessions ; le compte des autres services est limité à `cache:*`.
L'AOF Redis est en `appendfsync always`. Après changement de son fichier monté,
redémarrer Redis pour appliquer la configuration.

Pour créer le premier administrateur, saisir le mot de passe au terminal :

```bash
docker compose -f docker-compose.dev.yml run --rm -it --no-deps \
  --entrypoint python user-service -m scripts.bootstrap_school \
  --name "Nom de votre école" --login administrateur --system-admin
```

Le script retourne le school_id nécessaire à la connexion. Aucun compte ou mot
de passe par défaut n'est créé automatiquement. L'API est joignable sous
`/services/<nom-service>/...`, Swagger sous `/services/<nom-service>/docs`.
Le proxy de développement reste lié à 127.0.0.1:18088 ; l'overlay TLS du module 1
s'applique aux nouvelles routes.

Pour changer la clé de signature, distribuer d'abord le jeu de clés publiques
contenant ancienne et nouvelle clés aux vérificateurs, puis basculer la clé privée
d'auth-service et EDU_JWT_ACTIVE_KID. Recréer les conteneurs concernés car Compose
monte des fichiers. Conserver l'ancienne clé publique jusqu'à expiration des JWT
qu'elle a signés. Les refresh tokens opaques ne dépendent pas de cette clé. Pour
les clés PII, conserver les clés de lecture tant que données ou sauvegardes les
utilisent ; changer `active` ne ré-encrypte pas les anciennes données.

La rotation de refresh suit les principes de détection de réutilisation du
[RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html).

## Vérification

```bash
bash scripts/test_module2.sh
bash scripts/verify_migrations.sh
bash scripts/verify_restore.sh
python3 scripts/smoke.py
```

Le premier script crée une base PostgreSQL temporaire, y applique les migrations,
vérifie leur correspondance avec les modèles et exécute tous les tests. Les
sessions de test utilisent Redis DB 15 et des clés uniques, supprimées ensuite.
Aucune donnée de test n'est injectée dans la base active.

Le downgrade est implémenté sur une base sans données propres au module 2. Il
refuse explicitement de détruire identités chiffrées, consentements, accords ou
événements de sécurité déjà créés ; utiliser alors une restauration contrôlée.
Le rollback de cette tentative conserve les politiques RLS.

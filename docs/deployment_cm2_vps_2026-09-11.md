# Déploiement du 11 septembre 2026

Application transférée de `D:\codex\training` vers `root@192.168.1.10:/stockage/training` et services remplacés avec le Compose déjà utilisé par le VPS. Ce document est chronologique : la section **Relais au prochain assistant** en fin de fichier décrit l’état courant et prévaut sur les constats plus anciens. Aucun secret n’est enregistré dans ce compte rendu.

## Résultat

- Migration active au terme de la dernière intervention : `0018_course_progress_read`.
- 17 services applicatifs remplacés, dont 16 avec contrôle de santé réussi et le worker démarré. PostgreSQL, Redis, Ollama, proxy et supervision conservés ; proxy Nginx vérifié puis rechargé.
- 4 comptes et 71 versions de cours déjà approuvées conservés.
- Histoire : 6 dossiers éditoriaux, 18 exercices effectivement créés en brouillon, 8 sources enregistrées, 9 documents RAG en brouillon et **51 vrais vecteurs de 768 dimensions**. Aucun avis humain ni approbation automatique créé.
- 385 tests passés dans une base temporaire sur le VPS. Vérification supplémentaire locale du diagnostic d’erreur historique : 23 tests d’histoire passent. Les 13 parcours navigateur ont été vérifiés (11 existants, puis 2 nouveaux d’histoire après correction du contraste). TypeScript et les 6 tests frontend passent.
- Migration testée aussi depuis une restauration de la base existante, avec conservation des 4 comptes et 71 cours. Import documentaire testé deux fois sur une copie : seconde exécution sans doublon.
- Vérification du fournisseur réel avec un texte technique sans données d’élèves : modèle configuré `glm-5.2:cloud`, embeddings `educapilote-embeddinggemma:v1`, plan structuré valide. Il ne s’agit pas d’un modèle entièrement local ; sa configuration existante a été conservée. La rédaction automatique d’un cours complet n’est pas déclarée validée pédagogiquement.
- Page `/connexion` servie par le VPS : HTTP 200 et aucune erreur JavaScript dans le contrôle navigateur. Le catalogue d’histoire sans session renvoie 401.

## Sauvegardes

- `/stockage/training/backups/before-cm2-20260911T092959Z` : sources/configuration originales, sauvegarde PostgreSQL et identifiants d’images antérieures. Répertoire privé.
- `/stockage/training/backups/before-history-switch-20260911T100203Z` : nouvelle sauvegarde PostgreSQL immédiatement avant la bascule.

Les migrations sont additives. Ne pas exécuter une restauration de base active sans examiner les données écrites depuis la sauvegarde. Les anciennes images et le premier lot de sources sont conservés pour organiser un retour en arrière si nécessaire.

## Accès et publication

Le service écoute actuellement sur `127.0.0.1:18088` **sur le VPS**. Aucun domaine public n’était configuré pour ce projet dans les tunnels existants. Son choix a été demandé ; aucune route DNS inventée ni configuration d’un autre site modifiée.

Un tunnel SSH de vérification relie `http://127.0.0.1:18088/connexion` sur le poste Windows au service du VPS. Ce lien ne représente pas une publication sur Internet. Le tunnel local est identifié dans `artifacts/vps-tunnel.pid` ; il peut être arrêté sans arrêter le site du VPS.

L’aperçu de recette `http://127.0.0.1:19093/tests/cm2-preview/?subject=histoire` reste une démonstration locale avec données éphémères. Il est distinct du site du VPS.

Dans l’espace enseignant du site, **Relire les nouveaux dossiers d’histoire** donne accès aux contenus, documents et corrections. Le catalogue élève ne livre que la navigation tant que les nouvelles versions ne sont pas approuvées. Les cours anciens restent accessibles. Les nouveaux parcours mathématiques/français/sciences ont été transférés avec leur code et leurs outils ; ce transfert ne fabrique pas les revues humaines nécessaires à leur publication.

Les dossiers de relecture, exports ClassQuiz/quizli/Interactive-Quiz-Maker et sources téléchargées se trouvent dans `/stockage/training/artifacts/history-review` et `/stockage/training/artifacts/history-sources`. Les comptes propriétaires existants ont été conservés ; aucun compte supplémentaire créé. Les documents et exercices importés sont attribués au créateur de contenu existant pour qu’il puisse les soumettre. Les journaux opérateur ne prétendent pas qu’un humain les a relus.

Journaux techniques : `artifacts/cm2-switch.log`, `cm2-history-integration.log`, `cm2-history-stage-production.log`, `cm2-history-stage-final.log`. Les exemples de commandes et les limites du MVP figurent dans `docs/history/README.md`.

## Mise à jour de la connexion

Le formulaire affiche CP, CE1, CE2, CM1 et CM2, l’identifiant et le mot de passe. L’établissement est configuré côté serveur avec `EDU_LOGIN_SCHOOL_ID` (Compose) / `LOGIN_SCHOOL_ID` (Next.js). Aucun UUID n’est demandé à l’utilisateur. Une configuration absente refuse la connexion proprement. Pour un élève, le niveau sélectionné doit correspondre au profil enregistré ; les droits et le profil proviennent de la session authentifiée. La liste ne crée pas de comptes ni de nouveaux programmes CP–CE2. Les adultes sont dirigés vers leur espace selon leur rôle.

Les comptes existants `demo.admin` et `eleve.cm2.demo` sont renommés `admin` et `eleve1`, sans changer leurs identifiants internes ni leurs données. Les mots de passe des quatre comptes ont été renouvelés à la demande du propriétaire, les versions d’authentification incrémentées et les opérations auditées. Aucun mot de passe n’est conservé dans ce document.

Validation : TypeScript, 15 tests frontend dont 9 tests de connexion ; vérification navigateur réelle sur le VPS des profils élève et administrateur, refus de mauvaise classe et mauvais mot de passe, authentification des deux autres comptes et affichage mobile sans débordement. Seul le service web a été reconstruit et remplacé. Sauvegarde privée : `/stockage/training/backups/before-login-20260911T124432Z`.

## Domaine BoostClasse

Le domaine fourni par le propriétaire, `https://boostclasse.com`, répond via Cloudflare. Les origines HTTPS `boostclasse.com` et `www.boostclasse.com` sont maintenant explicitement autorisées par le serveur web, avec conservation des adresses de recette locales. Les cookies de session portent désormais l’attribut Secure. Aucune confiance automatique n’est accordée aux en-têtes Host/Forwarded pour autoriser une origine ; les requêtes d’autres sites restent refusées.

L’identité visible est BoostClasse : logo vectoriel original (livre ouvert et élan jaune), nom dans les espaces et à la connexion, titre des pages et icône d’onglet. Les noms techniques des services restent inchangés.
Validation sur https://boostclasse.com : connexion navigateur admin et eleve1 vers leur profil, authentification des quatre comptes, cookies Secure, refus de mauvaise classe/mot de passe/origine étrangère, aucun débordement mobile. TypeScript et 17 tests frontend passent.

## Relais au prochain assistant — état courant

### Environnement actif

- Poste de travail : `D:\codex\training`.
- VPS : `root@192.168.1.10`, application dans `/stockage/training`.
- Site public : `https://boostclasse.com`.
- Le projet Docker actif porte le nom `educapilote` et utilise actuellement `/stockage/training/docker-compose.dev.yml`. Ne pas supposer que `docker-compose.prod.yml` pilote les conteneurs en cours : les labels Docker de `educapilote-web-1` indiquent explicitement le fichier Compose actif.
- Migration Alembic vérifiée dans la base active : `0018_course_progress_read`.
- Au dernier contrôle, `educapilote-web-1` et `educapilote-assessment-service-1` étaient `healthy`, et `https://boostclasse.com/api/health` répondait `{"status":"ok"}`.
- Le profil de connexion `eleve1` correspond à l’élève affiché « Lina ». Ne conserver aucun mot de passe dans un fichier Markdown, un test, un journal ou une commande versionnée.

### Publication des cours de français

Les 28 ateliers de français CM2 et leurs 84 exercices sont publiés. Cette publication a été faite à la demande explicite du propriétaire au moyen de `scripts/publish_french_owner.py` et de la migration `0017_owner_publication`. Elle est enregistrée comme décision opérateur et ne fabrique pas de prétendue relecture humaine. Le profil enseignant indésirable a été verrouillé lors de l’intervention précédente ; `/enseignant` redirige vers `/administration`.

Le catalogue élève filtre maintenant les anciens doublons et affiche exactement 28 cours : 8 en grammaire, 6 en conjugaison, 5 en orthographe, 5 en lexique, 2 en lecture et 2 en écriture. La carte héritée « Accorder le verbe avec son sujet » n’est plus présentée dans ce catalogue car elle ne fait pas partie des 28 ateliers suivis.

### Suivi individuel ajouté pour `eleve1`

L’espace français comporte désormais **Ma route dans les cours** avec une barre par cours. Chaque leçon possède un test déterministe de trois exercices : la mini-question, le premier exercice progressif et le second exercice progressif. `apps/web/src/components/student.tsx` utilise ces trois identifiants attachés à la leçon ; il ne remplace plus un exercice du test par une sélection provenant d’un autre cours.

Le bilan est calculé par `GET /students/{student_id}/course-progress?subject=francais` dans `services/assessment-service/app/routes.py` :

- aucune tentative soumise : `non_commencé`, 0 % ;
- une ou deux tentatives : `en_cours`, 33 % ou 67 % ;
- trois exercices automatiquement évaluables : moyenne des trois scores, convertie sur 20 ;
- note supérieure ou égale à 14/20 : `passed`, affiché `PASSED` ;
- note inférieure à 14/20 : `à_revoir` avec la note ;
- au moins une production non évaluable automatiquement : `à_relire`, sans note inventée.

Seule la dernière tentative soumise de chaque exercice compte. Le bilan expose une note agrégée et ne publie ni réponse privée ni corrigé. L’utilisation d’un indice est conservée dans `help_used` afin d’orienter la suite, sans changer artificiellement la note.

Quand le statut est `à_revoir`, l’API construit `adapted_course` uniquement avec le contenu pédagogique approuvé de la leçon et les codes d’erreur enregistrés : objectif ciblé, explication, méthode, exemple travaillé et identifiant de l’exercice à reprendre. Ce contenu apparaît dans le bilan final du parcours avec le bouton **Faire l’exercice ciblé**. Il ne s’agit pas d’une génération libre par un modèle externe.

Le profil réel `eleve1` n’a reçu aucune tentative factice pour la recette. Lors de la vérification finale, ses 28 cours affichaient `À commencer`, `0/3` et 0 %. Toute prochaine évolution doit préserver cet historique réel.

### Fichiers de cette évolution

- `migrations/versions/0018_course_progress_read.py` : droits de lecture minimaux accordés à `edu_assessment` sur les tables de cours.
- `services/assessment-service/app/schemas.py` : contrats `CourseProgress` et `AdaptiveCourse`.
- `services/assessment-service/app/routes.py` : agrégation du test, note et remédiation.
- `apps/web/src/lib/access.ts` : autorisation du nouveau chemin dans le proxy.
- `apps/web/src/lib/contracts.ts` : contrats TypeScript et version de programme des compétences.
- `apps/web/src/components/student.tsx` : test fixe de trois exercices, bilan final et cours adapté.
- `apps/web/src/components/french-library.tsx` : tableau de barres, statut et note sur chaque carte, filtre des 28 ateliers.
- `apps/web/src/components/french-workshop.css` : rendu bureau, petit écran et états visuels.
- `tests/test_french_installation.py` : scénario PostgreSQL `non_commencé → À revoir 0/20 → cours adapté → PASSED 20/20`.

### Validation exécutée

- Front local : `npm run typecheck`, `npm test` avec 17 tests réussis, puis `npm run build` réussi.
- Pédagogie locale : 76 tests réussis ; 3 tests d’intégration ignorés localement faute de base Docker Windows.
- PostgreSQL isolé sur le VPS : les 3 tests de `tests/test_french_installation.py` réussissent, y compris le nouveau scénario de note et de remédiation. La base, le réseau et les volumes de recette portaient le projet temporaire `educapilote-course-progress` et ont été supprimés après le test.
- Vérification dans le navigateur sur le vrai site et la vraie session `eleve1` : 28 leçons annoncées, 28 barres accessibles, 28 cartes disponibles et aucun ancien doublon. Le rendu étroit a aussi été inspecté.

### Sauvegarde et reprise

- Sources avant cette évolution : `/stockage/training/backups/before-course-progress-20260911T132830Z`.
- Base chiffrée avant migration : `/stockage/training/backups/encrypted/educapilote-20260911T132830Z-2723354.sql.gz.age`.
- Les identifiants des anciennes images `web` et `assessment-service` sont enregistrés dans la sauvegarde de sources.

Pour redéployer les fichiers actuels après une modification vérifiée :

```bash
cd /stockage/training
docker compose -f docker-compose.dev.yml build migrate assessment-service web
docker compose -f docker-compose.dev.yml run --rm migrate alembic upgrade head
docker compose -f docker-compose.dev.yml up -d --no-deps assessment-service web
docker compose -f docker-compose.dev.yml ps assessment-service web
```

Ne pas utiliser `--remove-orphans` sur le projet actif : la supervision, Ollama et n8n sont attachés au même nom de projet avec d’autres fichiers Compose. Avant une nouvelle migration ou un remplacement de service, créer une nouvelle sauvegarde chiffrée. Pour une recette PostgreSQL, employer un nom de projet Docker distinct et une base dont le nom commence par `edu_module2_test_`; les fixtures refusent volontairement la base active.

### Limite fonctionnelle actuelle

Le tableau détaillé par cours et le bilan adaptatif sont raccordés aux 28 ateliers de **français CM2**. Les mathématiques, les sciences et l’histoire conservent leurs parcours existants mais n’utilisent pas encore ce nouveau contrat `course-progress`. Une extension à ces matières doit conserver leurs règles pédagogiques propres et ajouter des tests isolés avant le déploiement.

*Historique : les mathématiques ont été raccordées le 11 septembre 2026 en fin de journée ; voir la section « Ateliers de mathématiques et espace parent » en fin de document, qui décrit l’état courant.*

## Ateliers de mathématiques et espace parent (11 septembre 2026, soir)

Cette section décrit l’état courant et prévaut sur les constats plus anciens de ce document.

### Contenu mathématique publié

Les **32 ateliers de mathématiques CM2** et leurs **96 exercices** (test déterministe de trois exercices par leçon) sont publiés à la demande explicite du propriétaire, au moyen de `scripts/stage_math_ateliers.py` puis `scripts/publish_math_owner.py`. Comme pour le français, la publication est enregistrée comme décision opérateur (`operator.owner_publication`) et ne prétend à aucune relecture humaine. Les 21 anciennes versions squelettiques de mathématiques sont passées `archived` ; chaque leçon conserve exactement une version approuvée (contrainte `uq_lesson_one_approved`), la date de publication étant posée par le trigger `edu_guard_lesson_version`.

Le contenu provient de `shared/exercises/cm2_pack.py` (22 cours) et de `shared/exercises/math_extension.py` (10 cours) : découverte, explication, méthode, exemple travaillé, erreurs fréquentes, indices, puis trois tâches évaluables automatiquement (nombre, choix, rangement) via le moteur de calcul rationnel exact. La source officielle enregistrée est le PDF `programme-de-math-matiques-pour-le-cycle-3-439827.pdf` (empreinte SHA-256 journalisée par le staging). Les 32 compétences `CM2-MATH-*` du programme `programme-2025-cm2-2026` sont couvertes.

### Suivi par cours étendu aux mathématiques

`GET /students/{student_id}/course-progress` accepte désormais `subject=mathematiques` (motifs de leçons `cm2-math-%`) en plus de `subject=francais`. La correction explicite autorise le contexte `("mathematiques","CM2")` dans `services/assessment-service/app/routes.py`. La page élève affiche **Ma route dans les cours** pour les mathématiques avec une barre par cours (`apps/web/src/components/math-library.tsx`), les mêmes statuts `non_commencé`/`en_cours`/`passed`/`à_revoir`, la note sur 20 (seuil 14) et le cours adapté en cas d’échec. Les portes de fin de parcours acceptent français et mathématiques.

### Espace parent activé avec un compte de démonstration

Le compte `parent.demo` (rôle parent) est lié à l’élève `eleve1` (« Lina ») par un lien parental vérifié : `Guardian.verified_at` et `GuardianStudent.authority_verified_at` horodatés, preuve chiffrée via `IdentityCipher`, journal opérateur `operator.parent_demo_created` (script `scripts/create_parent_demo.py`, exécuté avec le compte `edu_user`). La connexion redirige vers `/parent`, qui présente le suivi par cours de l’enfant via la même API `course-progress` ; l’accès exige un lien parental vérifié non révoqué (`accessible_student` + `student_query`). Le mot de passe a été transmis au propriétaire hors de tout fichier ; il peut être renouvelé par la procédure normale sans toucher au lien.

À la demande du propriétaire, les mots de passe de `eleve1` et `admin` ont été réinitialisés par opérateur (script `scripts/reset_account_password.py`, journal `operator.access_reset`, `auth_version` incrémentée) avec des mots de passe mémorisables de 12 et 15 caractères ; la plateforme refuse toute longueur inférieure à 12. Aucun mot de passe n’est consigné ici.

### Validation exécutée

- Base éphémère `edu_module2_test_*` sur le VPS : **393 tests passés, 0 échec**, dont les trois nouveaux de `tests/test_math_installation.py` (staging idempotent 96→0, publication 32/96 sans `content_reviews` fabriquée, scénario complet `non_commencé → à_revoir 0/20 → cours adapté → passed 20/20`). La base éphémère est supprimée après exécution (piège `cleanup` du script).
- `tests/test_french_training.py` ajusté : tête de migration attendue `0018_course_progress_read` (l’assertion datait d’avant cette migration) et la correction explicite mathématiques CM2 est désormais autorisée par le jeu de paramètres.
- Frontend sur le VPS : `npm run typecheck`, `npm test` (17 tests) et `npm run build` réussis.
- Vérification live sur `https://boostclasse.com` avec le compte parent : santé OK, 32 cours de maths (3 exercices chacun, `non_commencé`, note nulle) et 28 cours de français suivis, contenu de leçon et exercice publiés lisibles sans fuite de corrigé (`answer_spec`/`candidate` absents), page `/parent` accessible.

### Sauvegarde et reprise

- Base chiffrée avant l’intervention : `/stockage/training/backups/encrypted/educapilote-20260911T161043Z-3623174.sql.gz.age`.
- Sources avant modification : `/stockage/training/backups/before-math-ateliers-20260911T152021Z/` (`routes.py`, `student.tsx`, `math-library.tsx` originaux).
- Seuls `assessment-service` et `web` ont été reconstruits et remplacés ; la migration active reste `0018_course_progress_read` (aucune nouvelle migration).
- Les scripts opérateur de staging/publication s’exécutent dans le conteneur `migrate` avec `PYTHONPATH=/app`, le secret `postgres_password` et le PDF source montés en lecture seule ; aucun mot de passe ne figure en argument ni dans un journal.

### Limite fonctionnelle actuelle

Le suivi par cours et le bilan adaptatif couvrent désormais le **français** et les **mathématiques** CM2. Les **sciences** et l’**histoire** conservent leurs parcours existants sans ce contrat ; une extension doit respecter leurs règles pédagogiques propres et s’accompagner de tests isolés. L’ajout de **langues vivantes** (demande du propriétaire) n’est pas commencé : prévoir des compétences, un programme et un pipeline dédiés avant tout contenu. L’intégration de dépôts GitHub tiers recommandée lors de l’audit fonctionnel (ClassQuiz, quizli, Interactive-Quiz-Maker pour les sources de quiz ; déjà pris en charge côté imports) reste à la discrétion du propriétaire pour les prochains contenus.

## Redirection HTTPS obligatoire et photo de connexion (11 septembre 2026, soir — correctif « Origine interdite. »)

### Symptôme et cause

Le propriétaire ne pouvait pas se connecter depuis son navigateur : soumission du formulaire → « Une étape à reprendre / Origine interdite. ». Le site est servi par un tunnel Cloudflare (`cloudflared` → proxy interne `127.0.0.1:18088` → `web:3000`) et Cloudflare ne redirigeait pas les visites `http://` vers `https://` : un visiteur qui tape le domaine sans schéma restait en HTTP, envoyait `Origin: http://boostclasse.com` et était refusé par la liste d’origines HTTPS (`WEB_ORIGINS`). Le proxy interne écrase par ailleurs `X-Forwarded-Proto` avec son propre schéma http, donc cet en-tête ne distingue pas les visiteurs https des visiteurs http.

### Correctif appliqué

- `apps/web/src/proxy.ts` : pour les hôtes `boostclasse.com` et `www.boostclasse.com`, redirection **308** vers `https://` lorsque l’en-tête `CF-Visitor` (posé par l’edge Cloudflare, seul témoin fiable du schéma réel du visiteur) n’indique pas https, plus en-tête `Strict-Transport-Security: max-age=31536000` sur les réponses de production pour que le navigateur passe en https de lui-même ensuite. Les accès locaux de recette (`localhost:18088`, `127.0.0.1:18088`) et par IP restent en http, inchangés.
- Photo fournie par le propriétaire ajoutée sur la page de connexion : `apps/web/public/login-eleve.png` (redimensionnée à 836×470, ~505 Ko), cadre blanc arrondi et légère rotation dans le panneau « histoire » (classe `.login-photo`, masquée sur mobile comme le reste du panneau). Le `Dockerfile` web copie désormais `public/` dans l’image standalone.

### Validation exécutée

- `npm run typecheck` et `npx vitest run` (17 tests) sur `apps/web` du VPS : réussis.
- `curl` : `http://boostclasse.com/connexion` et `http://www.boostclasse.com/connexion` → 308 vers https ; POST `http://…/api/session` → 308 ; `https://…/connexion` → 200 avec en-tête HSTS ; `https://boostclasse.com/login-eleve.png` → 200 `image/png` ; connexion `eleve1` en https → `{"ok":true,"redirect":"/eleve"}` ; `http://127.0.0.1:18088/connexion` → 200 (recette intacte).
- Navigateur réel : saisie de `http://boostclasse.com/connexion` → atterrissage sur `https://boostclasse.com/connexion` ; appel de connexion depuis la page → 200 `/eleve`, l’espace élève de Lina s’affiche avec la route par cours ; connexion `admin` → `/administration` qui rend « Les cours de ton site » ; sessions fermées ensuite.
- Sauvegarde chiffrée avant remplacement du service web : `backups/encrypted/educapilote-20260911T164604Z-3812841.sql.gz.age`. Seul `web` a été reconstruit et remplacé (aucune migration, aucun autre service touché).

## Tableau de progression masquable (11 septembre 2026, soir)

À la demande du propriétaire, « Ma route dans les cours » (français et mathématiques, page élève) peut désormais être affiché ou masqué d’un clic : bouton `Masquer le tableau` / `Afficher le tableau` à côté du compteur de cours réussis (`aria-expanded`/`aria-controls`, focus visible). Le choix est mémorisé par navigateur dans `localStorage` (clé `edu-progress-board`, partagée par les deux matières ; lecture au montage, donc sans écart d’hydratation) et reste appliqué après rechargement. Implémentation dans `apps/web/src/components/french-library.tsx` et `math-library.tsx`, styles `.progress-board-tools`/`.board-toggle` dans `french-workshop.css`. Validé : typecheck, 17 tests unitaires et `next build` verts ; navigateur réel — masquage/affichage et persistance vérifiés sur les 28 cours de français et les 32 cours de mathématiques. Sauvegarde avant remplacement : `educapilote-20260911T170633Z-3921123.sql.gz.age` ; seul `web` a été reconstruit.

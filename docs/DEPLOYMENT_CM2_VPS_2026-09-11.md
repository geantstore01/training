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

## Fluence calculatoire et enrichissement du français (11 septembre 2026, nuit)

Cette section décrit l’état courant et prévaut sur les constats plus anciens de ce document. Les contenus rédigés suivent la charte pédagogique fournie par le propriétaire : méthode par indices, vocabulaire précis du programme cycle 3 CM2, ton encourageant sans classement.

### Module « Fluence calculatoire » (mathématiques)

La bibliothèque de mathématiques comporte une section **Fluence calculatoire** inspirée de `fluence.mathalea.fr` : composant `FluenceLab` dans `apps/web/src/components/math-library.tsx` (placé sous le tableau de progression), styles `.fluence-*` dans `math-workshop.css`.

- Neuf séries générées côté client, sans serveur : tables de multiplication, multiplications à trou, compléments à 100, compléments à 1000, doubles et moitiés, additions mentales, soustractions mentales, multiplier par 10 et 100, tables de division.
- Chaque série dure 60 secondes : question affichée en grand, saisie validée au clavier, correction immédiate bienveillante (bonne réponse comptée ; mauvaise réponse corrigée sur le ton « La réponse était 12. Continue ! »), puis question suivante. Bilan de fin avec score, précision et record mémorisé par navigateur (`localStorage`, clé `edu-fluence-best`).
- Liens sortants vers les ressources publiques de la coopérative : `https://fluence.mathalea.fr/` et `https://www.coopmaths.fr/mathalea.html`. Le dépôt MathAléa est sous licence **AGPL-3.0** : aucun code ni contenu n’en a été incorporé. Le module est une réalisation originale et les liens renvoient vers le service public ; une intégration directe du code exigerait d’ouvrir l’ensemble du code du site sous la même licence, ce qui n’a pas été décidé.

### Enrichissement des 28 ateliers de français (version 2)

La première version des leçons de français était volontairement légère (méthode générique identique pour les 28 leçons, une seule erreur fréquente par leçon). Chaque leçon dispose désormais d’une version 2 enrichie, avec les trois exercices de test inchangés :

- `shared/exercises/french_deepening.py` : pour chaque code `CM2-FR-*`, prérequis (2 à 3), découverte en deux paragraphes, explication en trois paragraphes, **méthode spécifique à la leçon** (4 à 5 étapes), exemple résolu en trois items raisonnés et **trois erreurs fréquentes propres à la leçon**.
- `scripts/stage_french_deepening.py` : crée une version 2 `pending_review` par leçon (idempotent, journal `operator.french_lesson_staged`, ne publie jamais). `scripts/publish_french_deepening.py` : archive la version 1 approuvée puis approuve la version 2 (journal `operator.owner_publication` ; décision opérateur à la demande explicite du propriétaire, aucune relecture humaine fabriquée). Contrainte `uq_lesson_one_approved` respectée, `published_at` posé uniquement par le trigger `edu_guard_lesson_version`.
- `apps/web/src/components/lesson-reader.tsx` : les champs découverte et explication composés de plusieurs paragraphes (séparés par des retours à la ligne) sont rendus en paragraphes distincts.
- État en production : **28 leçons approuvées en version 2, 28 versions 1 archivées**. La requête de staging filtre les compétences sur `programme_version='programme-2025-cm2-2026'` car les tables contiennent aussi l’ancien programme `programme-cycle-3-reference-2020` avec des codes dupliqués.

### Validation exécutée

- Base éphémère `edu_module2_test_*` sur le VPS : **396 tests passés, 0 échec** (393 précédents + 3 de `tests/test_french_deepening.py` : couverture et enrichissement des 28 leçons, staging idempotent sans publication, publication v2 avec archivage v1 et service de la version enrichie sans fuite de `answer_spec`/`candidate`). Base éphémère supprimée après exécution.
- Frontend sur le VPS : `npm run typecheck`, `npx vitest run` (17 tests) et `npm run build` réussis.
- Vérification navigateur réelle sur `https://boostclasse.com` avec `eleve1` : section Fluence rendue (9 séries, liens externes), une série lancée — bonne réponse validée (« Juste ! 1 calcul réussi. »), mauvaise réponse corrigée avec le résultat attendu, chronomètre décomptant ; leçon « Distinguer classe et fonction » — les six pages enrichies (prérequis, découverte, explication en paragraphes, méthode en 5 étapes, exemple résolu, erreurs fréquentes) s’affichent ; session fermée ensuite.

### Sauvegarde et reprise

- Base chiffrée avant staging/publication : `/stockage/training/backups/encrypted/educapilote-20260911T191423Z-536486.sql.gz.age`.
- Seul `web` a été reconstruit et remplacé ; aucune nouvelle migration (tête toujours `0018_course_progress_read`).
- Les scripts de staging/publication s’exécutent dans le conteneur `migrate` avec `PYTHONPATH=/app` et un override temporaire ajoutant le secret `postgres_password` (`/tmp/ovr-migrate.yml`, supprimé après usage) ; aucun mot de passe en argument ni dans un journal.

## Le génie de la lampe remplace la boussole du Capitaine Savoir (11 septembre 2026, nuit)

À la demande du propriétaire, l’icône boussole de l’en-tête du panneau **Capitaine Savoir** (tuteur des étapes « Avec un coup de pouce » et « En autonomie ») est remplacée par un petit génie de lampe façon Aladdin, animé, qui invite l’élève à poser ses questions.

- `apps/web/src/components/tutor.tsx` : l’icône `Compass` (lucide-react) est retirée au profit d’un composant `GenieLamp` — SVG inline original de 64×64 (aucune dépendance ajoutée) : génie bleu-vert avec deux yeux, un sourire et un bandeau doré, sortant d’une lampe dorée (bec, anse, couvercle), volutes de fumée et étincelles dorées. `aria-label` « Petit génie sorti de sa lampe, prêt à aider », `focusable="false"`.
- Sous le badge, une **bulle de dialogue animée** porte le message : « Une difficulté ? Questionne-moi ! » (pointe vers le badge, texte sur deux lignes).
- Animations CSS dans `apps/web/src/app/globals.css` (`.captain-wrap`, `.captain-genie`, `genie-float`, `genie-rise`, `genie-twinkle`, `genie-bounce`) : flottement du génie, montée des volutes, scintillement des étincelles, rebond léger de la bulle ; toutes désactivées sous `prefers-reduced-motion: reduce`, conformément au motif déjà utilisé par les ateliers. Aucun autre élément du panneau (titre, messages, champ, boutons d’envoi et d’aide supplémentaire, lecture orale espeak) n’a changé.

### Validation exécutée

- Frontend sur le VPS : `npm run typecheck`, `npx vitest run` (17 tests) et `npm run build` réussis.
- Navigateur réel sur `https://boostclasse.com` avec `eleve1`, parcours jusqu’à « Étape 4 · Avec un coup de pouce » : génie rendu, bulle « Une difficulté ? Questionne-moi ! » présente, animations actives (`genie-float`, `genie-rise`, `genie-bounce` confirmées par `getComputedStyle`), dessin vérifié visuellement en zoom (visage, yeux, sourire, bandeau, lampe, volutes, étincelles ; rien ne déborde du badge) ; session fermée ensuite.

### Sauvegarde et reprise

- Base chiffrée avant remplacement du service web : `/stockage/training/backups/encrypted/educapilote-20260911T195208Z-752739.sql.gz.age`.
- Seul `web` a été reconstruit et remplacé (`build web` puis `up -d --no-deps web`, santé `{"status":"ok"}`) ; aucune migration, aucun autre service touché.

## Le génie présent dès l’explication et « À toi d’essayer » (11 septembre 2026, nuit)

À la demande du propriétaire, le Capitaine Savoir (génie de la lampe) n’attend plus l’étape « Avec un coup de pouce » : il accompagne l’élève dès la lecture de l’explication et pendant le premier essai, pour poser des questions librement (« je ne comprends pas, simplifie-moi l’explication »).

- `apps/web/src/lib/journey.ts` : nouvelle action `prime` du reducer, qui enregistre exercice/tentative/session sans changer d’étape ni effacer les réponses.
- `apps/web/src/components/student.tsx` : à l’ouverture d’un parcours, la session et la tentative de la mini-question sont créées immédiatement avec la même clé d’idempotence que « Je fais un premier essai » (`2:0:<exercise>:0`) — la tentative est donc réutilisée telle quelle au moment du test, sans doublon ni donnée factice. Le panneau du Capitaine (classe `with-tutor`) et le composant `Tutor` sont affichés aux étapes **Explication, À toi d’essayer et Avec un coup de pouce** (stages 1 à 3) ; la Découverte et l’autonomie restent sans panneau, et l’aide automatique après échec reste limitée à « Avec un coup de pouce ». Le bouton « Revenir à mon carnet » ne demande confirmation que si des réponses non envoyées existent (la tentative anticipée ne déclenche plus d’alerte inutile).
- `apps/web/src/components/tutor.tsx` : le bouton d’envoi devient « Poser ma question » (le questionnement libre n’est pas seulement une demande d’indice) ; « Un peu plus d’aide » conserve la progression d’indices.
- `services/tutor-service/app/routes.py` : quand l’aide est refusée parce que les accords de confidentialité ne sont pas réunis, la réponse pédagogique dit désormais précisément ce qu’il faut faire (« l’aide “Aide IA locale” doit être autorisée par ton représentant puis activée dans “Mes choix de confidentialité” ») au lieu du message générique « Faisons une pause… » ; idem pour la suspension par l’enseignant. Les autres réponses (protection, indisponibilité) sont inchangées.

### Point important : la réponse du génie exige les accords parent + élève

La modération locale refuse de transmettre toute question tant que l’option **Aide IA locale** n’est pas autorisée (`consent_allowed` : accord du représentant lié vérifié **et** assentiment de l’élève, version de politique courante). Au moment du déploiement, `eleve1` a donné son assentiment mais aucun accord parental n’est enregistré ; le génie répond donc par le message explicite ci-dessus. Pour activer réellement les réponses : se connecter sur le compte parent (`parent.demo`), autoriser « Aide IA locale » dans la confidentialité de l’enfant, puis l’élève confirme dans « Mes choix de confidentialité ». Aucun consentement n’a été fabriqué en base lors de cette intervention.

### Validation exécutée

- Frontend sur le VPS : `npm run typecheck`, `npx vitest run` (17 tests) et `npm run build` réussis ; syntaxe Python du tutor-service vérifiée.
- Navigateur réel avec `eleve1` (leçon « Accorder dans le groupe nominal ») : génie absent à « Découverte », présent à « Explication » (bulle et animation confirmées), présent à « À toi d’essayer » — la tentative anticipée est réutilisée sans erreur et la soumission « Réponse juste » fonctionne —, présent à « Avec un coup de pouce ». Une question posée depuis la page d’explication déclenche bien le message d’activation des accords (avant : message générique). Session fermée ensuite.

### Sauvegarde et reprise

- Base chiffrée avant remplacement de `web` : `/stockage/training/backups/encrypted/educapilote-20260911T201247Z-860997.sql.gz.age`.
- Base chiffrée avant remplacement de `tutor-service` : `/stockage/training/backups/encrypted/educapilote-20260911T202032Z-904526.sql.gz.age`.
- Services remplacés : `web` et `tutor-service` uniquement (aucune migration ; tête toujours `0018_course_progress_read`).

## Avatar du propriétaire pour le Capitaine Savoir (11 septembre 2026, soir)

À la demande du propriétaire (« remplace l'emoji par cet avatar en plus grand »), le dessin vectoriel du génie a été remplacé dans le panneau « Capitaine Savoir » par l'avatar fourni (`1789158484.png`, personnage façon Aladdin généré par IA, 1664×928 avec filigrane « Qwen » en bas à droite).

- Traitement local (Pillow) : recadrage carré centré sur le personnage — le recadrage élimine le filigrane — puis réduction à 320×320 PNG optimisé (~155 Ko). Fichier déposé dans `apps/web/public/captain-avatar.png` (même mécanique que `login-eleve.png` ; le `Dockerfile` web copie `public/` dans l'image standalone).
- `apps/web/src/components/tutor.tsx` : le composant `GenieLamp` (SVG) est retiré et remplacé par `CaptainAvatar` — `<img src="/captain-avatar.png" alt="Capitaine Savoir, ton capitaine guide" width={96} height={96}>` — dans l'en-tête du panneau ; la bulle « Une difficulté ? Questionne-moi ! » est conservée.
- `apps/web/src/app/globals.css` : le bloc « génie » est remplacé par `.captain.captain-avatar` (médaillon rond 96 px — 84 px sous 1050 px — fond dégradé or, ombre douce) et l'image ronde en `object-fit:cover` avec une flotte douce `captain-float` (translation verticale, sans rotation, adaptée à une photo) ; `prefers-reduced-motion` coupe l'animation comme avant.
- Taille : le badge SVG précédent mesurait 48 px (dessin 34 px) ; l'avatar occupe désormais 96 px de diamètre, soit le double.

### Validation exécutée

- `npm run typecheck`, `npx vitest run` (17 tests) et `npm run build` sur `apps/web` du VPS : réussis.
- `curl https://boostclasse.com/captain-avatar.png` → 200 `image/png`, 158 027 octets (fichier exact).
- Navigateur réel avec `eleve1` : leçon « Accorder dans le groupe nominal » → « Voir mon cours » (Explication) : le médaillon avatar s'affiche en grand avec la bulle, sans chevauchement ni débordement ; « Je fais un premier essai » (À toi d'essayer) : l'avatar y est également présent. Session fermée ensuite.

### Sauvegarde et reprise

- Base chiffrée avant remplacement de `web` : `/stockage/training/backups/encrypted/educapilote-20260911T203541Z-983875.sql.gz.age`.
- Seul `web` a été reconstruit et remplacé (aucune migration, aucun autre service touché).

### Remplacement par l'avatar Einstein (même soir)

À la demande du propriétaire (« je prefere einstein »), l'avatar Aladdin ci-dessus a été remplacé par celui d'Einstein (`1789159314.png`, 1664×928, même filigrane « Qwen » en bas à droite).

- Même traitement local (Pillow) : recadrage carré 928×928 centré sur le personnage (le recadrage exclut le filigrane), réduction LANCZOS à 320×320 PNG optimisé (195 514 octets), déposé sous le **même nom** `apps/web/public/captain-avatar.png`. Aucun changement de code ni de CSS (même fichier, même `alt`, même médaillon rond 96 px à dégradé or) : seule l'image change.
- Changement d'image seul (aucun TS/CSS modifié) : typecheck/vitest/build locaux non relancés — le build Docker de `web` exécute `next build` en interne, ce qui valide la compilation.
- Sauvegarde chiffrée avant remplacement : `backups/encrypted/educapilote-20260911T204336Z-1025511.sql.gz.age` ; seul `web` a été reconstruit et remplacé (aucune migration, aucun autre service touché).
- Validation : `curl https://boostclasse.com/captain-avatar.png` → 200 `image/png`, 195 514 octets (fichier exact) ; navigateur réel avec `eleve1`, leçon « Accorder dans le groupe nominal » → « Voir mon cours » (Explication) : Einstein rendu dans le médaillon or avec la bulle « Une difficulté ? Questionne-moi ! », image entière sans rognure ni débordement. Session fermée ensuite.

## Allègement des pages ateliers : suppression du bloc de présentation (11 septembre 2026, soir)

À la demande du propriétaire (« c'est trop chargé pour un élève de CM2, supprime tout ce bloc »), la grande carte de présentation qui occupait tout le haut des bibliothèques de français **et** de mathématiques est supprimée : les deux pages commencent désormais directement par « Ma route dans les cours », puis les domaines et les leçons.

- `apps/web/src/components/french-library.tsx` : suppression de la section `.atelier-intro` (titre « Les mots, ça se comprend en jouant. », texte de présentation, « 28 leçons à explorer » et le panneau de démonstration incliné « Une phrase à ouvrir » avec ses morceaux cliquables) ; nettoyage de l'état local et des icônes devenus inutiles (`ArrowUpRight`, `Check`).
- `apps/web/src/components/math-library.tsx` : suppression de la section équivalente (« Les maths prennent forme. », « 32 leçons à explorer » et le panneau de manipulation `MathLab` — fractions coloriées / rectangle aire-périmètre) ; le composant partagé `MathDiagram` reste utilisé par les exercices et n'est pas touché.
- `apps/web/src/components/french-workshop.css` et `math-workshop.css` : retrait des règles devenues mortes (`.atelier-intro`, `.atelier-story`, `.atelier-facts`, `.sentence-lab`, `.piece*`, `.number-lab`, `.math-lab-tabs`, `.fraction-buttons`, `.rectangle-*`, `.math-observation`…) ; les styles partagés restent intacts (tableau de progression, domaines, catalogue, `.math-diagram`/`.math-grid`/`.math-band` utilisés par les exercices).
- Aucun changement fonctionnel : tableau de progression masquable, fluence calculatoire, domaines, recherche et cartes de leçons sont inchangés.

### Validation exécutée

- Frontend sur le VPS : `npm run typecheck`, `npx vitest run` (17 tests) et `npm run build` réussis.
- Navigateur réel avec `eleve1` : page français — `.atelier-intro` absent du DOM, aucun texte du bloc (« comprend en jouant », « Une phrase à ouvrir ») ; « Ma route dans les cours » est le premier bloc, six domaines et « 28 leçons disponibles » intacts ; page mathématiques — idem (« prennent forme » et « Manipulation libre » absents, « 32 leçons disponibles », fluence rendue). Session fermée ensuite.

### Sauvegarde et reprise

- Sources avant modification : `/stockage/training/backups/before-atelier-intro-20260911T212000Z/components/` (`french-library.tsx`, `math-library.tsx`, `french-workshop.css`, `math-workshop.css` originaux).
- Base chiffrée avant remplacement du service web : `/stockage/training/backups/encrypted/educapilote-20260911T210229Z-1125000.sql.gz.age`.
- Seul `web` a été reconstruit et remplacé (aucune migration ; tête toujours `0018_course_progress_read`).

## Suppression du bandeau « Ma route dans les cours » et de l'en-tête du carnet élève (11 septembre 2026, soir)

À la demande explicite du propriétaire (deux captures désignant les blocs restants), deux parties encore présentes dans l'espace élève sont supprimées. Cette section prévaut sur la section « Tableau de progression masquable » : le bouton Masquer/Afficher et la clé `localStorage` `edu-progress-board` n'existent plus.

1. **Bandeau marine « Ma route dans les cours »** (français **et** mathématiques) : les composants `CourseProgressBoard` et `MathProgressBoard` sont retirés de `french-library.tsx` et `math-library.tsx` (avec les imports devenus inutiles `Trophy`, `Eye`, `EyeOff`, `useEffect`, `Loading`, `ErrorBox` — `statusLabel` reste utilisée par les cartes de leçons). Le CSS mort est retiré de `french-workshop.css` (`.course-progress-board`, `.progress-board-heading`, `.progress-score`, `.progress-board-tools`, `.board-toggle`, `.progress-summary`, `.course-bars`, `.course-bar*` et leurs fragments 650 px) ; `.lesson-progress`, `.course-result` et `.adaptive-course` sont conservés (utilisés par les cartes de leçons et le panneau de fin de cours).
2. **En-tête de la page élève « Mon carnet d'exploration / Bonjour, … ! »** avec son bouton : supprimé de `student.tsx` (bloc `.title-with-action` avec `PageTitle`, présent sur l'accueil et pendant un parcours). L'accueil commence désormais directement par « 1. Choisis une matière » puis la bibliothèque. Les règles CSS mortes `.french-home .page-title*` et `.french-home>.title-with-action*` sont retirées (`.title-with-action` reste utilisé par les espaces parent et enseignant).

**Point fonctionnel conservé** : le bouton supprimé était le seul accès de l'élève à « Mes choix de confidentialité » (assentiment élève nécessaire pour activer « Aide IA locale », cf. section du génie). Un **lien texte discret** « Mes choix de confidentialité » est donc posé tout en bas de la page élève (classe `.privacy-entry`) ; il ouvre le même panneau enfant, avec un lien « Revenir à mon carnet » pour revenir.

La progression de l'élève reste visible ailleurs : statut sur chaque carte de leçon (PASSED · n/20, barre de %), panneau de résultat en fin de test (`CourseResult`), et espace parent inchangé.

### Validation exécutée

- Frontend sur le VPS : `npm run typecheck`, `npx vitest run` (17 tests) et `npm run build` réussis.
- Navigateur réel avec `eleve1` : accueil — aucun « Bonjour », aucun « carnet d'exploration », aucun « Ma route dans les cours »/« tableau de progression » dans le DOM ; « 1. Choisis une matière » puis les domaines de français rendus. Page mathématiques — bandeau absent, « Fluence calculatoire », « Six façons de raisonner » et les leçons intactes. Lien discret « Mes choix de confidentialité » → panneau enfant (« Tu peux choisir tes aides ») ouvert, « Revenir à mon carnet » → accueil restauré. Session fermée ensuite.

### Sauvegarde et reprise

- Sources avant modification : `/stockage/training/backups/before-student-blocks-20260911T211428Z/` (`components/` : `student.tsx`, `french-library.tsx`, `math-library.tsx`, `french-workshop.css` + `globals.css`).
- Base chiffrée avant remplacement du service web : `/stockage/training/backups/encrypted/educapilote-20260911T211738Z-1204957.sql.gz.age`.
- Seul `web` a été reconstruit et remplacé (aucune migration ; tête toujours `0018_course_progress_read`).

## Espace sous la barre de lecture + retour accueil « Mes missions » (11 septembre 2026, soir)

À la demande du propriétaire (capture désignant un grand vide sous la barre de lecture de l'accueil élève, et souhait que « Mes missions » ramène à l'accueil et non à la page de connexion).

1. **Espace vide supprimé** : sur l'accueil élève (français/mathématiques/histoire/sciences), l'espace de 61 px entre la barre de lecture et la première section est réduit à 12 px. Dans `french-workshop.css` : `.main-content>.french-home{margin-top:-15px}` (et `-30px` au-delà de 1500 px pour compenser le padding du `main-content`), `.french-home>.choice-section{margin-top:18px}` ; le bloc `.privacy-entry` passe de `margin:34px 0 0` à `margin:34px 0 0;text-align:center`.
2. **« Mes missions » / logo → accueil, partout** : dans `shell.tsx`, le lien de marque et les liens de navigation détectent quand on est déjà dans la zone cible et émettent alors un événement DOM dédié `edu:go-home` (au lieu d'un simple lien qui ne faisait rien en navigation douce). Dans `student.tsx`, un écouteur sur `edu:go-home` réinitialise l'état local (parcours en cours fermé, réglages/panneau confidentialité fermés, rafraîchissement de la progression) et remonte en haut de page. Résultat : depuis une leçon, un test, ou la vue « Mes choix de confidentialité », cliquer « Mes missions » ou le logo ramène à l'accueil élève sans déconnexion. « Quitter » déconnecte toujours vers `/connexion`.

### Validation exécutée

- Frontend sur le VPS : `npm run typecheck`, `npx vitest run` (17 tests) et `npm run build` réussis.
- Navigateur réel avec `eleve1` : écart barre de lecture → première carte mesuré à 12 px ; depuis la vue « Mes choix de confidentialité », « Mes missions » ramène à l'accueil (titres « 1. Choisis une matière », « Six façons de progresser », « Ton carnet de découvertes » présents) ; « Quitter » ramène bien à `/connexion`.

### Sauvegarde et reprise

- Sources avant modification : `/stockage/training/backups/before-missions-home-20260911T213552Z/` (`components/` : `shell.tsx`, `student.tsx`, `french-workshop.css`).
- Base chiffrée avant remplacement du service web : `/stockage/training/backups/encrypted/educapilote-20260911T213723Z-1310738.sql.gz.age`.
- Seul `web` a été reconstruit et remplacé (aucune migration ; tête toujours `0018_course_progress_read`).

## Page d'accueil publique « façon kresco.ma » avec la mascotte de l'élève (11 septembre 2026, nuit)

À la demande du propriétaire : une page d'accueil construite sur le modèle visuel de `https://kresco.ma/` (structure, palette, rythme des sections), avec son avatar (garçon voxel 3D aux lunettes tenant un livre « Learning », source `1789162391.png`) à la place du renard « Kres ». Les textes et contenus sont originaux BoostClasse (charte pédagogique : indices plutôt que réponses, vocabulaire CM2, pas de classement) — aucune copie de texte ni d'image du site de référence.

1. **Nouveaux fichiers** : `apps/web/src/components/landing.tsx` (composant client) et `apps/web/src/components/landing.css` (styles préfixés `bc-`, aucune collision avec l'espace connecté). Assets : `public/landing-mascot.png` (recadrage carré 560×560 de l'avatar fourni) et `public/landing-mascot-sm.png` (300×300, barre de navigation, bandeau final, pied de page).
2. **Structure reprise de kresco.ma** : barre de navigation fixe translucide (flou 12 px, ombre au défilement) avec marque + ancres + « Se connecter » + CTA ; héros dégradé indigo pleine largeur (titre Nunito 900 très serré « Comprends. / Entraîne-toi. / Réussis. », badge pilule, double CTA, carte mascotte inclinée avec pastilles flottantes animées) ; bandeau de 4 compteurs animés au passage (IntersectionObserver) ; parcours en 8 étapes (leçon → exemples guidés → exercices à indices → quiz → atelier d'écriture → lecture suivie → bilan → espace parent) ; 3 sections fonctionnelles alternées avec maquettes (tchat d'indices du capitaine Savoir, carte de leçon avec « À retenir » et barre de progression, tableau de bord parent) et chips ; section « rythme » en 4 étapes numérotées ; 3 cartes Élève/Parent/Enseignant (l'élève mise en avant) ; FAQ accordéon en 5 questions ; bandeau CTA final dégradé avec la mascotte ; pied de page 3 colonnes. Animations d'apparition (translation + flou, échelonnées 40-70 ms) désactivées sous `prefers-reduced-motion`.
3. **Palette et typographie inspirées de kresco** (tokens relevés sur le site de référence) : page `#f7f6f4`, cartes blanches, encre `#18181b`/`#52525c`, bordures `#e4e4e7`, primaire indigo `#453dee` (doux `#edf1ff`), accents jaune `#fbae17`, pervenche `#707fff`, bleu `#29aee4`, vert `#16a34a` ; boutons arrondis 12 px Nunito 800 ; courbe d'aisance `cubic-bezier(.22,1,.36,1)`. La police Nunito 900 est ajoutée dans `app/layout.tsx` (import `@fontsource/nunito/900.css`).
4. **Routage** (`app/page.tsx`) : un visiteur non connecté voit la page d'accueil publique (plus de redirection immédiate vers `/connexion`) ; un visiteur connecté est toujours redirigé vers son espace (`home(roles)`). Tous les CTA de la page mènent à `/connexion`, inchangée.

### Validation exécutée

- Frontend sur le VPS : `npm run typecheck`, `npx vitest run` (17 tests) et `npm run build` réussis.
- Navigateur réel : `https://boostclasse.com/` en visiteur — page d'accueil rendue (titre « Comprends. Entraîne-toi. Réussis. », 4 sections ancrées, 8 étapes, 5 FAQ, 11 liens vers `/connexion`), les 5 images (mascotte ×4 + capitaine) chargées, aucun débordement horizontal (`scrollWidth == clientWidth`). Connexion `eleve1` → `/eleve` ; retour sur `/` en session → redirection vers `/eleve` (la page d'accueil publique ne s'affiche plus pour un utilisateur connecté).

### Sauvegarde et reprise

- Sources avant modification : `/stockage/training/backups/before-landing-20260911T215514Z/apps-web/` (`src/app/page.tsx`, `src/app/layout.tsx` originaux + copie de `public/`). Les fichiers `landing.tsx`, `landing.css`, `landing-mascot*.png` sont nouveaux (absents de la production avant ce déploiement).
- Base chiffrée avant remplacement du service web : `/stockage/training/backups/encrypted/educapilote-20260911T215556Z-1408083.sql.gz.age`.
- Seul `web` a été reconstruit et remplacé (aucune migration ; tête toujours `0018_course_progress_read`).

## Page d'accueil v2 : reproduction intégrale de l'interface kresco.ma (11 septembre 2026, nuit — à la demande du propriétaire)

La première version « inspirée » ne suffisait pas : le propriétaire demande l'interface **identique** à kresco.ma. La structure exacte du site de référence a été extraite en navigateur (en-tête, 8 étapes de la vitrine, 6 sections fonctionnalités, CTA intermédiaire, rythme en 4 points, 4 cartes d'offres + tableau comparatif + simulateur, FAQ, bande question, CTA final, pied de page) puis reproduite avec le contenu BoostClasse et l'avatar Minecraft fourni (garçon voxel au livre « Learning ») **partout où le renard Kres apparaît**.

`landing.tsx` et `landing.css` sont réécrits en entier ; nouvel asset `public/landing-mascot-head.png` (recadrage tête pour les avatars de tchat).

1. **Structure reproduite à l'identique** : barre fixe translucide (4 ancres + Se connecter + CTA « On y va ! ») ; rail promesse indigo arrondi (h1 deux phrases, badge, double CTA, compteur animé 0→3→9→27→81→∞ « façons de comprendre », mascotte avec bulle « On commence ? ») ; bande « ton guide » (mascotte + chips) ; vitrine produit interactive « Ta route vers la réussite. » — 8 étapes (Cours, Atelier, Guide, Quiz, Résumés, Exercices, Lecture, Bilan CM2) avec maquette produit par étape, sélection manuelle + avance automatique 5,2 s (pause au survol), points de progression ; 6 sections fonctionnalités alternées (texte + chips + maquette : leçon, formats, atelier, indices du guide, progression, bilan) ; CTA intermédiaire « Une idée ? Essaie-la tout de suite. » ; rythme en 4 points numérotés ; section offres : bandeau info, 4 cartes (Découverte/Élève mis en avant/Parent/Enseignant), tableau comparatif 8 lignes × 5 colonnes, simulateur « Construis ta route. » (accordéon numéroté 3 étapes : classe → matière → rythme, boutons « Choisir… », carte résultat avec CTA) ; FAQ accordéon 7 questions (dont « L'aide IA donne-t-elle les réponses ? ») ; bande question « Encore une petite question ? » avec mascotte ; CTA final « Prends une notion. Apprivoise-la. » (Explorer / Créer mon compte / Se connecter) ; pied de page.
2. **Maquettes produit façon kresco** : leçon de fractions (fraction visuelle 3/4, « À retenir »), atelier de mots (tuiles à glisser dont une en pointillés), tchat d'indices (avatar mascotte-tête, Indice 1/2/3), quiz QCM avec option sélectionnée, fiche express, exercice guidé en 3 étapes, lecteur avec surlignage, bilan 18/20, démo de raisonnement (barres 3/4 · 1/4 · 4/4 de 20), avant/après atelier, trail de progression à pastilles.
3. **Routage inchangé** : visiteur → page d'accueil ; connecté → redirection vers son espace (vérifié au déploiement précédent, `page.tsx` non modifié depuis).

### Validation exécutée

- Frontend sur le VPS : `npm run typecheck` (après correction `.matches()` et `clearTimeout`), `npx vitest run` (17 tests) et `npm run build` réussis.
- Navigateur réel en visiteur (session de test fermée) : h1, compteur à ∞, 4 ancres, 8 étapes de vitrine avec avance automatique (étape active passe à « Atelier ») et sélection manuelle (clic étape 8 → maquette « Bilan CM2 »), 6 fonctionnalités, rythme ×4, 4 cartes, tableau 8 lignes, FAQ 7 questions, simulateur complet CM2 → Français → Régulier → « Ta route est prête : CM2 · Français · Régulier · 4 missions / semaine », accordéon FAQ ouvre la réponse « L'aide IA donne-t-elle les réponses ? », 9 images chargées, aucun débordement horizontal.

### Sauvegarde et reprise

- Sources de la v1 avant réécriture : `/stockage/training/backups/before-landing2-20260911T220801Z/apps-web/src/components/` (`landing.tsx`, `landing.css` de la v1).
- Base chiffrée avant remplacement du service web : `/stockage/training/backups/encrypted/educapilote-20260911T221307Z-1499197.sql.gz.age`.
- Seul `web` a été reconstruit et remplacé (aucune migration ; tête toujours `0018_course_progress_read`).

## Bannières de module et accueil homogène des matières (12 septembre 2026)

À la demande du propriétaire (trois images fournies : laboratoire sciences, classe de mathématiques, classe de français, thème mascotte voxel), chaque matière ouvre désormais sur la même bannière structurée.

1. **Nouveaux fichiers** : `apps/web/src/components/subject-banner.tsx` (composant partagé `SubjectBanner`) et `subject-banner.css`. Assets : `apps/web/public/banner-francais.jpg`, `banner-mathematiques.jpg`, `banner-sciences.jpg` (fournies en 1664×928 avec filigrane « Qwen » en bas à droite ; recadrées pour l'éliminer → 1400×~700, JPEG progressif ~130-145 Ko chacune).
2. **Bannière identique pour les trois matières** : pastille kicker colorée par matière (palette existante `subject-*` de `globals.css`), titre, accroche et fil d'étapes numérotées ; image encadrée blanc avec légère rotation au repos (désactivée sous `prefers-reduced-motion`), empilement mobile avec image d'abord.
3. **Intégration** : `french-library.tsx` (bannière en tête, avant « Six façons de progresser »), `math-library.tsx` (en tête, avant la fluence), `science-library.tsx` — l'ancien hero marine « STATION SCIENCES » et son orbite SVG sont remplacés par la bannière commune (même traitement que les blocs de présentation français/maths supprimés précédemment sur demande). Le CSS mort associé (`.science-hero*`, `.science-orbital`, `.orbital-*`, `.science-status-dot`, fragments médias) est retiré de `science-workshop.css` ; `.science-kicker` et `.science-primary` restent (utilisés par les missions et le laboratoire). L'histoire conserve son hero existant (aucune image fournie ; ajout ultérieur en une ligne via `SubjectBanner`).
4. **Accès opérateur** : la clé SSH du poste actuel (`relbrahli@P146S032`, ed25519) a été autorisée dans `/root/.ssh/authorized_keys` par le propriétaire sur la console.

### Validation exécutée

- Frontend sur le VPS : `npm run typecheck` et `npx vitest run` (17 tests) réussis ; image `web` reconstruite (`next build` interne au build Docker) et service remplacé (`up -d --no-deps web`), état `healthy`, `/api/health` → `{status:ok}`.
- `https://boostclasse.com/banner-francais.jpg`, `banner-mathematiques.jpg`, `banner-sciences.jpg` → 200 `image/jpeg` avec tailles exactes (traversée Cloudflare vérifiée depuis le VPS) ; page `/connexion` → 200. Les chunks du bundle déployé référencent le composant et les trois images.
- Vérification visuelle navigateur avec session élève non refaite par l'opérateur (identifiants non détenus) : à confirmer par le propriétaire sur `https://boostclasse.com`.

### Sauvegarde et reprise

- Sources originales : `/stockage/training/backups/before-subject-banners-20260912T065700Z/` (4 fichiers remplacés).
- Base chiffrée avant remplacement : `/stockage/training/backups/encrypted/educapilote-20260912T065700Z-290500.sql.gz.age`.
- Seul `web` a été reconstruit et remplacé (aucune migration ; tête toujours `0018_course_progress_read`).


## Mascotte de marque dans la barre du haut (12 septembre 2026)

Mise en évidence de la mascotte (garçon voxel, thème Minecraft) dans la barre d'en-tête de l'espace connecté, sur le modèle de kresco.ma dont le renard Kres fait partie du logo de navigation. La mascotte apparaît désormais sur toutes les pages des espaces élève / parent / administration.

- `apps/web/public/masthead-mascot.jpg` — NOUVEAU : recadrage portrait 3:4 (180×240, JPEG progressif q88, ~14 Ko) réalisé depuis `landing-mascot.png` (560×560) pour remplir la carte sans vide latéral.
- `apps/web/src/components/shell.tsx` — la carte mascotte (`img.masthead-mascot`, alt décoratif) est intégrée dans le lien de marque du `masthead`, avant `<Brand/>` ; cliquable vers l'accueil de l'espace comme le reste de la marque.
- `apps/web/src/app/globals.css` — règles `.masthead-mascot` (hauteur 78 px, coins 16 px, bordure blanche 3 px, ombre, inclinaison −5°, redressement au survol, `prefers-reduced-motion` respecté) + variante mobile ≤760 px (52 px).

Validation avant remplacement : prévisualisation locale de la barre (bureau 1440 px et mobile 390 px) jugée conforme ; sauvegarde des sources dans `backups/before-masthead-mascot-20260912T071317Z/` ; sauvegarde chiffrée de la base `backups/encrypted/educapilote-20260912T071321Z-376810.sql.gz.age` ; `npm run typecheck` sans erreur ; `npx vitest run` 17/17.

Déploiement : `docker compose -f docker-compose.dev.yml build web` puis `up -d --no-deps web` (conteneur healthy). Vérifié : `/api/health` → `{"status":"ok"}` ; `/masthead-mascot.jpg` → 200 `image/jpeg` 13834 octets en local (127.0.0.1:18088) et via Cloudflare (https://boostclasse.com) ; référence de l'image présente dans le chunk JS `259wuj49ve7bl.js` et règle `.masthead-mascot` présente dans le chunk CSS `2_8krh1iuzhy2.css` du conteneur.

## 2026-09-12 (2) — Masthead Minecraft illustré, textes cliquables

- Barre du haut remplacée par la bannière pixel-art fournie par l'utilisateur : apps/web/public/masthead-banner.webp (2172×312, WebP q95, 138 Ko), affichée pleine largeur.
- Textes de l'image rendus cliquables via zones transparentes positionnées en pourcentages : marque → accueil (event edu:go-home), « Mes missions » → /eleve, « Quitter » → déconnexion. Liens autres espaces (parent/administration) en boutons HTML superposés (.masthead-extra).
- Barre compacte existante (mascotte + Brand + nav + Quitter) conservée comme repli mobile ≤760 px.
- Fichiers modifiés : apps/web/src/components/shell.tsx, apps/web/src/app/globals.css, apps/web/public/masthead-banner.webp.
- Sauvegardes préalables : backups/manual/2026-09-12-pre-masthead-minecraft/ (shell.tsx, globals.css, masthead-mascot.jpg) + backups/encrypted/educapilote-20260912T074225Z-528539.sql.gz.age.
- Validation : typecheck OK ; vitest 17/17 ; docker compose -f docker-compose.dev.yml build web puis up -d --no-deps web ; conteneur healthy ; /masthead-banner.webp 200 image/webp via 127.0.0.1:18088 et https://boostclasse.com ; chunks 1-jf65f47ddrg.js et 0il-aajr6_m05.css contiennent masthead-art / masthead-hotspot ; prévisualisations bureau 1440 px et mobile 390 px validées (hotspots testés au elementFromPoint).

## 2026-09-12 (3) — Bande « Mon espace personnel » supprimée, boutons alignés sur le titre + correctifs responsive

- La bande pleine largeur (reading-bar) est supprimée. « Mon espace personnel » (lien vers l'accueil de l'espace) et « Confort de lecture » (menu déroulant Texte agrandi / Lecture aérée) deviennent deux boutons compacts ancrés en haut à droite de la zone de contenu, au niveau du titre de page (page-tools) ; en dessous de 1050 px ils passent en flux au-dessus du contenu.
- Dégagements ciblés pour les pages commençant par un bloc large (héros élève, mission en cours, barre d'outils parent) afin qu'aucun chevauchement n'ait lieu.
- Responsive masthead : l'overlay des liens autres espaces (Espace parent / Les cours) ne tient que ≥1500 px ; entre 761 et 1499 px ces liens passent dans une fine ligne de navigation sous la bannière (masthead-art-nav) — corrige le chevauchement mesuré (−103 px à 844 px) avec le bouton « Mes missions » dessiné dans la bannière.
- Responsive grilles : subject-grid passe à 2 colonnes ≤1050 px (et typo réduite ≤760 px), topic-grid 2 colonnes ≤1050 px puis 1 colonne ≤760 px — corrige les libellés (« Mathématiques ») qui débordaient sur les tuiles voisines en mobile/tablette.
- Fichiers modifiés : apps/web/src/components/shell.tsx, apps/web/src/app/globals.css.
- Sauvegardes préalables : backups/manual/2026-09-12-pre-page-tools/ + backups/encrypted/educapilote-20260912T095613Z-1218019.sql.gz.age.
- Validation : typecheck OK ; vitest 17/17 ; build web + up -d --no-deps web ; conteneur healthy ; tunnel 18088 = 200 ; chunk CSS 1of94205nhypz.css contient page-tools, chunk JS 0cz23tmjp08qn.js contient masthead-art-nav ; prévisualisations validées visuellement à 1440, 1366, 980, 844 et 390 px (boutons alignés sur « 1. Choisis une matière », pas de chevauchement, tuiles 2 colonnes).

## 2026-09-12 (4) — Page de connexion : mascotte « carret » à la place de la photo élève

- `public/login-eleve.png` (836×470 PNG, 518 Ko, photo élève) remplacée par `public/login-carret.jpg` (640×357 JPEG progressif q85, 28,7 Ko) produite depuis le fichier fourni `carret.png` (1664×928) — resize LANCZOS, fond opaque conservé.
- `src/app/connexion/page.tsx` : `src`, `alt` (« La mascotte de BoostClasse, un élève cubique qui salue… ») et attributs `width/height` (640×357) mis à jour. Ancien login-eleve.png conservé sur le disque (plus référencé).
- Sauvegardes : `backups/manual/2026-09-12-carret/` (page.tsx + login-eleve.png, md5 vérifiés) + base chiffrée `educapilote-20260912T103314Z-1412042.sql.gz.age`.
- Vérifs : typecheck OK, 17/17 tests vitest, build web + `up -d --no-deps web`, conteneur healthy, `/connexion` 200 (référence login-carret.jpg, plus aucune référence login-eleve), asset `/login-carret.jpg` 200 (28 733 octets), chunk `.next/static/chunks/130eo08d903l_.js`, capture visuelle validée sur https://boostclasse.com/connexion (cadre tourné, mascotte nette).

### 2026-09-12 (5) — Nouveau slogan « Apprendre ensemble » (bannière + connexion)

- **Objet** : remplacer le slogan peint « Apprendre en s'amusant ! » par « Apprendre ensemble ! » sur la bannière du haut (masthead-banner.webp) et l'image de la page /connexion (login-carret.jpg). Le fichier slogan.png fourni s'est révélé identique pixel pour pixel à carret.png (diff nul) ; le texte a donc été recomposé.
- **Méthode** : masthead — effacement de la zone de texte sarcelle (x130-755, y120-240) puis re-rendu en police pixel Minecraft 5×7 maison, sarcelle (10,93,97) avec ombre dure, deux lignes centrées « Apprendre » / « ensemble ! » ; décorations hautes (torches/cordes) et panneaux « Mes missions »/« Quitter » intacts, hotspots inchangés (dimensions 2172×312 conservées). Connexion — effacement du sous-titre noir (x620-1260, y190-282) rempli par dégradé de ciel échantillonné, nouveau texte « Apprendre ensemble ! » en Segoe UI Bold 61 px, recalcul du JPEG 640×357 q85 progressif (28 533 o).
- **Sauvegardes** : backups/manual/2026-09-12-slogan/ (anciens masthead-banner.webp c3deeec2…, login-carret.jpg 3566be59…) ; sauvegarde chiffrée educapilote-20260912T111317Z-1619792.sql.gz.age.
- **Chaîne** : scp + md5 conformes (c8f01177… webp, af7779d5… jpg) ; typecheck OK ; vitest 17/17 ; docker compose build web + up -d --no-deps web.
- **Vérifications** : HTTP 200 (127.0.0.1:18088 et https://boostclasse.com) tailles/md5 conformes ; contrôle visuel : slogan lisible et centré, aucun texte fantôme, raccords invisibles, page /connexion conforme dans son cadre incliné.

### 2026-09-12 (6) — Nouvelle bannière fournie par l'utilisateur (scène complète)

- **Objet** : remplacer la bannière retouchée (entrée 5) par l'image générée new_banniere.png (1664×928, 16:9, slogan « Apprendre ensemble ! » déjà inclus). La retouche pixel-art de l'entrée 5 est abandonnée au profit de ce visuel.
- **Asset** : masthead-banner.webp = conversion WebP q90 (148 820 o) de new_banniere.png, dimensions natives conservées (1664×928).
- **Adaptation CSS** (globals.css) : la bannière 16:9 remplacerait une bande 7:1 — affichage en crop contrôlé : hauteur clamp(240px,30vw,560px), object-fit:cover ancré en haut (bande source visible ~y0-500 : titre, mascotte en buste, panneau, tour). Hotspots recalés sur la nouvelle composition : marque = bloc titre (left 2%, top 7%, w 29%, h 38%) ; Mes missions = panneau en bois (left 51%, top 66%, w 15%, h 34%) ; Quitter = tour droite (left 82%, top 36%, w 16%, h 64%) ; .masthead-extra remonté en ciel dégagé (top 10%). shell.tsx : attributs width/height 1664×928.
- **Sauvegardes** : backups/manual/2026-09-12-banniere/ (masthead-banner.webp c8f01177…, globals.css 8a7bdc22…, shell.tsx 3ffa0809…) ; sauvegarde chiffrée educapilote-20260912T112715Z-1694080.sql.gz.age.
- **Chaîne** : scp + md5 conformes (webp 662cebb3…, globals.css 780cd4f8…, shell.tsx 35397303…) ; typecheck OK ; vitest 17/17 ; build + up -d --no-deps web.
- **Vérifications** : HTTP 200 bannière (127.0.0.1:18088 et https://boostclasse.com, 148 820 o, md5 conforme) ; règle clamp présente dans le chunk CSS construit (.next/static/chunks/14wu-71dkzdl-.css) ; prévisualisation locale des hotspots validée (titre/panneau/tour couverts, pastilles en ciel) ; visuel live intact.

### 2026-09-12 (7) — Bannière recomposée en bande proportionnée 2172×312

- **Objet** : l'affichage 16:9 en crop 30vw (entrée 6) donnait un en-tête de 240-560 px jugé « complètement disproportionné » (≈40 % de l'écran à 1900 px, mascotte coupée en plein corps). Retour à une bande large au ratio de la bannière historique (2172×312 ≈ 7:1, ~272 px à 1900 px, ~215 px à 1500 px).
- **Méthode** (recomposition depuis new_banniere.png, sans redessin) : le bloc titre sarcelle (source x805-1455, y362-522, « BoostClasse / Apprendre ensemble ! ») est extrait et agrandi à gauche (×0,6) ; la scène complète est réduite (×0,372) en tranche à droite (x1097-1672 du canevas) avec le titre de la dalle effacé par texture pierre échantillonnée ; le fond est prolongé en ciel dégradé + bande herbe/terre synthétiques (blocs 2-6 px) ; décor cloné depuis l'image source : 5 nuages, buisson à fleurs jaunes, lanterne droite, 6 étincelles dorées. Bords de tranche fondus (feather 18 px). Aucun texte repeint : seuls les pixels fournis par l'utilisateur sont utilisés.
- **Assets/code** : masthead-banner.webp = WebP q92 2172×312 (154 116 o, b3019342…) ; globals.css : .masthead-art-img height:auto (ratio naturel, plus de clamp/cover), hotspots recalés — marque = titre gauche (left 2,8 %, top 4,5 %, w 18,9 %, h 32,4 %), Mes missions = mascotte (left 53,4 %, top 3,2 %, w 8,8 %, h 64,1 %), Quitter = marge droite (left 79,2 %, top 8 %, w 20,2 %, h 83,3 %) ; .masthead-extra right 9 % / top 7 % (ciel droite) ; shell.tsx width/height 2172×312.
- **Sauvegardes** : backups/manual/2026-09-12-banniere2/ (webp 662cebb3…, globals.css 780cd4f8…, shell.tsx 35397303…) ; sauvegarde chiffrée educapilote-20260912T115355Z-1832295.sql.gz.age.
- **Chaîne** : scp + md5 conformes (webp b3019342…, globals.css c9445c7e…, shell.tsx 6dc0bb28…) ; typecheck OK ; vitest 17/17 ; build web + up -d --no-deps web.
- **Vérifications** : bannière 200 sur 127.0.0.1:18088 et https://boostclasse.com (154 116 o, md5 conforme) ; règles nouvelles dans le chunk CSS construit (.next/static/chunks/3vmgkrzfjxhky.css : height:auto + 4 zones) ; chunk JS 0cz23tmjp08qn.js contient masthead-art-img ; prévisualisation locale 1900/1500 px validée visuellement (titre lisible, mascotte torche visible, nuages/buisson, pastilles en ciel, aucune trace de l'effacement pierre) ; /eleve protégé (307) donc contrôle du masthead authentifié fait en prévisualisation locale aux valeurs exactes du CSS déployé.

### 2026-09-12 (8) — Bannière héros interactive élève (Minecraft x Pokémon) intégrée à /eleve

- **Objet** : intégrer à l'espace élève production la bannière héros du prototype livré par l'assistant Antigravity (commit 90ad12f6, style défaut « pika-minecraft », composant BannerNewStyle) avec les données réelles de l'application. L'ancien hero statique (fond dégradé « Bonjour … Prêt pour de nouvelles missions ? ») est remplacé.
- **Méthode** : port Vite/React → Next.js **sans nouvelle dépendance** : animations motion → transitions/keyframes CSS ; canvas-confetti → mini-confettis canvas maison (~25 lignes) ; sons → WebAudio maison (blip carré, jingle XP) ; alert() « Quitter » → vrai logout (api session DELETE puis /connexion, identique au shell) ; « Mes missions » → badge compte réel (useApi class/missions/today) + scroll vers .optional-missions ; h1 unique « BoostClasse » + slogan pixel « Apprendre ensemble ! » (police Press Start 2P chargée via link Google Fonts dans le layout racine). Interactivité conservée : personnage cliquable (bulles citations + confettis + compteur), 5 étoiles cliquables scintillantes, badge livre, toggle son (aria-pressed).
- **Nettoyage de l'image source** (boostclasse_pikacraft 1376×768) : le texte gravé du panneau (« ADVENTURE / AWAITS! » blanc lumineux, sous-ligne dorée « START THE JOURNEY | LEVEL 14 » sur la planche en dessous, y compris les jambages résiduels y483-502) est effacé par masquage pixel (blancs L>210, dorés R−B>55 & G−B>28, dilatation 5-6 px) puis resynthèse : intérieur du panneau (x766-1168, y288-448) en pierre tavelée procédurale calibrée sur les bords propres (L moyen 150,6, écart-type 27,3 : base basse fréquence par blocs 8 px diffusés + taches 3-9 px + grain), planche bois par diffusion. Cadre, rivets et poteau bouleau intacts ; aucun texte repeint — le titre affiché est du HTML superposé.
- **Assets/code** : public/banner-eleve.webp = WebP q85 (99 654 o, md5 14024862…) ; src/components/banner-eleve.tsx (md5 d676b90f…, correction TS5076 après premier typecheck : parenthèses autour de `C&&…webkitAudioContext` avant `??C`) ; student.tsx : hero statique remplacé par `<BannerEleve missionsCount={missions.data?.length??0}/>`, import lucide allégé (Sparkles/BookOpen/Flag ne servaient qu'au hero, 24732e03…) ; globals.css : bloc .banner-eleve/.be-* (~70 lignes, titre right 14 % pour poser sur la dalle, bevel pierre exact du prototype, media queries 900/640/560, prefers-reduced-motion) + patch règle 1050 (.banner-eleve:first-child margin-top:0) ; layout.tsx : preconnect + link Press Start 2P (42f35da3…).
- **Sauvegardes** : backups/manual/2026-09-12-banniere-eleve/ (student.tsx 23 490 o, globals.css 26 070 o, layout.tsx 698 o) ; sauvegarde chiffrée educapilote-20260912T165530Z-3441387.sql.gz.age.
- **Chaîne** : scp + md5 conformes (5 fichiers) ; typecheck : 1 échec TS5076 corrigé puis OK ; vitest 17/17 (3 fichiers) ; build web + up -d --no-deps web (conteneur healthy).
- **Vérifications** : /banner-eleve.webp 200 (99 654 o) sur 127.0.0.1:18088 et https://boostclasse.com ; chunks construits contiennent la bannière (CSS .next/static/chunks/2obp_wancgeid.css + JS 2mm6u8iecvb8g.js avec be-slogan et Press+Start+2P) ; /eleve 307 (protégé), /connexion 200 ; prévisualisation locale validée visuellement en desktop 1200 px et mobile 375 px (Edge headless, vraies media queries) : titre/slogan lisibles sur la dalle nettoyée, boutons pierre entiers avec badge missions, étoiles et badge livre en place, aucun chevauchement, aucune trace du texte effacé.
- **Information** : le commit Antigravity 90ad12f6 reste local à AI Studio (non poussé sur GitHub) ; le livrable effectif intégré ici est le prototype Vite/React de C:\work\training.

### 2026-09-12 (9) — Badge emblème sur la page de connexion + retrait du bloc « Une activité proposée pour moi »

- **Objet** : (1) remplacer la photo polaroïd de la page de connexion (login-carret.jpg, entrée « carret ») par l'emblème BoostClasse fourni par l'utilisateur (badge mascotte issu du prototype Antigravity, asset rocket_star_badge_1789222053636.jpg 1024×1024) ; (2) supprimer de /eleve la section « Une activité proposée pour moi » (.optional-missions), jugée inutile et distrayante pour l'élève.
- **Assets/code** : public/login-badge.webp (WebP q88, 640×640, 120 608 o, md5 67e187eb…) ; connexion/page.tsx : .login-photo img src=/login-badge.webp, alt « L'emblème de BoostClasse : sa mascotte sur son île, entourée d'étoiles », dimensions 640×640, cadre polaroïd incliné conservé ; student.tsx : section optional-missions retirée (imports tous toujours utilisés : ArrowRight, Card, Button, Compass vérifiés) ; globals.css : règles mortes supprimées (.optional-missions, .mission-grid, .mission-card et variantes, .mission-top ; .mission-grid retiré des media queries 1050/760).
- **Note d'interaction** : le bouton « Mes missions » de la bannière élève scrolle désormais vers .choice-section (fallback prévu dans banner-eleve.tsx) ; le badge missionsCount du bouton reste alimenté par l'API réelle.
- **Sauvegardes** : backups/manual/2026-09-12-badge-login/ (connexion/page.tsx 2 651 o, student.tsx 22 696 o, globals.css 31 519 o) ; sauvegarde chiffrée educapilote-20260912T185402Z-4071657.sql.gz.age.
- **Chaîne** : scp + md5 conformes (4 fichiers) ; typecheck OK ; vitest 17/17 (3 fichiers) ; build web + up -d --no-deps web (conteneur healthy).
- **Vérifications** : /connexion 200 et /login-badge.webp 200 (120 608 o) sur 127.0.0.1:18088 et https://boostclasse.com ; chunk JS 2x_w3izoeljuc.js contient login-badge ; « Une activité proposée pour moi » absente du build ; login-carret.jpg conservé en public/ (inutilisé mais disponible pour un retour arrière) ; prévisualisation locale du panneau story validée visuellement (badge dans le cadre blanc incliné, sous le chemin en pointillés).

### 2026-09-12 (10) — Retrait de la section « Fluence calculatoire » (le vrai bloc demandé)

- **Objet** : supprimer de la bibliothèque mathématiques de /eleve la section « Fluence calculatoire / Calcul mental chronométré » (grille de 9 séries chronométrées 60 s : tables, compléments, doubles…). Nouvelle lecture des captures de l'utilisateur (zoom-bloc.png = zoom 2× de la première capture, user-shot-full.png = seconde capture) : les deux montrent cette section, et non le bloc « Une activité proposée pour moi » retiré en (9) — ce mauvais ciblage explique le retour « je t'ai demandé de supprimer, mais tu le gardes toujours ». Le retrait (9) reste pertinent, mais le bloc visé était celui-ci.
- **Code** : src/components/math-library.tsx — composant FluenceLab, FLUENCE_SERIES (9 séries), FLUENCE_DURATION, rand(), type FluenceSerie et rendu `<FluenceLab/>` retirés ; imports allégés (useEffect, FormEvent, Trophy, Timer, ExternalLink ne servaient plus) — 12 194 → 5 071 o, md5 c5b1bd98… ; src/components/subject-banner.tsx — tagline maths « 32 ateliers pour comparer, calculer, mesurer et raisonner. » (mention « plus la fluence calculatoire pour t'entraîner en 60 secondes » retirée), md5 7014ea38… ; src/components/math-workshop.css — bloc .fluence-lab→.fluence-links a + les 2 media queries 900/650 px retirés, 4 686 → 1 239 o, md5 f76eaa07…. La clé localStorage « edu-fluence-best » n'est plus lue ni écrite (les scores existants deviennent inertes, aucun nettoyage nécessaire).
- **Sauvegardes** : backups/manual/2026-09-12-retrait-fluence/ (math-library.tsx 12 194 o, math-workshop.css 4 686 o, subject-banner.tsx 2 213 o) ; sauvegarde chiffrée educapilote-20260912T191607Z-4190481.sql.gz.age.
- **Chaîne** : scp + md5 conformes (3 fichiers) ; typecheck OK ; vitest 17/17 (3 fichiers) ; build web + up -d --no-deps web.
- **Vérifications** : aucun chunk JS servi sur 127.0.0.1:18088 (/ et /connexion, tous les /_next/static/chunks/*.js référencés greppés) ne contient « fluence » ; /app/.next/static du conteneur propre (le répertoire .next de l'hôte VPS est un vestige de build local non servi, il contient encore les anciens chunks) ; https://boostclasse.com/connexion 200.

### 2026-09-12 (11) — Page de connexion : trois cartouches
- Demande utilisateur : placer la bannière Minecraft de /eleve sur /connexion et présenter le panneau gauche en trois cartouches.
- connexion/page.tsx : .login-path (3 tuiles icônes) et .login-photo (polaroïde seul) remplacés par .login-cartouches — 3 cartes inclinées reliées de pointillés : /banner-eleve.webp (bannière Minecraft), /login-badge.webp (emblème, carte carrée), /banner-sciences.jpg (laboratoire), chacune avec pastille icône (BookOpen, Compass, Flower2) en bas à droite.
- globals.css : règles .login-path/.login-photo retirées, règles .login-cartouches/.login-cartouche ajoutées ; à ≤760 px la bande est masquée comme avant (login-foot inclus).
- Sauvegardes : manual/2026-09-12-cartouches-login (page.tsx, globals.css) + chiffrée 20260912T192955Z-73101.
- Vérifs : typecheck OK ; vitest 17/17 ; /connexion 200 avec 3 .login-cartouche et les 3 images ; assets 200 ; plus aucune classe login-path/login-photo servie ; https://boostclasse.com/connexion 200.

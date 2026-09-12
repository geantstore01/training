# Modules 9 et 10 — application web

Le frontend est dans `apps/web`. Il utilise Next.js 16.3.4 App Router, React 19.3, TypeScript strict, Tailwind CSS 4 et des composants shadcn/ui adaptés au thème du projet (Radix Slot, CVA, `cn`, variantes typées). Les versions exactes et intégrités sont fixées dans `package-lock.json`. Le conteneur Node 22 est fixé par digest.

## Écrans livrés

| Page | Parcours |
|---|---|
| `/connexion` | Connexion avec établissement, identifiant et mot de passe ; orientation selon le rôle |
| `/eleve` | Missions affectées, leçon validée, essai libre, exercice guidé, autonomie, bilan et fin de séance |
| `/parent` | Enfants autorisés, progression, compétences travaillées, temps estimé, rapports, consentements et confort de lecture |
| `/enseignant` | Classes, élèves, groupes, difficultés récurrentes, composition et archivage des missions, plafonds d’aide par élève |

Les pages ne contiennent aucune donnée de démonstration. Un établissement sans comptes, élèves, contenus ou missions voit un état vide explicite. Les comptes se créent avec les mécanismes du module 2 ; le frontend ne crée pas automatiquement un administrateur ou des identifiants de démonstration.

### Parcours élève

Le fil en six étapes matérialise la progression dans l’activité, sans note ni comparaison. Une leçon associée n’est affichée que si elle est approuvée. Sans leçon associée, l’écran le dit et invite à relire la consigne avec l’enseignant ; aucune explication disciplinaire n’est inventée.

L’essai libre reste en mémoire et porte une mention explicite de non-enregistrement. Les exercices guidés et autonomes sont de vraies tentatives du service assessment, corrigées par ses validateurs déterministes. Une mission de deux exercices ou plus utilise le premier pour le guidage et les suivants pour l’autonomie. Une mission ancienne comportant un seul exercice propose explicitement de le reprendre sans tuteur. La phase autonome masque l’aide ; le serveur conserve la comptabilité des aides réellement reçues.

Les composants prennent en charge QCM, réponses numériques et textuelles, textes à compléter, problèmes à plusieurs parties, classement et frise chronologique. Le déplacement des cartes possède toujours une alternative au clavier avec les boutons Monter/Descendre. Les retours viennent du serveur, jamais d’une correction simulée dans React.

Le tuteur appelle `/turns`, affiche le JSON pédagogique validé et propose des aides progressives. Le bouton audio **lit la consigne de l’exercice**, via speech-service : il ne prétend pas vocaliser une réponse libre du LLM. Les URL audio en mémoire sont révoquées après lecture et au démontage. Les accords parent/enfant restent vérifiés par le serveur.

### Parent et enseignant

Les graphiques représentent des états de compétences avec leurs libellés textuels ; aucune information n’est transmise uniquement par la couleur. Le temps affiché reste l’estimation des sessions closes définie au module 7. Les recommandations à domicile sont des suggestions générales d’accompagnement, signalées comme telles.

Les consentements ne sont pas présélectionnés. Le parent doit confirmer sa compréhension avant d’autoriser un usage. L’enfant peut donner ou retirer son assentiment séparément. Les préférences de lecture enregistrées par le parent sont appliquées dans l’espace élève ; les réglages rapides du bandeau restent limités à la visite.

L’enseignant peut créer sa classe, inscrire les élèves déjà accessibles, former des groupes, sélectionner des exercices publiés et archiver une mission. Un administrateur peut choisir l’enseignant responsable lors de la création. L’affectation initiale d’un nouvel élève hors du périmètre de l’enseignant relève de l’administrateur, conformément aux règles d’accès existantes.

## Sécurité et état

- Le navigateur possède uniquement `edu_session`, un identifiant aléatoire de 256 bits dans un cookie HttpOnly, SameSite Strict. Aucun JWT ni refresh token n’est placé dans le HTML, localStorage ou sessionStorage.
- Next.js conserve les jetons dans Redis sous l’ACL dédiée `edu_web`, limitée à `edu:web:*`. Le renouvellement utilise un verrou distribué et une durée de session absolue de sept jours.
- Les routes Next.js appellent les services depuis le serveur. Une liste fermée de chemins exclut les endpoints internes et les corrigés éditoriaux. Les mutations exigent une origine autorisée ; les contrôles de rôle et de tenant restent appliqués par chaque service.
- Les pages et réponses privées sont non mises en cache. Une CSP avec nonce protège les scripts ; les polices sont embarquées, sans requête Google Fonts. Aucun outil de publicité, de suivi tiers ou de classement n’est ajouté.
- React `useReducer` gère le parcours et ses réponses. Les erreurs réseau de soumission conservent l’essai à l’écran. Les brouillons ne sont pas persistés dans le navigateur ; fermer la page avant envoi peut les perdre. Une confirmation accompagne la sortie d’une tentative en cours.

La migration **0007_student_controls** ajoute `tutor_controls` sous RLS forcée. Les endpoints `GET/PUT /classes/{id}/students/{student_id}/tutor-control` exigent une affectation à la classe et une révision attendue. Le plafond 0–6 et la suspension sont contrôlés par le tuteur, le routeur IA et les indices déterministes. Le tuteur revérifie la limite avant de retourner un nouveau résultat et borne également la relecture d’une réponse idempotente. Ces réglages ne remplacent pas les consentements.

## Lancement sur le VPS

L’accès de développement reste limité à la boucle locale du VPS, sur le port 18088. Depuis un poste client :

```bash
ssh -L 18088:127.0.0.1:18088 root@192.168.1.10
```

Ouvrir ensuite `http://localhost:18088`. Les API restent disponibles sous `/services/<service>/...` et le frontend sous `/`.

```bash
cd /stockage/training
python3 scripts/init_security_secrets.py
docker compose -f docker-compose.dev.yml build
bash scripts/backup.sh
docker compose -f docker-compose.dev.yml run --rm --no-deps migrate alembic upgrade head
docker compose -f docker-compose.dev.yml up -d --wait
docker compose -f docker-compose.dev.yml up -d --no-deps --force-recreate --wait proxy
```

Pour une exposition HTTPS, utiliser l’overlay de production et renseigner `EDU_PUBLIC_ORIGIN=https://votre-domaine` avec les paramètres TLS existants. L’overlay force `COOKIE_SECURE=true`. Le mode HTTP local utilise explicitement un cookie non Secure ; il ne doit pas être exposé publiquement. Les origines sont exactes, sans barre oblique finale. Aucun compte Ollama ni secret du VPS n’est inclus dans le frontend.

## Développement et tests

```bash
cd apps/web
npm ci
npm run typecheck
npm test
npm run build
```

Pour `npm run dev`, configurer Redis et son fichier de secret, `WEB_ORIGINS=http://localhost:3000,http://127.0.0.1:3000` et `COOKIE_SECURE=false`. `BACKEND_BASE` permet de joindre un proxy API depuis un poste de développement ; en conteneur il reste absent et les services sont joints directement sur le réseau privé.

La recette Playwright utilise Edge installé et un Redis accessible sur `127.0.0.1:16379`, avec l’ACL `edu_web` et le fichier `../../secrets/redis_web`. `playwright.config.ts` lance un **double HTTP explicite**, limité à `tests/browser/backend.mjs`, et le vrai frontend compilé. Les données de cette recette sont fictives et ne sont jamais injectées dans PostgreSQL. Les tests couvrent navigation, session opaque, CSRF, exercices, consentements, formulaires, clavier et contrôles axe. Les tests Pytest, séparés, vérifient les droits métier sur PostgreSQL/Redis réels dans une base isolée.

Les vérifications automatisées WCAG 2 AA / 2.1 AA et le clavier constituent une recette technique, pas une certification complète. La police Atkinson Hyperlegible, l’agrandissement et l’espacement aident la lecture sans garantir un confort universel pour toutes les personnes DYS.

Références de conception technique : [Next.js BFF](https://nextjs.org/docs/app/guides/backend-for-frontend), [shadcn/ui et Tailwind 4](https://ui.shadcn.com/docs/tailwind-v4), [installation manuelle shadcn/ui](https://ui.shadcn.com/docs/installation/manual).

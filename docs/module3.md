# Module 3 — Curriculum et contenus

Le code des deux services FastAPI, les schémas Pydantic v2, la migration Alembic
0003 et les tests sont livrés. Les autres modules métier ne sont pas développés
par cette livraison. Les JWT, révocations Redis et droits par école du module 2
s’appliquent à chaque endpoint métier.

## Référentiel Cycle 3

Le catalogue partagé comprend les matières Français (`francais`), Mathématiques
(`mathematiques`) et Histoire (`histoire`), ainsi que les niveaux CM1 et CM2.
`curriculum_domains` regroupe les compétences par matière. Chaque compétence
conserve un domaine, un niveau, un code, un libellé, une description, des objectifs,
des erreurs fréquentes, une URL officielle HTTPS, une version de programme et
une période de validité inclusive. La cohérence domaine/matière est aussi imposée
par une clé étrangère PostgreSQL composite.

Les compétences créées par API sont immuables : une révision de programme demande
un nouveau code/version. Les URL sont validées comme références du ministère ou
de Légifrance ; elles ne sont pas téléchargées. Ce contrôle ne certifie pas
l’exactitude pédagogique du contenu saisi, qui relève du responsable du catalogue.
Les anciens enregistrements du socle peuvent avoir un domaine nul et des listes
vides ; les nouvelles créations API exigent un domaine et des objectifs.

Seul `sys_admin` enrichit le catalogue national et ses prérequis. Les créateurs
et administrateurs d’une école ne peuvent pas modifier le référentiel de toutes
les autres écoles. Tout utilisateur connecté peut le lire. Les écritures sont
auditées avec l’identité de leur auteur, sans recopier les textes.

### Endpoints curriculum-service

Préfixe via Nginx : `/services/curriculum-service`.

| Méthode | Chemin | Fonction |
|---|---|---|
| GET | `/subjects` | Trois matières |
| GET | `/levels` | CM1 et CM2 |
| GET | `/evaluation-levels` | Six niveaux de maîtrise |
| GET, POST | `/domains` | Liste paginée / création de domaine |
| GET, POST | `/competencies` | Recherche paginée / création |
| GET | `/competencies/{id}` | Fiche complète |
| POST | `/competencies/{id}/prerequisites` | Ajouter un prérequis |
| DELETE | `/competencies/{id}/prerequisites/{prerequisite_id}` | Retirer une arête |
| GET | `/competencies/{id}/graph` | Parcours amont ou aval |

Recherche : `subject_id`, `domain_id`, `level`, `programme_version`, `effective_on`,
`limit` (100 maximum), `offset`. Sans date, la recherche inclut les différentes
versions de programme : fournir `effective_on` pour sélectionner la période.

Le graphe est orienté de la compétence vers ses prérequis. `direction=upstream`
renvoie les compétences à reprendre après un échec ; `downstream` explore les
dépendants. La racine est incluse à distance 0 ; les autres distances sont les
plus courtes. Les nœuds sont dédupliqués, y compris pour les graphes en losange.
`max_depth` vaut 10 par défaut, maximum 30 ; `truncated` signale une frontière
encore ouverte. Une réponse dépassant 200 nœuds est refusée en 422 ; la requête SQL
est limitée à trois secondes. Les cycles et auto-dépendances sont rejetés en 409,
avec verrou transactionnel commun aux modifications et garde PostgreSQL.

L’option `student_id` ajoute les états de maîtrise, uniquement pour l’élève
lui-même, son représentant vérifié, son enseignant affecté ou l’administrateur de
son école. Les créateurs de contenus n’accèdent pas aux résultats individuels.
Aucune identité d’élève n’est incluse dans le graphe.

Les valeurs exactes sont `non_evalué`, `découverte`, `en_cours`, `fragile`,
`maîtrisé`, `consolidé`. Elles sont définies par une énumération partagée et un
CHECK PostgreSQL. Une absence de mesure retourne `non_evalué`. Aucun seuil de
probabilité arbitraire n’est inventé : l’écriture des résultats et le calcul de
maîtrise appartiennent au futur assessment-service.

### Références et données initiales

Le calendrier varie selon les programmes. Le français et les mathématiques de
2025 s’appliquent au CM1 depuis 2025 et au CM2 depuis 2026. Le nouveau programme
d’histoire-géographie de 2026 s’applique au CM1 en 2026 ; l’ancien reste applicable
au CM2 pendant 2026–2027. Sources officielles consultées le 10 septembre 2026 :

- [Français — éduscol](https://eduscol.education.gouv.fr/4800/ressources-d-accompagnement-du-programme-de-francais-au-cycle-3)
- [Mathématiques — éduscol](https://eduscol.education.gouv.fr/5712/ressources-d-accompagnement-du-programme-de-mathematiques-au-cycle-3)
- [Histoire-géographie — éduscol](https://eduscol.education.gouv.fr/4791/ressources-d-accompagnement-du-programme-d-histoire-et-geographie-au-cycle-3)
- [Arrêté du 10 avril 2025, application](https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000051468925)

La migration initialise uniquement les trois matières, sans présenter un catalogue
fabriqué comme programme officiel exhaustif. Les compétences et contenus de test
sont explicitement synthétiques et confinés à une base jetable. Les API permettent
au responsable pédagogique de saisir et référencer le catalogue validé.

## Contenus versionnés

Un contenu possède un identifiant, un slug unique dans son école, un auteur et
un type : `lesson`, `teaching_sheet` ou `learning_sequence`. Une version contient
un titre, un résumé, des objectifs et des blocs de texte typés (paragraphe,
exemple, activité, question). Une séquence comporte aussi des étapes ordonnées,
chacune avec objectif, durée et blocs. Les fiches pédagogiques sont réservées à
l’équipe ; élèves et parents n’y accèdent pas même après approbation.

Le corps est du texte structuré, pas du HTML exécutable. Une future interface doit
l’afficher comme texte échappé. Les modèles interdisent les propriétés non prévues,
les références dupliquées et les structures incohérentes. La taille maximale des
requêtes est 32 Kio, comme pour le module 2 ; découper les séquences trop longues.

Chaque version référence au moins une compétence et une source de son école.
La source conserve URL HTTPS, éditeur, licence, date et SHA-256 déclarés. Aucun
fichier distant n’est téléchargé, et le condensat n’est pas prétendu vérifié par
le serveur. Le relecteur doit contrôler ces références et les droits d’usage.
L’approbation du cours n’approuve pas automatiquement sa source pour le futur RAG.

### Workflow et garanties

`draft → pending_review → approved → archived`

Une demande de correction ou un rejet ramène `pending_review` à `draft` et laisse
la décision dans le journal immuable. Chaque nouvelle soumission ouvre un tour de
revue distinct. Une approbation ancienne ne peut pas servir pour un autre tour.
Un auteur ou administrateur peut également archiver un brouillon ou une version
en attente. L’archivage est terminal pour la version.

- Seuls `teacher` et `content_creator` créent des contenus et rendent une décision
  de relecture. Une simple fonction d’administration n’autorise pas à approuver.
- La soumission et l’ajout d’une version sont réservés à l’auteur du contenu.
- Le relecteur doit être différent de l’auteur et de l’éditeur de la version,
  avoir un compte actif et confirmer explicitement sa relecture humaine.
- La décision `approved` publie cette version dans la même transaction. Il n’existe
  aucun endpoint permettant de forcer `status` ou `published_at` depuis le client.
- Une nouvelle version commence toujours en brouillon. La version approuvée
  précédente reste disponible jusqu’à l’approbation de sa remplaçante, puis est
  archivée atomiquement. Un index unique empêche deux versions approuvées courantes.
- Le numéro de version est alloué sous verrou du contenu. `base_version` doit être
  le dernier numéro connu, sinon 409. Les soumissions et décisions obsolètes sont
  refusées dès qu’une version plus récente existe.
- Le titre et le corps d’une version ne sont jamais modifiés en place, même en
  brouillon. Les modifications exigent une nouvelle version complète. Les liens
  ne sont pas modifiables par API ; leurs UPDATE/DELETE sont bloqués en base.
- Les revues restent immuables même face à un UPDATE/DELETE du propriétaire SQL.
  Les contrôles de transition et de relecture s’appliquent aussi en PostgreSQL.

L’application distingue accès aux brouillons et accès à la publication pour
**tous** les environnements, pas seulement pour une variable « production ».
Les droits restent limités à l’école issue du JWT vérifié et sont renforcés par RLS.
La validation humaine ne remplace pas le service de filtrage : aucun appel au
modèle de sécurité ni à une IA n’est ajouté implicitement par ce module.

### Endpoints content-service

Préfixe via Nginx : `/services/content-service`.

| Méthode | Chemin | Fonction |
|---|---|---|
| GET, POST | `/sources` | Références documentaires de l’école |
| GET, POST | `/contents` | Catalogue paginé / création de contenu et version 1 |
| GET | `/contents/{id}` | Version actuellement approuvée |
| GET, POST | `/contents/{id}/versions` | Historique paginé / nouvelle version |
| GET | `/contents/{id}/versions/{number}` | Version précise, selon droits |
| POST | `/contents/{id}/versions/{number}/submit` | Soumettre à relecture |
| GET, POST | `/contents/{id}/versions/{number}/reviews` | Historique / décision humaine |
| POST | `/contents/{id}/versions/{number}/archive` | Archiver une version |

Filtres du catalogue : `kind`, `status`, `competency_id`, `limit`, `offset`.
L’équipe voit la dernière version correspondant au statut demandé ; sans statut,
elle voit la dernière version du contenu. Les élèves et parents voient uniquement
la version approuvée et ne peuvent pas demander les brouillons. L’historique et
les revues sont réservés aux enseignants, créateurs et administrateurs de l’école.
Les codes 401, 403, 404, 409, 413, 422, 429 et 503 sont décrits dans OpenAPI.

## Exploitation et migrations

Le schéma compte 40 tables métier (41 avec Alembic). La migration 0003 préserve
les données existantes, convertit les statuts des leçons et laisse inchangés ceux
des exercices du socle. Plusieurs anciennes versions publiées d’une même leçon
font échouer la migration avec un message demandant un archivage préalable.
Le downgrade est réservé aux bases sans données spécifiques au module 3 ; il
refuse la perte d’objectifs, domaines, tours de revue ou états de maîtrise. Les
matières ajoutées restent disponibles après retour à 0002.

Les deux nouveaux services possèdent chacun leur compte SQL et leur utilisateur
Redis ACL. Ils peuvent lire les sessions pour vérifier les JWT, mais ne peuvent
pas les modifier. Ils reçoivent les clés publiques et une clé de limitation de
débit, sans clé privée de signature ni clé de déchiffrement des profils.

```bash
cd /stockage/training
python3 scripts/init_security_secrets.py
docker compose -f docker-compose.dev.yml build curriculum-service content-service migrate
docker compose -f docker-compose.dev.yml up -d --no-build
docker compose -f docker-compose.dev.yml restart proxy
bash scripts/test_module3.sh
bash scripts/verify_migrations.sh
bash scripts/verify_restore.sh
python3 scripts/smoke.py
```

Les clés supplémentaires sont créées sans écraser les clés existantes. Redis est
recréé par Compose quand ses montages de secrets changent. Les trois services du
module 2 restent compatibles avec cette migration.
Les commandes d’initialisation du premier administrateur sont dans [module2.md](module2.md).
Les contrats complets figurent dans les dossiers des deux services (`openapi.json`)
et sont consultables dans Swagger avec `/services/<service>/docs` via tunnel SSH.

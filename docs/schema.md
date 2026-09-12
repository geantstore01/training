> Module 4 : 41 tables métier, preuves de maîtrise et résultats idempotents.
> Voir [module4.md](module4.md).

> Module 3 : 40 tables métier, domaines pédagogiques, niveaux de maîtrise et
> statuts des leçons actualisés. Voir [module3.md](module3.md).

> Évolution module 2 : la migration `0002_access_safety` porte le schéma à
> 39 tables métier. Elle ajoute les accords élèves, les versions d’authentification,
> les preuves de liaison chiffrées et les événements de consentement immuables.
> Une école correspond à un tenant. Voir [le guide actuel](module2.md).
> La description ci-dessous documente le socle initial.

# Modèle de données

## Conventions

Tous les enregistrements ont un UUID généré par PostgreSQL et des timestamps
`timestamptz`. `updated_at` est maintenu par trigger même pour du SQL direct.
Les enums sont des chaînes avec CHECK nommés, afin de simplifier les évolutions
transactionnelles. Les probabilités et coûts sont des NUMERIC, pas des flottants.

Les données d'un établissement sont rattachées à un `tenant`. Un tenant peut
contenir plusieurs écoles. Les identités sont locales au tenant : un utilisateur
intervenant dans plusieurs tenants possède une identité distincte dans chacun.
Chaque table tenant possède une unicité `(tenant_id,id)` ; les FK entre tables
tenant sont composites pour empêcher les références croisées, même sans RLS.

Les tables `subjects`, `curriculum_levels`, `competencies` et
`competency_prerequisites` forment le référentiel global, lisible par les services,
modifiable seulement par curriculum-service et la maintenance.

## Entités et liens

| Domaine | Tables et relations |
|---|---|
| Identités | tenants → users → user_roles ; guardians, students et teachers référencent users |
| Représentants | guardian_students relie les guardians aux students, avec preuve d'autorité vérifiée |
| Scolarité | schools → classes ; enrollments relie classes et students ; teacher_classes relie teachers et classes |
| Groupes | learning_groups rattachés à une classe ; group_members relie groupes et élèves |
| Programme | subjects + curriculum_levels → competencies ; competency_prerequisites forme un graphe sans cycles |
| Cours | lessons → lesson_versions → lesson_competencies / lesson_sources |
| Exercices | exercises → exercise_versions → exercise_competencies / exercise_sources / hints |
| Travail | students → learning_sessions → exercise_attempts → answers |
| Progression | mastery_records et spaced_repetition_items : unicité élève/compétence |
| IA | ai_interactions liées à une session et au même élève ; safety_events liés facultativement à une interaction |
| RAG | content_sources → content_chunks ; embedding 768 dimensions + index HNSW cosinus et GIN français |
| Gouvernance | content_reviews ciblent exactement une version ; audit_logs ; consent_records |

La session et l'élève d'une tentative ou interaction IA sont vérifiés ensemble
par une FK triple. Les tentatives sont idempotentes par tenant. Une tentative
ne peut démarrer que sur une version publiée. Les réponses référencent toujours
une tentative et la tentative une version précise, jamais le contenu courant.

## Publication

Une nouvelle version doit être `draft`. Le passage à `in_review` fige son
contenu et ses enfants (indices, compétences, références). Un utilisateur actif
ayant le rôle teacher/moderator/tenant_admin et différent de l'auteur peut la
valider, via admin-service. La publication exige la dernière décision approuvée
après la dernière soumission. Un retour au brouillon invalide l'ancienne revue.
Une version publiée peut uniquement devenir `retired`, sans modifier son contenu.
Les revues sont insérables mais non modifiables par les services applicatifs.

## Conservation et suppression

Les références sensibles sont principalement `RESTRICT`, pour éviter une purge
en cascade accidentelle. Les réponses suivent la suppression d'une tentative ;
les rôles suivent celle d'un utilisateur. L'effacement d'un élève devra être
orchestré dans une transaction et dans l'ordre des dépendances par user-service.
Un `deleted_at` n'est pas un effacement RGPD : il n'est pas présenté comme tel.

Les traces IA, sécurité et audit possèdent `expires_at` indexé. Le script
`scripts/purge_expired.py` supprime uniquement les traces expirées du tenant
explicite ; une interaction conservant un événement de sécurité non expiré reste
présente pour préserver l'intégrité. Aucune durée légale universelle n'est codée.

Le consentement enregistre finalité, version de politique, base juridique,
décision et preuve chiffrée. Le lien représentant/élève doit être vérifié.
Les données de preuve sont immuables ; le retrait peut être enregistré une seule
fois. Les renouvellements créent de nouveaux enregistrements. Le futur moteur
d'autorisation doit évaluer le dernier enregistrement pertinent, son retrait et
son expiration avant chaque traitement qui le nécessite.

## Limites volontaires du module

Seuls CM1/CM2 sont initialisés. Aucun programme officiel, cours ou exercice
inventé n'est importé : le contenu versionné et sourcé appartient aux modules
curriculum/content. Le choix 768 dimensions est un contrat de stockage, pas
l'annonce d'un modèle d'embedding déjà opérationnel. Tout changement de modèle
incompatible requiert une migration et une réindexation.

Le DDL SQL figé est livré dans `migrations/sql/0001_schema.sql` ; les protections
et droits font partie de la même migration via `0001_security.sql`. Ne pas
réexécuter l'export initial après une modification des modèles : créer `0002`.

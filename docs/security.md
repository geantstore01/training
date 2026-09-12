# Périmètre de sécurité — modules 1 à 4

## Mesures effectives

- RLS activée et forcée sur toutes les tables tenant, y compris tenants.
- Sans `app.tenant_id`, aucune ligne tenant n'est accessible aux comptes applicatifs.
- Contexte tenant transactionnel via `set_config(..., true)` ; pas de fuite via le pool.
- 15 comptes SQL sans superuser, BYPASSRLS, création de rôle/base ou DDL.
- Droits par domaine ; tutor-service ne peut pas lire `answer_spec`.
- Audits et revues sans UPDATE/DELETE pour les services.
- Aucun texte de conversation, adresse IP ni email dans les traces IA/sécurité/audit.
- Identité du représentant, email et réponses d'élève stockables seulement dans des
  colonnes binaires dédiées au ciphertext ; aucune fonction de chiffrement factice.
- Réseau base/cache non publié, mots de passe SCRAM et secrets aléatoires distincts.
- Redis authentifié, AOF, noeviction, commandes administratives dangereuses désactivées.
- TLS pour l'entrée publique via overlay, conteneurs applicatifs sans root, logs limités.

## Frontières à respecter dans les prochains modules

`app.tenant_id` n'est pas une authentification : un service compromis peut choisir
un autre tenant dans son propre domaine. Il doit exclusivement le définir depuis
une identité authentifiée et autorisée. Les rôles SQL limitent les domaines, mais
le RBAC enseignant/parent/élève, les JWT rotatifs et les accès individuels sont
appliqués dans les trois services du module 2. Aucun endpoint ne reçoit de SQL.
Le school_id de connexion est vérifié ; ensuite le contexte vient du JWT signé.

Le superuser PostgreSQL contourne la RLS ; ses secrets sont réservés à
l'initialisation et aux tests/administration. Ne pas exécuter les services métier
avec le compte migrator. Les secrets de test ne sont montés que dans le profil test.

Les profils et preuves de liaison sont chiffrés par AES-256-GCM avec contexte
école/propriétaire/finalité authentifié et clés versionnées. Sauvegarder les clés
séparément et tester leur restauration. Les parcours d’export et d’effacement
complets restent à construire. Voir [module 2](module2.md).

Redis isole auth/user/safety par utilisateurs ACL et préfixes. Les refresh tokens
ne sont conservés que sous forme de condensats ; les rotations sont atomiques.
Les autres services conservent seulement l’espace cache commun du socle.
Le réseau Docker interne n'est pas chiffré ; une installation multi-hôte devra
ajouter le chiffrement et l'authentification interservices adaptés.

## Exploitation avant ouverture aux mineurs

Valider les responsabilités de traitement, les finalités/bases juridiques, la
politique de conservation et l'analyse d'impact avec le responsable concerné.
Ne pas assimiler une ligne `consent_records` à une conformité juridique acquise.
Le moteur de sécurité comporte dix couches effectives et un modèle NER local.
Il réduit les risques sans garantir une anonymisation exhaustive ni détecter
toutes les formulations dangereuses. Aucun appel cloud n’est effectué. Un
indicateur de détresse ne déclenche pas encore de notification externe.

Installer un certificat de confiance, limiter l'administration, superviser les
échecs de sondes et de sauvegarde, vérifier la restauration, analyser régulièrement
les images/dépendances et requalifier les mises à jour avant déploiement.

## Validation éditoriale du module 3

Curriculum et content vérifient les mêmes JWT et révocations que les services
du module 2 et ont des ACL Redis distinctes. Le catalogue national est modifiable
seulement par sys_admin. La publication d’un contenu d’école exige la revue d’un
enseignant ou créateur distinct de l’auteur, sur la version et le tour de revue
courants ; une fonction d’administration seule ne permet pas l’approbation.
Les élèves et parents ne reçoivent ni brouillons ni historique de relecture.
Voir [les garanties et limites](module3.md).

## Exercices et évaluations du module 4

Les corrigés restent privés et les réponses sont chiffrées. Les calculs emploient
un interpréteur arithmétique limité, sans eval ni appel LLM. Les requêtes rejouées
ne dupliquent pas la maîtrise. Les niveaux d’aide sont relevés côté serveur.
Les API n’exposent pas de notes ou probabilités numériques. Les paramètres du
modèle probabiliste sont des valeurs de départ, à calibrer pédagogiquement ; ils
ne constituent pas une mesure validée des capacités de l’enfant.

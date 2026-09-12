# Recette des modules 9 et 10

Contrôles du 10 septembre 2026, source locale `D:\codex\training`, déploiement `/stockage/training` sur le VPS.

## Frontend

- Compilation Next.js de production et TypeScript strict : réussies.
- Vitest : **5 tests réussis**, couvrant séparation des espaces, chemins autorisés et état du parcours.
- Playwright/Edge : **5 scénarios réussis** sur le frontend compilé. Connexion et renouvellement des jetons côté serveur, cookie opaque HttpOnly, rejet CSRF, parcours complet, QCM/texte/nombre, déplacement au clavier, tuteur, consentements, mission, groupe et contrôle enseignant.
- Les trois espaces ont été contrôlés en format mobile à 390 px, sans débordement horizontal.
- Les scans axe des écrans de recette ne signalent **aucune violation** pour les tags WCAG 2 A, 2 AA et 2.1 AA. Les captures ont été inspectées. Ces vérifications ne constituent pas une certification exhaustive WCAG ni une étude d’usage DYS.
- `npm audit --omit=dev --audit-level=high` : aucune vulnérabilité signalée au moment de la recette.

Les scénarios navigateur utilisent un double HTTP clairement isolé dans `tests/browser/backend.mjs`, avec des données fictives, et un vrai stockage Redis des sessions. Ils ne revendiquent pas un parcours navigateur complet contre des comptes réels de production. Le fonctionnement des services est testé séparément ci-dessous.

## Backend

- **245 tests existants réussis** dans une base PostgreSQL éphémère avec Redis réel.
- Les deux premiers nouveaux tests avaient une erreur d'import de fixture, corrigée puis retestée. La suite complémentaire finale contient **3 tests réussis** : droits enseignants, plafonds sur les indices, réponse publique d'exercice, relecture idempotente après réduction du plafond et suspension avant appel au fournisseur.
- Total : **248 tests backend distincts validés** ; les 5 tests Vitest et 5 scénarios navigateur s'ajoutent à ce total.
- Migration `0007_student_controls` : montée, comparaison avec les modèles, retour à zéro, réapplication et nouvelle comparaison réussis.
- Aucune donnée fictive de cette recette n'est insérée dans la base pédagogique active.

Les avertissements observés concernent les dépréciations Starlette/httpx/AnyIO, la couleur des logs Playwright et l'utilisation de `next start` pour la recette locale. Le conteneur de production exécute bien `node server.js` depuis la sortie standalone.


## Déploiement vérifié

- Frontend et services modifiés déployés ; page de connexion ouverte et vérifiée dans le navigateur intégré via le tunnel SSH.
- Les 15 services répondent et leurs contrats OpenAPI correspondent au dépôt.
- Contrôle HTTP du frontend réussi : connexion 200, redirection des pages privées, absence de session 401, origine interdite 403, route IA interne 404, CSP à nonce et absence de cache.
- Le proxy a été recréé pour reprendre le nouveau fichier monté ; un simple rechargement conservait l'ancien inode après extraction de l'archive.
- Sauvegarde et restauration isolée validées : `backups/educapilote-20260910T185356Z-3821482.sql.gz`, **54 tables**, dont 53 métier, révision `0007_student_controls`.

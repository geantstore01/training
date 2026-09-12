# Validation des modules 5 et 6

État vérifié le **10 septembre 2026 à 15:51 UTC**, VPS `192.168.1.10`, dépôt `/stockage/training`.

## Résultat livré

- `ai-router-service`, `retrieval-service` et `tutor-service` actifs, version API `0.6.0`.
- Les 15 services sont sains derrière Nginx ; leurs contrats OpenAPI actifs correspondent exactement aux fichiers du dépôt.
- Révision PostgreSQL `0005_ai_rag_tutor` : 45 tables métier, 46 avec `alembic_version`.
- Base active : aucun compte, document RAG ni tour de tuteur créé par les tests. Tous les scénarios métier ont utilisé des bases jetables.
- Les 15 fichiers de migrations antérieurs comparés à l'archive du module 4 sont inchangés.

## Tests

| Vérification | Résultat |
|---|---|
| Suite complète VPS, PostgreSQL/Redis réels, base isolée | **230 réussis**, aucun ignoré, 287,02 s |
| Suite IA ciblée après ajout des deux cas vecteur `null`/scalaire | **47 réussis**, 1,21 s sur VPS |
| Suite locale finale | **163 réussis**, 69 intégrations explicitement ignorées, 12,30 s |
| Cas distincts validés sur l'ensemble de ces exécutions | **232** |
| Migration neuve, comparaison SQLAlchemy | Réussies, aucun écart |
| Retour à zéro puis réapplication et comparaison | Réussis sur base isolée |
| Contrats actifs derrière le proxy | 15/15 conformes |
| Accès HTTP depuis tutor vers safety/retrieval/ai-router | 200/200/200 |

La suite complète comportait deux avertissements de dépréciation Starlette/httpx/AnyIO. L'exécution ciblée comportait un avertissement de cache Pytest sur le système de fichiers en lecture seule ; les tests ont tous réussi. Le script de suite complète désactive ce cache.

Couverture des nouveaux scénarios : consentements local/cloud, masquage avant transmission, refus socratique, niveaux 0–6, idempotence, requêtes concurrentes, effet de l'aide sur la maîtrise, sources archivées pendant un appel, séparation des tenants/niveaux/matières, branches lexicale et vectorielle, relecture indépendante, immutabilité, refus d'accès aux corrigés, SSRF, JSON fournisseur malformé, sources inventées, quotas HTTP, délais et circuit d'échec.

Les tests d'intégration emploient les vrais endpoints et les vraies bases avec rôles/RLS ; leurs téléchargements et réponses Ollama sont des doubles déterministes déclarés. Ils ne sont pas présentés comme des appels cloud réels.

## Vérifications externes réelles

Les appels suivants ont aussi été exécutés **dans les conteneurs déployés** :

- Ollama Cloud `gpt-oss:120b-cloud`, compte existant du daemon hôte : plan JSON validé, action et source conformes.
- Embeddings locaux `educapilote-embeddinggemma:v1` : **768 dimensions**. Alias du modèle existant, digest `85462619ee721b466c5927d109d4cb765861907d5417b9109caebc4e614679f1`.
- Téléchargement HTTPS du [PDF officiel de mathématiques](https://www.education.gouv.fr/sites/default/files/programme-de-math-matiques-pour-le-cycle-3-439827.pdf) : **527 151 octets**, SHA-256 `f3f79a75ca8be7f54409b8b7cee3eafd769c23d12e6c822a253454e2c703b508`.
- Extraction des pages physiques 5 et 6 : 8 passages ; deux passages effectivement encodés en vecteurs lors du smoke. Aucune publication ni approbation simulée dans la base active.

La liaison Ollama utilise la passerelle du backend `10.200.2.1`, inscrite par `scripts/configure_ollama_host.py` dans le `.env` du VPS. Le routeur conserve son réseau interne sans accès Internet direct. Le daemon Ollama assure son propre accès au compte cloud.

## Sauvegardes

Avant migration : `/stockage/training/backups/educapilote-20260910T154937Z-2838985.sql.gz`.

Après migration, sauvegarde et restauration complète vérifiées dans une base isolée : `/stockage/training/backups/educapilote-20260910T155032Z-2844558.sql.gz`. Contrôles de révision, propriétaires des 46 tables et graines CM1/CM2 réussis. La base de restauration a été supprimée par le script.

## Périmètre

Le tuteur choisit et rend des démarches pédagogiques contrôlées ; il ne transmet pas de réponse libre générée par le LLM. Le corpus destiné aux élèves reste vide jusqu'à l'import et la validation par des comptes humains autorisés. Le code, les contrats et les tests sont livrés ; la relecture du corpus ne peut pas être remplacée par une validation automatique de l'agent.

Voir [le guide d'utilisation](module56.md) pour les endpoints, les limites documentaires, les quotas, les modèles et les commandes reproductibles.

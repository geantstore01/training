# ÉDUCAPILOTE — ce que fait exactement la plateforme

ÉDUCAPILOTE est une plateforme d'apprentissage pour les élèves de CM1 et CM2. Elle aide l'élève à avancer dans les programmes du Cycle 3, sans classement public ni note anxiogène. L'établissement pilote les accès, l'enseignant construit les missions et les parents suivent le cheminement de leur enfant dans un cadre contrôlé.

## Les trois espaces

### Espace élève

Après connexion avec les accès fournis par l'établissement, l'élève arrive sur ses **missions du jour**. Une mission est préparée par l'enseignant pour toute la classe ou pour un groupe de niveau. Elle enchaîne : découverte, explication à partir d'une leçon validée, activité interactive, exercice guidé, exercice autonome, puis bilan.

La plateforme prend en charge les QCM, textes à compléter, réponses courtes ou numériques, problèmes à étapes, classements et frises chronologiques. Les réponses sont corrigées par des règles déterministes lorsque c'est possible : par exemple SymPy pour les mathématiques et des contrôles linguistiques pour le français. La correction ne repose pas simplement sur une réponse générée par une IA.

L'élève peut demander de l'aide à **Capitaine Savoir**. Ce tuteur ne donne pas directement la réponse aux devoirs. Il pose des questions et propose jusqu'à six niveaux d'aide, progressivement. Les explications se fondent uniquement sur des contenus officiels ou pédagogiques validés. L'enseignant peut réduire le niveau d'aide ou désactiver le tuteur pour un élève ; cette règle est vérifiée côté serveur.

La consigne d'un exercice validé peut être lue à voix haute par synthèse vocale française. L'audio est construit en mémoire et n'est pas conservé comme fichier temporaire. La transcription vocale n'est pas activée actuellement.

L'élève peut aussi consulter ses réglages de confidentialité et de confort de lecture. Les options de police DYS et d'agrandissement sont prévues. Les brouillons d'exercice restent dans la mémoire de la page : ils ne sont pas enregistrés dans le navigateur et peuvent être perdus si la page est fermée avant envoi.

### Espace parent

Un parent ne voit que les enfants dont le lien de responsabilité a été vérifié. Il peut consulter le temps estimé des séances closes, les compétences travaillées et leur état qualitatif : acquis, en apprentissage ou à retravailler. Il n'y a ni score public, ni classement entre élèves.

L'espace parent contient aussi les rapports hebdomadaires livrés dans une boîte de réception interne pendant 30 jours. Aucun e-mail n'est envoyé tant qu'un serveur SMTP n'a pas été configuré. Les suggestions d'activités à la maison sont générales et doivent être adaptées avec l'enseignant.

Les parents gèrent les consentements nécessaires à certains usages, notamment IA locale, IA Cloud et audio. L'enfant peut donner ou retirer son assentiment séparément. Les consentements sont historisés ; ils ne sont pas présélectionnés.

### Espace enseignant / établissement

L'enseignant crée et gère ses classes, inscrit les élèves déjà autorisés, forme des groupes et compose des missions avec des exercices publiés. Une mission peut être ciblée sur un groupe de niveau, puis archivée.

Le tableau de bord montre les compétences acquises, en apprentissage ou à retravailler, ainsi que des difficultés récurrentes. Il ne diffuse pas de probabilités de maîtrise, de notes ni de classement. Le temps affiché est une estimation calculée à partir des sessions closes, avec fusion des chevauchements et plafond par séance.

L'enseignant peut régler le cadre d'aide de chaque élève : suspendre l'aide IA ou plafonner les niveaux 0 à 6. L'administrateur d'établissement modère les contenus, consulte les événements de sécurité sans texte brut de conversation et pilote certains drapeaux de fonctionnalités.

## Comment une activité devient disponible

1. Les compétences sont organisées par matière, domaine, niveau CM1/CM2, objectifs, prérequis et erreurs fréquentes.
2. Les leçons, fiches et exercices sont versionnés.
3. Un contenu passe par les statuts `draft`, `pending_review`, `approved` ou `archived`.
4. Une validation humaine est obligatoire avant publication.
5. L'enseignant sélectionne uniquement les exercices publiés pour composer une mission.
6. L'élève reçoit la mission correspondant à sa classe ou son groupe.

Les évaluations conservent les tentatives et les erreurs récurrentes. Elles alimentent une estimation probabiliste interne de maîtrise et un moteur de répétition espacée. L'interface montre des formulations pédagogiques, pas une note chiffrée.

## Protection des données et sécurité

Chaque établissement est isolé par `school_id`. Les rôles sont élève, parent, enseignant, administrateur d'établissement, créateur de contenu et administrateur système. Les JWT sont courts, les refresh tokens tournent dans Redis et les droits sont revérifiés côté serveur.

Les profils utilisent des pseudonymes côté élève. Les informations personnelles sensibles sont chiffrées. Avant une transmission vers l'IA, le service de sécurité détecte et masque les éléments personnels tels que noms, école, adresse ou e-mail. Il applique aussi dix couches de contrôle contre les demandes de données personnelles, l'injection de prompt et les contenus dangereux ou inappropriés.

Le navigateur ne reçoit pas les JWT : il possède seulement un cookie de session opaque, `HttpOnly` et `SameSite=Strict`. Les jetons restent côté serveur dans Redis. Les réponses privées ne sont pas mises en cache, une CSP avec nonce protège les scripts et aucun outil publicitaire ou de suivi tiers n'est inclus.

Les consentements parentaux et l'assentiment de l'enfant sont requis avant l'IA ou la voix. Ils constituent des contrôles techniques ; ils ne remplacent pas les décisions juridiques du responsable de traitement, l'AIPD, les contrats avec les sous-traitants et les procédures complètes d'exercice des droits RGPD.

## IA et recherche documentaire

Le service RAG ingère des documents, les nettoie, les découpe en blocs pédagogiques, calcule des embeddings et les recherche avec PostgreSQL plein texte et pgvector. Les résultats sont filtrés par niveau, matière et validation humaine.

Le routeur IA utilise l'Ollama hôte déjà connecté au compte Cloud pour le modèle `gpt-oss:120b-cloud`; les embeddings sont locaux. Avant un appel Cloud, les sources sont validées, les données personnelles sont masquées, les consentements sont contrôlés et un quota d'appels par établissement est appliqué. Les erreurs fournisseur n'exposent pas son contenu. Le système garde les métadonnées utiles — code, modèle, durée, tokens et sources — sans conserver les messages bruts dans les traces d'exploitation.

Un profil Ollama local GPU existe également. Il est optionnel, utilise une RTX 4070 de 12 Go lorsqu'il est lancé et ne télécharge pas automatiquement de modèle ni d'identifiants Cloud.

## Traitements en arrière-plan

Un worker durable et Redis traitent les rapports hebdomadaires, alertes de difficulté, lots d'exercices et purges. Les tâches sont idempotentes et réessayées au plus cinq fois. Les workflows n8n correspondants sont livrés mais inactifs, sans secrets ni données d'exécution enregistrées.

Les rapports parentaux et alertes d'enseignants restent dans la boîte interne. Les alertes concernent notamment des difficultés répétées ou des demandes d'aide élevée ; elles ne révèlent pas de note.

## Exploitation sur le VPS

La plateforme comprend 15 microservices FastAPI, un frontend Next.js, PostgreSQL 17 avec pgvector, Redis, un reverse proxy et des conteneurs isolés. Les données PostgreSQL et Redis sont persistantes. Les services sont démarrés après les migrations Alembic, possèdent des comptes de base distincts et tournent avec système de fichiers en lecture seule lorsque possible.

Prometheus et Grafana mesurent disponibilité, latence, 5xx, CPU, mémoire, disque, GPU, appels IA, tokens et âge des sauvegardes. Loki reçoit uniquement des journaux techniques filtrés : service, route gabarit, méthode, statut, durée et identifiant technique aléatoire. Il ne reçoit ni conversation, ni adresse IP, ni cookie, ni jeton, ni adresse e-mail. Sentry est désactivé tant qu'un DSN n'est pas défini ; s'il est activé, il ne reçoit que les erreurs 5xx sous une forme reconstruite et limitée.

Les sauvegardes PostgreSQL sont compressées puis chiffrées avec `age`, avec checksum et restauration uniquement dans une base isolée. La rétention locale est de 14 jours pour les backups chiffrés, 15 jours pour Prometheus et 7 jours pour Loki et les logs techniques. Une copie chiffrée hors site reste à organiser avant une ouverture réelle.

## Ce qui n'est pas encore activé ou certifié

- Le domaine public et le certificat Let's Encrypt ne sont pas configurés ; l'accès actuel est privé sur le VPS.
- Le DSN Sentry n'est pas fourni : aucun événement n'est envoyé à Sentry.
- L'envoi d'e-mails n'est pas configuré ; les notifications sont internes.
- La transcription vocale n'est pas active.
- Les tests automatisés ne constituent pas une certification RGPD, OWASP ou WCAG, ni un audit indépendant.
- L'AIPD, la validation DPO/responsable de traitement, les contrats Cloud et la sauvegarde hors site restent nécessaires avant ouverture à des mineurs.

## Carte interactive

La page [educapilote-architecture-3d.html](educapilote-architecture-3d.html) présente les flux de la plateforme en 3D. Elle utilise **Three.js** (interprétation de « treed.js ») et charge la bibliothèque depuis un CDN ; une connexion Internet est donc nécessaire pour afficher la visualisation.

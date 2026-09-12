# Checklist de mise en production — ÉDUCAPILOTE

Les statuts « testé » renvoient aux rapports de tests ; ils ne constituent pas une
certification OWASP, WCAG ou RGPD. Les points « à valider » sont des conditions
de recette, pas des garanties implicites. Nommer un responsable et dater chaque
validation avant d'accueillir des mineurs.

## Sécurité applicative — lecture inspirée OWASP ASVS

Référence : [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/).
Cette sélection opérationnelle n'est pas une évaluation exhaustive de toutes les
exigences ASVS ni une attestation d'un niveau de conformité.

| Contrôle | Preuve / validation attendue |
|---|---|
| JWT courts, rotation refresh, rejeu, révocation | Tests auth existants, suite PostgreSQL/Redis isolée |
| Autorisations objet / multi-tenant | Tests RLS, gardiens vérifiés, enseignants affectés, administration |
| Cookies, CSRF et BFF | Tests module 9/10 ; Secure en HTTPS public à valider après certificat |
| Réponses privées / corrections | Tests d'absence de réponses dans les DTO élèves et routes BFF |
| Injection et contenus IA | Scénarios safety/tutor ; pas de preuve de blocage universel des LLM |
| Secrets hors dépôt / images | Exclusions et fichiers protégés ; coffre/rotation opérateur à valider |
| Surface réseau | Monitoring loopback, API privées, aucun socket Docker ; audit pare-feu/NAT à valider |
| Logs et données sensibles | Tests module 11 sur corps, jetons et identités ; inspection des erreurs runtime |
| TLS reconnu, renouvellement | À valider avec domaine public, ACME production et test de renouvellement |
| Vulnérabilités de dépendances/images | Digests figés ; scan CVE complet et traitement des findings à valider |
| Compromission / reprise | Test backup/restauration isolée ; exercice de reprise complet à planifier |
| Pentest indépendant | À valider ; aucun pentest externe réalisé par ce module |

## RGPD et protection des mineurs

| Décision / contrôle | Statut attendu avant ouverture |
|---|---|
| Responsable de traitement, DPO, finalités et registre | À renseigner et approuver |
| Base légale de chaque traitement | À décider avec le responsable ; le consentement technique ne tranche pas la base légale scolaire |
| AIPD, risques enfants/profilage/IA et mesures résiduelles | À réaliser/valider avec DPO ; le code ne vaut pas AIPD |
| Information compréhensible par l'enfant et les parents | À relire et tester avec le public cible |
| Lien gardien, consentements append-only et assentiment | Tests fonctionnels existants ; vérification réelle de qualité du représentant à organiser |
| Suspension IA / limitation d'aide par enseignant | Tests module 9/10 et contrôle côté serveur |
| Localisation, sous-traitants Ollama Cloud/Sentry et transferts | Contrats, région et garanties à valider avant activation correspondante |
| Minimisation et télémétrie | Journaux techniques filtrés, aucune conversation dans Sentry ; rétention bornée |
| Durées métier et purge | Purges existantes ; politique finale à approuver selon finalités et obligations |
| Accès, export, rectification, effacement complet | Parcours opérationnel complet à valider ; la purge d'expiration n'est pas un effacement de compte exhaustif |
| Effacement après restauration | Registre des demandes et rejeu après reprise à organiser |
| Copies hors site et clés de chiffrement | Destination, coffre et restauration hors VPS à valider |
| Gestion de violation / information des personnes | Procédure, contacts et exercice à valider avec DPO |
| Absence de classement anxiogène | Interfaces qualitatives testées ; évaluation pédagogique humaine à finaliser |

La CNIL souligne les risques liés aux personnes vulnérables, à l'usage innovant et
à l'évaluation/profilage dans l'éducation : [référence](https://www.cnil.fr/fr/education-mise-en-place-systeme-ia).
Le périmètre exact de l'AIPD et les choix juridiques appartiennent au responsable
de traitement : [méthode CNIL](https://www.cnil.fr/fr/realiser-une-analyse-dimpact-si-necessaire).

## Recette end-to-end

| Parcours | Automatisation existante | Recette publique à compléter |
|---|---|---|
| Connexion, expiration et déconnexion | Auth/Redis + BFF + Playwright | HTTPS réel et cookie Secure |
| Mission → activité → correction | Tests backend + frontend avec serveur de test explicitement fictif | Jeux de contenus approuvés et comptes dédiés |
| Tuteur, aides 0–6, refus réponse directe | Scénarios contrôlés et smoke IA antérieurs | Recette pédagogique enseignant |
| Parent : enfant autorisé, rapport, confidentialité | Contrats et scénarios module 10 | Compte parent réel de recette, retrait consentement |
| Enseignant : groupe, mission, désactivation IA | Contrôle serveur et UI testés | Classe de recette et cas simultanés |
| Audio : lecture/arrêt/consentement | Service et UI testés | Appareils et lecteurs d'écran ciblés |
| Accessibilité | Axe sur écrans testés module 9/10 | Audit humain WCAG AA, DYS, clavier et lecteur d'écran |
| Erreurs 5xx, perte DB/Redis, alerte | Compteurs et règles validables sans couper la production | Exercice de panne en environnement de recette |
| Backup chiffré / restauration | Test isolé module 11 | Reprise hors VPS et mesure RTO à volume réaliste |
| Charge / GPU / concurrence | Métriques disponibles | Test de charge et seuils adaptés au nombre d'élèves |

Décision d'ouverture : responsable technique ______ ; responsable pédagogique
______ ; responsable de traitement/DPO ______ ; date ______ ; réserves ______.

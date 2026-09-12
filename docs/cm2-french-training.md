# Français CM2 : ce qui est implémenté

Le parcours existant contient maintenant **28 micro-leçons et 84 exercices** de français.
Le contenu est original et lié au catalogue pédagogique. Les cinq dépôts ont été
examinés ; deux fournissent des données effectivement importées, trois ont servi
à adapter des mécanismes pédagogiques. Les cinq applications ne sont pas installées
comme services distants. Aucun modèle n'a été entraîné sur les réponses d'enfants.

## Périmètre pédagogique

| Domaine | Leçons disponibles |
|---|---|
| Grammaire | Classe/fonction, sujet inversé, COD/COI, attribut, phrase simple/complexe, circonstances, pronoms, expansions du nom |
| Conjugaison | Présent d'être, imparfait d'avoir, futur d'aller, passé composé, passé simple et plus-que-parfait de chanter |
| Orthographe | Accords du groupe nominal, a/à, on/ont, participe passé avec être, relecture de phrases par catégories |
| Lexique | Familles de mots, choix du sens par le contexte, synonymes, antonymes, dictionnaire |
| Lecture | Déduction et justification, enquête de lecture, ordre des événements |
| Écriture | Présenter un personnage, enchaîner des actions, écrire une fin, résumer et relire |

Chaque leçon suit : situation concrète, objectif fourni, prérequis, explication,
méthode, exemple résolu, erreur fréquente, mini-question et deux exercices.
Le lecteur avance par étapes. Chaque exercice présente une seule question ;
la justification peut être écrite ou expliquée à voix haute à un adulte.
Les deux indices sont progressifs et écrits à l'avance. Les erreurs connues
déclenchent un indice ciblé, notamment pour classe/fonction et a/à.

L'accueil « L'atelier des mots » propose six domaines, des filtres et une recherche
qui accepte les mots avec ou sans accents. Une phrase interactive explique le rôle
de ses trois groupes. Les exercices du dictionnaire et de lecture permettent de
déplacer des éléments, à la souris ou avec des boutons accessibles au clavier ;
leur ordre est vérifié par le correcteur existant. Les consignes ne sont plus
répétées trois fois au-dessus des champs. Aucun compteur de maîtrise fictif ou
récompense simulée n'est affiché. L'interface est adaptée au téléphone.

Les nouvelles activités sont aussi rapprochées des
[ressources Éduscol de français cycle 3](https://eduscol.education.gouv.fr/4800/ressources-d-accompagnement-du-programme-de-francais-au-cycle-3)
et de celles sur
[l'étude de la langue](https://eduscol.education.gouv.fr/4809/ressources-d-accompagnement-du-programme-de-francais-aux-cycles-2-et-3-etude-de-la-langue).
Le document joint est traité comme une proposition d'organisation, pas comme une
transcription officielle : ses numéros de page d'exemple ne sont pas repris comme
références vérifiées. Aucun ajout de prédicat ou d'impératif n'est fait sur cette
seule base. Les dix nouveaux ateliers sont des contenus originaux ; aucune nouvelle
intégration de LanguageTool, Lexique 3 ou des autres dépôts cités n'est prétendue.

Le référentiel principal est le [programme français de cycle 3 publié au BO du 17 avril 2025](https://www.education.gouv.fr/bo/2025/Hebdo16/MENE2504620A),
applicable au CM2 à la rentrée 2026. Les points travaillés ont été confrontés au
[texte du programme de français](https://www.education.gouv.fr/sites/default/files/programme-de-fran-ais-pour-le-cycle-3-439824.pdf),
notamment les parties lecture, écriture, vocabulaire, grammaire et orthographe CM2.
Les objectifs et codes CM2-FR-* sont des formulations et identifiants internes,
pas des citations ni des identifiants ministériels.

Ce n'est pas un programme annuel complet : notamment, l'oral, la lecture longue,
la fluence, tous les verbes irréguliers et tous les accords du participe passé
ne sont pas couverts par ces exercices. L'activité de relecture n'est **pas une
dictée audio**. Une dictée peut être lue par un adulte ; l'aperçu ne simule pas
une reconnaissance vocale ou une notation de la prononciation.

## Apports exacts des dépôts

| Dépôt examiné | Utilisation dans cette version | Limite retenue |
|---|---|---|
| [GPT-language/gpt-tutor](https://github.com/GPT-language/gpt-tutor/tree/ec19ad1101a2436dae99d2f8b110c0d32b3fc2f3) | Séparation entre rôle pédagogique, commande et actions guidées. Le prompt français est injecté dans le planificateur du tuteur existant ; les textes destinés à l'enfant restent contrôlés. | Source AGPL-3.0 : aucun code recopié. Pas d'installation de son extension ni de son serveur. |
| [French-exercise-site](https://github.com/aadilmallick/French-exercise-site/tree/4ffccc4092b9f8d7356e664c5b2e5360a8b603ec) | Structure question/réponse/explication et retour après essai, adaptée au parcours CM2 et aux réponses libres à relire. | Pas de licence trouvée à la racine examinée ; pas de copie du code ou des exercices. Son fichier example-exercises.json contient de l'espagnol : contenu non importé. |
| [Conjugaison-Francais](https://github.com/dspodina/Conjugaison-Francais/tree/bfa0ff9f8d9e36d778393294ad13719723d0255d) | Principe du triplet verbe–sujet–temps, ici avec mode explicite, sélection finie et difficulté progressive. | Pas de licence trouvée à la racine examinée ; pas de code copié ni d'appel RapidAPI. Le conditionnel proposé par le dépôt n'est pas ajouté au corpus CM2. |
| [french-verbs](https://github.com/andrewmcc/french-verbs/tree/135c2a6dd3de262d72c1e27ff6f5a3cd136044ce) | Données de conjugaison comparées à WordWeaver, puis importées dans la table utilisée par le correcteur. | MIT, notice conservée. Son acceptation des réponses sans accents n'est pas reproduite. |
| [WordWeaverLite](https://github.com/WordWeaverTools/WordWeaverLite/tree/9ed1d460601bca89589433941a1c03a98d9b02b9) | Données structurées mode–temps–sujet utilisées pour recouper les formes ; table de formes autorisées à l'exécution. | MIT, notice conservée. Formes tronquées ou divergentes exclues. |

L'importeur compare 72 cases concernant être, avoir, aller et faire au présent,
à l'imparfait et au futur. **47 formes concordent ; 25 divergences sont exclues**,
avec leur détail conservé. Cela ne signifie pas que 72 formes importées sont valides.
Des ajouts originaux explicites complètent le petit corpus de chanter et la forme
êtes, sans inventer des conjugaisons pour les verbes inconnus.

Fichiers de provenance : `shared/exercises/data/french_verbs.json`,
`LICENSE-french-verbs.txt` et `LICENSE-wordweaver.txt` dans le même dossier.
L'import se reproduit avec `python -m scripts.import_french_verb_sources`, à partir
des deux dépôts clonés dans les répertoires indiqués par le script et aux commits
ci-dessus. Il ne lance pas leur code applicatif.

## Ce que le serveur garantit

- Le prompt fourni est dans `shared/ai/french_policy.py` et sélectionné seulement
  pour les appels français CM2. L'IA choisit une action bornée ; elle ne rédige pas
  librement des règles grammaticales ou des corrections pour l'enfant.
- La leçon doit reprendre l'objectif de son contexte, son niveau et sa matière.
  L'export refuse un objectif incompatible ; la publication vérifie les exercices
  réellement publiés et liés aux mêmes compétences.
- `GET /attempts/{id}/correction` exige un essai enregistré et ne révèle que les
  parties tentées. `POST` avec `{"explicit":true}` permet la correction sur demande
  pour un exercice **entièrement français CM2**, après contrôle côté serveur.
  Une correction demandée avant l'essai marque celui-ci comme aidé. Les mathématiques
  conservent leur exigence d'une première tentative.
- Les réponses et règles privées ne sont pas dans les données publiques des exercices.
- Les conjugaisons sont contrôlées par sujet/personne, indicatif, temps et forme attendue.
  Une forme incohérente est refusée par le validateur éditorial. Les accents sont
  conservés ; une différence de casse seule n'est pas une faute de conjugaison.
- Une réponse libre n'est jamais notée par comparaison à une unique phrase modèle.
  Elle porte le statut **à relire**, sa correction est intitulée **exemple possible**,
  et elle ne reçoit pas de score automatique. Elle n'abaisse ni la maîtrise ni un
  calendrier de révision déjà acquis. Elle ne figure pas dans les erreurs récurrentes.
- La relecture prend en charge les catégories accord, conjugaison, homophone, lexique
  et orthographe lexicale grâce à des repères éditoriaux. Si les mots ont été ajoutés,
  supprimés ou modifiés hors des repères, une relecture humaine est demandée.
  La casse et la ponctuation ne sont pas évaluées automatiquement dans ce mode.
- Si le tuteur ne dispose pas de source validée, il répond :
  « Cette notion n'est pas suffisamment décrite dans mon cours CM2. »
- Aucune donnée personnelle supplémentaire n'est demandée. En production, la
  justification utilise le stockage chiffré des réponses déjà en place.

Le correcteur libre ne juge pas le sens d'une rédaction, et la demande de
justification n'est pas une évaluation automatisée de cette justification.
La relecture humaine des contenus et des productions reste nécessaire.

## Mise en place et vérification

La migration `0012_cm2_french_training` ajoute la nouvelle version du catalogue
et rejoint les deux branches 0011 existantes. Elle conserve les anciens contenus.
Son retour arrière conserve les compétences pour ne pas casser les références
des contenus publiés. Le SQL peut être régénéré avec
`python -m scripts.build_french_catalogue`.

La migration `0013_cm2_french_workshops` ajoute séparément les dix nouveaux
objectifs. Le générateur conserve le SQL des dix-huit premiers objectifs et
produit celui des dix nouveaux dans le fichier 0013.

Pour préparer les contenus de l'établissement, fournir son catalogue actif et
ses véritables identifiants de sources :

```powershell
.venv/Scripts/python.exe -m scripts.export_cm2_training --subject francais --catalogue catalogue-francais.json --source-id <UUID-source> --output exercices-francais.json
```

Le résultat contient des candidats pour le circuit éditorial existant, pas de
fausses signatures de validation. Après publication des exercices, fournir
`--published exercices-publies.json` (code → trois UUID de versions) pour exporter
les leçons liées. Aucune publication distante n'est effectuée par cet exporteur.

L'aperçu `http://127.0.0.1:19093/tests/cm2-preview/` présente les deux matières
avec les vrais contenus, le vrai correcteur et le composant élève. Il utilise des
identifiants de démonstration et des essais éphémères. Il n'utilise ni PostgreSQL
ni IA distante et ne vaut pas déploiement en établissement.

Tests exécutés : 39 contrôles Python propres au français (contenus, import,
accents, correction, périmètre CM2, conservation de la maîtrise), suite Python
existante (245 tests Python réussis au total), 5 tests d'interface unitaires,
6 parcours navigateur maths/français,
contrôle d'accessibilité mobile et compilation Next.js. Les tests nécessitant
PostgreSQL/Redis sont ignorés sans l'environnement Compose ; ils ne sont pas
présentés comme réussis. Les services authentifiés et le fournisseur IA n'ont
pas été testés de bout en bout dans cet environnement local.

## Installation effective sur BoostClasse — 11 septembre 2026

Les 28 ateliers décrits ci-dessus et leurs 84 exercices sont désormais enregistrés dans la base du VPS. Ils sont attribués au compte créateur existant, en attente de relecture. Le script `scripts/stage_french_courses.py` a été exécuté deux fois : 84 exercices créés au premier passage, zéro au second. Les cours déjà approuvés sont conservés.

La source PDF officielle de français a été téléchargée (21 pages) et enregistrée avec SHA-256 `e7c27f55c212b5ebb92ba8b60b6b1b0761a2301e7c0d0d780171c4cfb6e121ae`. Les cartes anciennes ne sont pas une preuve que les nouveaux cours étaient publiés : c’était la cause du message « en préparation ».

Dans `/enseignant`, le bouton **Relire et publier les parcours de français** affiche les 28 dossiers complets : objectif, prérequis, découverte, explication, méthode, exemple, erreurs, trois exercices, indices et corrections. Le compte administrateur peut consulter ; un enseignant indépendant de l’auteur, tel que `prof.master`, peut confirmer sa relecture et publier un parcours. Le bouton ne devient actif qu’après ouverture des exercices et confirmation explicite. Chaque validation est signée par la session réelle, via les API éditoriales existantes. Aucun avis humain n’a été fabriqué par l’import.

La publication des trois exercices précède celle de la leçon ; le serveur vérifie à nouveau leurs liens et leur statut. Une interruption peut être reprise sans publier deux fois les exercices déjà validés. Les brouillons et leurs réponses restent interdits aux élèves.

Ce travail installe les 28 modules annoncés ; il ne prétend pas transformer ces micro-leçons en un programme annuel exhaustif avec toutes les œuvres, toutes les conjugaisons et toutes les activités orales.

## Publication demandée par le propriétaire — 11 septembre 2026

Cette section remplace le statut « en attente de relecture » indiqué plus haut. Les 28 parcours et 84 exercices ont été publiés sur demande explicite du propriétaire, avec 112 traces `operator.owner_publication` distinctes des avis humains. Aucun avis de professeur n’a été fabriqué. La migration 0017 permet cette opération seulement au compte PostgreSQL opérateur, sur les versions identifiées par un audit préalable ; les comptes applicatifs n’obtiennent pas ce droit. Les autres contrôles de structure, immutabilité, tenant et réponses privées sont conservés.

L’accès `prof.master` est désactivé, ses sessions invalidées. Les données et historiques sont conservés. `/enseignant` redirige vers `/administration`, où l’administrateur consulte les cours publiés. L’élève reste sur `/eleve`. La bibliothèque ne compte que les compétences disposant d’une leçon publiée et d’exercices publiés.

Vérification effective sur `https://boostclasse.com` avec le compte élève : les 28 cours et les 84 exercices répondent et contiennent leur contenu ; les réponses privées ne figurent pas dans les données publiques. Les tests isolés couvrent publication idempotente sans création de faux avis humains et protection des brouillons. Le parcours attribut du sujet a été ouvert dans le navigateur intégré.

# Dépôts examinés et intégrations

Audit du 11 septembre 2026. L’intégration ne transforme aucune banque de questions en référentiel officiel.

| Dépôt | Révision examinée | Utilisation effective |
| --- | --- | --- |
| https://github.com/HKUDS/DeepTutor | `2e0816b090b298a91bc5cceca9ac8d73ce6dbaa6` | Découpeur `deeptutor/services/memory/consolidator/chunker.py` repris sans modification fonctionnelle dans `shared/history/vendor`. Il sert réellement à l’ingestion d’histoire. Licence Apache-2.0 jointe. Le moteur complet et ses agents ne sont pas installés. |
| https://github.com/mawoka-myblock/classquiz | `711bdde7a7dcd2d217cfc75dbbbb2592a78582d3` | Contrat `QuizInput` déjà intégré en sciences, sous MPL-2.0 ; les six exports d’histoire passent ce véritable schéma. Le serveur de parties multijoueurs n’est pas installé. |
| https://github.com/K41R0N/Interactive-Quiz-Maker | `0df11545fbb40280a2c0f2fc6a2f8a1243abb427` | Export JSON compatible avec son validateur : `title`, `questions`, `question`, `options`, `correct_answer`, `explanation`. Aucun code ou fichier graphique copié. README annonçant MIT, pas de fichier LICENSE dans la révision inspectée. |
| https://github.com/pwenker/quizli | `d6538b13c16c093935ac2d0f175ac041aa5be4ef` | Export CSV deux colonnes sans en-tête compatible avec `Quiz.from_csv`. MIT indiqué dans pyproject.toml ; aucun code copié. Son mode « sudden death » n’est pas repris pour les enfants. |
| https://github.com/Ethra8/history-quiz | `70e89acc536832a86235fa6a2153a3ced5aa0e68` | Inspiration de navigation thématique uniquement. Pas de licence explicite inspectée ; pas de code ni de banque de questions repris. Ses anecdotes générales ne sont pas un corpus CM2 vérifié. |
| https://zenodo.org/records/19447087 | archive `rag-tutor-v1.0.0`, DOI `10.5281/zenodo.19447087` | Archive du même projet KiavashBahreini7/rag-tutor déjà examiné pour les sciences, sous CC BY 4.0. Inspiration du questionnement socratique et de la réflexion de fin de séance ; aucun service Gemini ni clé navigateur ajouté. |

DeepTutor était cité deux fois : une seule intégration est faite. Le RAG pgvector, les accès par école et les validations humaines restent ceux d’Éducapilote. Les exports contiennent des réponses destinées à l’enseignant ; ils ne sont pas servis par le catalogue élève et ne sont pas téléversés automatiquement chez un tiers.

Pour régénérer les exports : `python -m scripts.export_history_review`. Les notices de ClassQuiz se trouvent dans `shared/science/vendor`, celles de DeepTutor dans `shared/history/vendor`.

# Provenance des dépôts sciences

Audit local du 11 septembre 2026. Révisions lues sans exécuter les applications des dépôts.

| Dépôt | Commit consulté | Licence et décision |
|---|---|---|
| ScienceGear/SparkSTEM | `5976d4ad9a7bc38145f5b25bb4435751b8343f60` | Pas de licence racine trouvée. README et `frontend/src/simulations/simulationConfig.ts` examinés. Inspiration uniquement. |
| KiavashBahreini7/rag-tutor | `cd8152a8d233688eb29901ee673b69bab7c4c8ef` | CC BY 4.0, Dr Kiavash Bahreini / Florida International University, 2026. `RAG_Tutor.html` examiné : conversation socratique et réflexion. Pas de copie de code ni des comptes ou clés en stockage navigateur. |
| openzim/phet | `4015ae6d0e9df311d4a9551b0263f0f5a51c326a` | Apache-2.0. Interface CLI documentée utilisée pour produire un plan optionnel ; aucun exécutable embarqué. |
| mawoka-myblock/classquiz | `711bdde7a7dcd2d217cfc75dbbbb2592a78582d3` | MPL-2.0. Sept classes extraites de `classquiz/db/models.py`, conservées dans `shared/science/vendor/classquiz_contract.py`. Imports réduits ; classes inchangées. Notice et licence intégrales conservées à côté du fichier. |
| joelgrus/science-questions | `6fab16a43efc415f2f1509ab0a269d7a8a88cbd8` | Unlicense. Corpus exclu pour sa nature volontairement absurde, indépendamment de la licence. |
| reneenoble/ai-rag-for-education | `78e9bc7558b1aac055aa16e9245fa9e88cf8755d` | MIT, Renee Noble, 2024. `get_search_summary` adapté dans `shared/science/retrieval.py` : segmentation Unicode, filtrage CM2/sciences/approuvé, mots entiers et limites. Aucun corpus publicitaire ni appel fournisseur repris. |
| phetsims | Organisation GitHub | Pas de révision unique. Le lien du circuit est servi par PhET Interactive Simulations, University of Colorado Boulder. Sa version `latest` reste externe et peut évoluer. Les droits de redistribution doivent être vérifiés avant un éventuel hébergement local. |

Références amont : [SparkSTEM](https://github.com/ScienceGear/SparkSTEM), [rag-tutor](https://github.com/KiavashBahreini7/rag-tutor), [openZIM](https://github.com/openzim/phet), [ClassQuiz](https://github.com/mawoka-myblock/classquiz), [science-questions](https://github.com/joelgrus/science-questions), [Renee Noble](https://github.com/reneenoble/ai-rag-for-education), [PhET](https://github.com/phetsims).

## Licence MIT de la recherche adaptée

Copyright (c) 2024 Renee Noble

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

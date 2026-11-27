# Veille – Bonnes pratiques RAG multimodal pour MaintiDoc

Équipe ELFAROUKI-HAFFARI-LOKSAIRI – Livrable 2 – novembre 2026

## 1. Méthode

**Questions de départ.** Comment découper nos manuels (pages, tableaux, figures) ? Faut-il combiner
plusieurs recherches et comment fusionner leurs résultats ? Comment retrouver une figure à partir d'une
question en français ou d'une photo ? Où appliquer le contrôle d'accès ? Comment mesurer la qualité de la
recherche avant d'avoir un générateur ?

**Outils.** Moteur de recherche web, documentation officielle (Qdrant), arXiv / ACL Anthology pour les
articles, et un assistant IA (Claude) pour proposer des pistes et des requêtes. Chaque source retenue a été
ouverte et lue ; une piste non retrouvée dans une source primaire n'a pas été conservée.

**Période.** 26 au 27 novembre 2026. **Critères** : sources publiées ou mises à jour depuis 2023,
priorité aux sources primaires (documentation officielle, articles). 9 sources retenues, dont 7 primaires.

## 2. Fiches thématiques

### Fiche 1 – Découpage des documents

**Problème.** Un passage trop long mélange plusieurs sujets et dilue son embedding ; trop court, il perd
son contexte. Un découpage aveugle coupe aussi les tableaux et sépare une figure de sa légende.

**Approches.** Découpage en blocs de taille fixe (tokens) avec chevauchement ; découpage récursif sur la
ponctuation ; découpage **structurel** selon les éléments du document (titres, paragraphes, tableaux,
figures). Sur des rapports financiers, le découpage par type d'élément améliore nettement les résultats
du RAG par rapport au découpage par paragraphes ou par taille fixe [S7].

**Avantages / limites.** Le découpage structurel produit des unités cohérentes et des citations précises,
mais dépend de la qualité de l'analyse de mise en page ; la taille fixe est simple mais coupe arbitrairement.

**Pour MaintiDoc.** Nos manuels ont un chapitre par page et des tableaux et figures numérotés. Nous
découpons donc d'abord par page et par élément (passage, tableau en Markdown, figure avec sa légende),
puis les passages en ~900 caractères (≈ 200-250 tokens) avec 150 caractères de chevauchement. Un
passage ne traverse jamais deux pages, pour que la citation « document + page » reste exacte.
**Appliqué.**

### Fiche 2 – Recherche hybride et fusion des résultats

**Problème.** Une recherche dense trouve les paraphrases mais peut manquer un identifiant exact
(« C-07 », « POMPE-C-03 ») ; une recherche lexicale fait l'inverse. Combiner plusieurs listes demande une
règle de fusion, car leurs scores ne sont pas comparables.

**Approches.** Recherche dense + lexicale (BM25 ou vecteurs creux) fusionnées. La Reciprocal Rank Fusion
n'utilise que le rang de chaque document dans chaque liste, ce qui permet de combiner des scores
hétérogènes sans les comparer [S2] ; Qdrant la propose nativement, avec des poids par liste [S2]. BGE-M3
produit à la fois des vecteurs denses, creux et multi-vecteurs avec un même modèle [S4].

**Avantages / limites.** La fusion est robuste et sans apprentissage, mais elle n'est pas toujours
gagnante : dans le guide de réglage de Qdrant, la fusion bat le meilleur système seul sur quatre jeux de
données sur cinq, d'où le conseil de mesurer plutôt que de supposer [S3].

**Pour MaintiDoc.** Nous fusionnons par RRF la liste texte (BGE-M3) et les listes visuelles. Notre première
version à poids égaux faisait **baisser** le Recall@5 (0,83 contre 0,94 en texte seul) : nous avons
pondéré les listes visuelles (0,5) et limité leurs candidats (5), ce qui ramène le Recall@5 à 0,94. La
recherche lexicale / creuse sur les codes d'alarme est **reportée en semaine 5** ; en attendant, les
identifiants lus sur la photo sont ajoutés à la requête.

### Fiche 3 – Recherche multimodale

**Problème.** Les réponses sont souvent dans un schéma, un tableau de voyants ou une photo de panneau,
qu'un index purement textuel ne voit pas, et le technicien envoie une photo plutôt qu'un texte.

**Approches.** (a) Encodeur texte-image de type CLIP qui place images et textes dans le même espace ;
les modèles OpenCLIP entraînés sur LAION sont ouverts et reproductibles, et ils sont meilleurs que le CLIP
d'OpenAI en recherche d'images [S9]. (b) Description des images par un modèle vision-langage, puis
indexation du texte. (c) Recherche directe sur l'image des pages avec un VLM et interaction tardive
(ColPali), qui dépasse les chaînes classiques d'extraction sur les documents visuellement riches [S5].

**Avantages / limites.** (a) est léger et tourne sur CPU, mais l'encodeur compare des formes et des
couleurs et ne « lit » pas les détails ; (b) est coûteux à l'ingestion ; (c) est très performant mais
demande un VLM de plusieurs milliards de paramètres, irréaliste sans GPU.

**Pour MaintiDoc.** Option (a), avec un encodeur multilingue choisi par benchmark : OpenCLIP
XLM-RoBERTa retrouve 15 requêtes visuelles françaises sur 20, contre 12 pour le CLIP multilingue de
sentence-transformers. Nous ajoutons l'OCR des photos (RapidOCR) pour récupérer les codes affichés.
**Appliqué.** ColPali est **écarté** au livrable 2 (pas de GPU) ; la description des figures par le VLM est
**reportée en semaine 3**.

### Fiche 4 – Métadonnées et contrôle d'accès

**Problème.** Un RAG ne doit jamais faire remonter un document qu'un utilisateur n'a pas le droit de
lire, ni dans les résultats, ni dans les extraits, ni dans les images affichées.

**Approches.** Filtrer avant la recherche (pré-filtrage), après (post-filtrage), ou pendant. Qdrant
recommande de filtrer **pendant** la recherche, sur des champs de la charge utile munis d'un index
(« payload index ») de type keyword, son index HNSW filtrable évitant les défauts du pré- et du
post-filtrage [S1].

**Avantages / limites.** Le post-filtrage peut renvoyer moins de k résultats et laisse transiter les
documents interdits dans la chaîne ; le filtrage pendant la recherche est sûr et efficace, à condition que
chaque élément porte ses groupes d'accès.

**Pour MaintiDoc.** Chaque élément porte `groupes_acces` (repris de l'inventaire), indexé en keyword ; le
filtre « groupes de l'utilisateur » est passé à chaque requête Qdrant (texte, texte→image, photo→image), et
l'ouverture d'une image ou d'une page revérifie les droits. 10 tests automatiques le démontrent, et ils
échouent bien si l'on retire le filtre. **Appliqué.**

### Fiche 5 – Évaluation

**Problème.** Sans mesure, impossible de savoir si un réglage aide ou nuit.

**Approches.** Pour la recherche : jeu de questions annotées et mesures de rang (Recall@k, MRR, nDCG)
[S3]. Pour la réponse générée : métriques sans référence humaine, comme la fidélité au contexte et la
pertinence de la réponse et du contexte, proposées par RAGAS [S8].

**Avantages / limites.** Les mesures de rang sont simples et reproductibles, mais dépendent de la
qualité des annotations ; RAGAS évalue la génération mais s'appuie sur un modèle juge.

**Pour MaintiDoc.** 20 questions annotées (document + page), Recall@5 et MRR@10 calculés par script pour
les deux configurations. **Appliqué.** L'évaluation de la génération (fidélité, citations) est **reportée en
semaine 5**.

### Complément – En-tête contextuel des passages

Un passage isolé perd souvent l'information sur son document. Anthropic propose d'ajouter un court
contexte propre à chaque passage avant de calculer son embedding et son index lexical ; combinées, les
deux techniques réduisent de 49 % les échecs de recherche dans leurs essais [S6]. Nous appliquons une
version **déterministe** (sans modèle de langage) : titre du document, identifiant, page et identifiants
d'équipement sont ajoutés avant l'embedding. C'est ce qui a permis de retrouver la question Q08
(« POMPE-C-03 »), qui échouait auparavant. **Appliqué.**

## 3. Tableau de synthèse

| # | Bonne pratique | Sources | Décision | Justification pour MaintiDoc |
|---|---|---|---|---|
| 1 | Découper selon la structure (page, tableau, figure + légende) plutôt qu'en blocs fixes | [S7] | Appliquée | Manuels organisés en chapitres par page, tableaux et figures numérotés ; citations exactes |
| 2 | Ajouter un en-tête contextuel au passage avant l'embedding | [S6] | Appliquée | Version déterministe (titre, page, équipements) ; Q08 retrouvée |
| 3 | Filtrer par métadonnées pendant la recherche, avec index de payload | [S1] | Appliquée | Groupes d'accès sur chaque élément ; 10 tests d'accès |
| 4 | Fusionner plusieurs recherches par RRF, en mesurant l'effet | [S2], [S3] | Appliquée | RRF pondérée : les images seules à poids égal faisaient baisser le Recall@5 |
| 5 | Encodeur texte-image ouvert, multilingue, choisi par benchmark | [S9] | Appliquée | OpenCLIP XLM-R : 15/20 requêtes visuelles contre 12/20 |
| 6 | Recherche hybride dense + lexicale / creuse (identifiants exacts) | [S2], [S4] | Reportée (S5) | Utile pour les codes d'alarme ; BGE-M3 fournit déjà des vecteurs creux |
| 7 | Recherche directe sur l'image des pages (ColPali) | [S5] | Écartée | VLM de plusieurs milliards de paramètres, pas de GPU dans l'équipe |
| 8 | Évaluer la recherche par Recall@k et MRR sur un jeu annoté | [S3] | Appliquée | 20 questions annotées, deux configurations, bonus calculé |
| 9 | Évaluer la génération (fidélité, pertinence du contexte) | [S8] | Reportée (S5) | Pas encore de génération au livrable 2 |

## 4. Sources

- [S1] Qdrant – *Filtering in Vector Search: When to Use What* – documentation officielle, mise à jour 2026 – https://qdrant.tech/documentation/search-design/vector-search-filtering/
- [S2] Qdrant – *Hybrid and Multi-Stage Queries* – documentation officielle (fonction disponible depuis la v1.10, 2024) – https://qdrant.tech/documentation/search/hybrid-queries/
- [S3] Qdrant – *How to Tune Hybrid Search in Qdrant* – documentation officielle, 2026 – https://qdrant.tech/documentation/search-tuning/how-to-tune-hybrid-search/
- [S4] J. Chen, S. Xiao, P. Zhang, K. Luo, D. Lian, Z. Liu – *BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation* – arXiv:2402.03216, 2024 – https://arxiv.org/abs/2402.03216
- [S5] M. Faysse et al. – *ColPali: Efficient Document Retrieval with Vision Language Models* – ICLR 2025, arXiv:2407.01449 – https://arxiv.org/abs/2407.01449
- [S6] Anthropic – *Introducing Contextual Retrieval* – billet technique, septembre 2024 – https://www.anthropic.com/news/contextual-retrieval
- [S7] A. Jimeno Yepes, Y. You, J. Milczek, S. Laverde, R. Li – *Financial Report Chunking for Effective Retrieval Augmented Generation* – arXiv:2402.05131, 2024 – https://arxiv.org/abs/2402.05131
- [S8] S. Es, J. James, L. Espinosa-Anke, S. Schockaert – *RAGAS: Automated Evaluation of Retrieval Augmented Generation* – EACL 2024 (démonstrations), arXiv:2309.15217 – https://arxiv.org/abs/2309.15217
- [S9] M. Cherti et al. – *Reproducible Scaling Laws for Contrastive Language-Image Learning* – CVPR 2023, arXiv:2212.07143 – https://arxiv.org/abs/2212.07143

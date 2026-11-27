# MaintiDoc – Livrable 2 : RAG multimodal

**Équipe ELFAROUKI-HAFFARI-LOKSAIRI** – Abderrahmane ELFAROUKI, Aya HAFFARI, Sabrine LOKSAIRI
Module IA générative multimodale – EMSI 2026 – Pr. Mariam CHERRABI – novembre 2026
Dépôt : https://github.com/Sabrineloksairi/maintidoc – version rendue : tag `v0.2-L2`

**En bref.** Les 36 documents du corpus sont découpés en 209 éléments, enregistrés dans PostgreSQL
et MinIO, et indexés dans Qdrant en texte (BGE-M3) et en images (OpenCLIP XLM-RoBERTa) en
4.5 minutes sur un portable sans GPU. Une question, avec ou sans photo, retrouve les bons passages et
figures parmi les seuls documents autorisés (10 tests automatiques). Sur 20 questions, le Recall@5 atteint
**0.94** dans les deux configurations, et la fusion pondérée corrige la baisse observée avec une fusion naïve.

## 1. Architecture réalisée et écarts par rapport au livrable 1

La figure 1 montre la chaîne réalisée. Elle reprend les blocs « ingestion », « recherche » et « stockage »
de l'architecture du livrable 1 (points de contrôle CP1 identité et CP2 filtrage avant recherche) ; la
génération par le VLM (semaine 3) et l'agent MCP (semaine 4) ne sont pas encore branchés.

![Figure 1 – Chaîne réalisée au livrable 2 (source : docs/diagrammes/05_chaine_L2.mmd)](/home/claude/maintidoc/docs/diagrammes/05_chaine_L2.png)

| Écart par rapport au livrable 1 | Justification |
|---|---|
| Deux moteurs OCR : Tesseract pour les pages scannées, RapidOCR pour le texte des photos | Le benchmark (§4) montre que chacun est nettement meilleur dans son cas d'usage |
| MinIO lancé depuis l'image `cgr.dev/chainguard/minio` | Les images officielles `minio/minio` ont été retirées de Docker Hub et de Quay fin 2025 ; même logiciel, reconstruit par Chainguard |
| Identification par l'en-tête HTTP `X-Utilisateur`, sans jeton | Suffisant pour démontrer le filtrage ; authentification par jeton prévue en semaine 4 (CP1 complet) |
| Exécution entièrement sur CPU (pas de GPU dans l'équipe) | Réglages légers : passages de 512 tokens maximum, encodeur ViT-B/32 ; risque R7/R8 du livrable 1 confirmé |
| Fusion RRF pondérée au lieu de RRF simple | Mesure : la RRF à poids égaux faisait baisser le Recall@5 (§6) |

## 2. Résumé de la veille

Le document séparé `L2_MaintiDoc_ELFAROUKI-HAFFARI-LOKSAIRI_Veille.pdf` (9 sources, dont 7 primaires) justifie nos choix. Nous
**appliquons** : un découpage structurel par page et par élément plutôt qu'en blocs fixes [S7] ; un en-tête
contextuel déterministe (titre, page, équipements) ajouté avant l'embedding, inspiré de la « Contextual
Retrieval » [S6] ; le filtrage par métadonnées pendant la recherche, sur des champs indexés [S1] ; la fusion
RRF, dont nous mesurons l'effet au lieu de le supposer [S2, S3] ; un encodeur texte-image ouvert et
multilingue de la famille OpenCLIP [S9] ; Recall@k et MRR sur un jeu annoté. Nous **reportons** à la semaine 5
la recherche hybride dense + creuse (vecteurs creux de BGE-M3 [S4]) pour les codes d'alarme et
l'évaluation de la génération (RAGAS [S8]). Nous **écartons** la recherche directe sur l'image des pages
(ColPali [S5]), qui demande un GPU.

## 3. Ingestion

**Extraction (PyMuPDF).** Pour chaque page : blocs de texte (en-têtes et pieds de page exclus), tableaux
détectés et convertis en Markdown avec leur légende « Tableau … », et figures. Nos schémas sont vectoriels,
sans image intégrée : nous regroupons les tracés proches (`cluster_drawings`, fusion des morceaux à moins
de 60 pt), nous écartons les encadrés d'avertissement et les grilles de tableaux, puis nous enregistrons la
zone en PNG (144 dpi) avec sa légende et les libellés qu'elle contient. Chaque page est aussi enregistrée en
image (≈ 100 dpi) pour être transmise au VLM en semaine 3.

**OCR.** Les 3 PDF scannés (`format = pdf_scanne`) sont rendus à 144 dpi et lus par Tesseract (français) ;
chaque page donne un élément « page » (index visuel) et des passages (index texte). Le texte visible sur les
5 photos (afficheurs, plaques) est lu par RapidOCR. Exemple : « Placer le bac sous le bouchon de vidange B …
serrer au couple de 25 N·m » est retrouvé dans la version scannée de la procédure de vidange.

**Découpage.** Une page de nos manuels correspond à un chapitre : nous découpons d'abord par page, puis
les passages par paragraphes jusqu'à ~900 caractères (≈ 200 à 250 tokens BGE-M3), avec 150 caractères de
chevauchement. Cette taille garde un seul sujet par passage (un voyant, une étape) tout en conservant son
contexte, et un passage ne traverse jamais deux pages, ce qui garantit des citations « document + page »
exactes. Résultat : 118 passages, 51 tableaux, 26 figures, 9 pages scannées et 5 photos.

**Métadonnées.** Chaque élément reprend de `inventaire.csv` : `document_id`, version, famille,
`equipement_id`, type de document, langue, format et groupes d'accès, plus son identifiant, sa page, son
type, sa boîte englobante, sa source d'extraction et les clés MinIO de son image et de sa page. Le texte
indexé est précédé d'un en-tête « titre – document – page – équipements ». Exemple d'élément indexé :

```
element_id     : manuel_pompe_a_p18_figure01
document_id    : manuel_pompe_a   version : v1.2 (2025-03)   page : 18
type_element   : figure   equipement_id : POMPE-A-01, POMPE-A-02   famille : pompes
groupes_acces  : techniciens_pompes, responsables
legende        : Figure 18.2 – Détail du voyant V2 orange TEMP. PALIER
chemin_image   : figures/manuel_pompe_a/p18_figure01.png   (MinIO, bucket maintidoc)
chemin_page    : pages/manuel_pompe_a/p18.png
texte_indexe   : Manuel d'utilisation et d'entretien pompe centrifuge HydroFlux HF-200 – manuel_pompe_a page 18 …
```

**Stockage.** Le script unique `python scripts/ingest.py --corpus corpus/` enchaîne extraction, OCR,
découpage, enregistrement dans PostgreSQL (36 documents, 209 éléments), envoi des
originaux dans MinIO (183 objets, 25.5 Mo) et indexation dans Qdrant.

<!--saut-->
## 4. Indexation, recherche et benchmarks

**Index.** `maintidoc_texte` : 199 éléments (passages, tableaux, légendes, texte des photos), BGE-M3, 1024
dimensions, en 184 s. `maintidoc_images` : 40 figures, photos et pages scannées, OpenCLIP
XLM-RoBERTa ViT-B/32, 512 dimensions, en 5 s. Distance cosinus ; toutes les métadonnées en charge utile, avec
des index keyword sur `groupes_acces`, `document_id`, `type_element` et `famille`. Indexation complète en
270 s (Windows AMD64, 12 cœurs, sans GPU).

**Recherche.** Pour une question : (1) recherche texte BGE-M3 (20 candidats) ; (2) recherche texte → image
avec OpenCLIP (5 candidats) ; (3) si une photo est fournie, recherche photo → image (5 candidats), et les
**identifiants** lus sur la photo (« HF-200 P-12 », « AT-37 C-07 ») sont ajoutés à la question ; (4) fusion
RRF pondérée, score = Σ wᵢ / (60 + rangᵢ), avec w = 1,0 pour le texte et 0,5 pour les listes visuelles ;
(5) 5 résultats avec document, page, type, extrait ou miniature et score. Accès par la fonction
`rechercher()`, l'API `POST /search` (FastAPI) et la page Streamlit `app/recherche_app.py`.

**Benchmarks** (mêmes documents, mêmes requêtes, même machine : Windows AMD64, 12 cœurs, sans GPU). L'OCR est comparé sur les
9 pages des 3 documents scannés, par rapport au texte d'origine des documents avant numérisation, et sur
3 photos. Les encodeurs sont comparés sur 20 requêtes visuelles en français dont la figure attendue est
annotée (`eval/requetes_visuelles.csv`). Le détail est dans `eval/benchmark_outils.csv`.

| Composant | Option | Qualité | Temps | Mémoire | Licence | Décision |
|---|---|---|---|---|---|---|
| Encodeur texte-image | clip-multilingue-st | 12/20 requêtes visuelles en français avec une image attendue dans le top 5 ; MRR@10 0.354 | 2 s pour 40 images ; 319 ms par requête ; chargement 12 s | 955 Mo (pic RSS) | Apache 2.0 | **Écarté** |
| Encodeur texte-image | openclip-xlmr | 15/20 requêtes visuelles en français avec une image attendue dans le top 5 ; MRR@10 0.568 | 4 s pour 40 images ; 90 ms par requête ; chargement 23 s | 1858 Mo (pic RSS) | MIT (open_clip, poids LAION) | **Retenu** |
| OCR pages scannées | rapidocr | mots corrects 31.7% ; exactitude caractères 62.4% (64.5% sans accents) ; faits clés 8/9 (9 pages des 3 documents scannés) | 13.1 s pour 9 pages (chargement inclus) | 64 Mo (pic RSS) | Apache 2.0 (modèles PaddleOCR : Apache 2.0) | **Écarté** |
| OCR pages scannées | tesseract | mots corrects 93.0% ; exactitude caractères 71.6% (71.7% sans accents) ; faits clés 8/9 (9 pages des 3 documents scannés) | 7.5 s pour 9 pages (chargement inclus) | 35 Mo (pic RSS) | Apache 2.0 | **Retenu** |
| OCR photos | rapidocr | textes clés lus 9/9 (codes d'alarme, n° de série, modèle sur 3 photos) | 2.1 s pour 3 photos | voir ligne pages scannées | Apache 2.0 (modèles PaddleOCR : Apache 2.0) | **Retenu** |
| OCR photos | tesseract | textes clés lus 6/9 (codes d'alarme, n° de série, modèle sur 3 photos) | 1.3 s pour 3 photos | voir ligne pages scannées | Apache 2.0 | **Écarté** |

Les outils imposés (PyMuPDF, BGE-M3, Qdrant, PostgreSQL, MinIO, FastAPI, Streamlit, Docker Compose) sont
utilisés sans remplacement.

## 5. Contrôle d'accès

Trois utilisateurs fictifs sont définis dans `config/utilisateurs.yaml` : `tech_pompes`
(techniciens_pompes), `tech_compresseurs` (techniciens_compresseurs) et `responsable` (responsables).
L'utilisateur est résolu en groupes **avant** toute recherche ; chaque requête Qdrant (texte, texte → image,
photo → image) porte le filtre « `groupes_acces` contient un groupe de l'utilisateur », de sorte qu'un
document interdit n'est jamais candidat. L'ouverture d'une image ou d'une page (`GET /elements/{id}/image`,
page Streamlit) revérifie les droits élément par élément et renvoie le même refus (HTTP 403) que l'élément
existe ou non.

`pytest tests/` exécute **10 tests, tous réussis** sur le PC de l'équipe, sans modèle (Qdrant en mémoire et
vrais documents du corpus) : un technicien pompes ne voit aucun document compresseurs (3 questions qui les
ciblent) ; la note de service et l'historique réservés aux responsables restent invisibles même quand la
question cite leur titre et leur référence ; une photo de compresseur ne contourne pas le filtre ; l'ouverture
d'image et de page est refusée (fonction et API) ; un espion vérifie que les 3 appels Qdrant portent le
filtre ; un utilisateur inconnu est refusé. Pour vérifier les tests eux-mêmes, nous avons retiré le filtre :
8 tests sur 10 échouent alors. Dans l'évaluation, les 2 questions d'accès (Q17, Q18) ne renvoient aucun
document interdit.

<!--saut-->
## 6. Évaluation

**Jeu de test** (`eval/questions_test.csv`) : 20 questions rédigées par l'équipe, dont 6 avec photo
(photos distinctes de celles du corpus : autre angle, autre éclairage, voyant jaune), 2 cas contradictoires
(procédures v1/v2), 3 cas ambigus (voyant orange isolé, pompe sans voyant orange, plaque illisible) et 2 cas
d'accès refusé. Les éléments attendus sont donnés sous la forme « document p.N ».

| # | Type | Photo | Éléments attendus | Texte seul (top 5) | Texte + images (top 5) |
|---|---|---|---|---|---|
| Q01 | photo | oui | manuel_pompe_a p.18, codes_alarme_pompe_a p.1, manuel_pompe_a p.12 | ✔ (rang 1) | ✔ (rang 3) |
| Q02 | contradictoire |  | proc_vidange_a_v2 p.3, proc_vidange_a_v1 p.2, manuel_pompe_a p.16, manuel_pompe_a p.5 | ✔ (rang 2) | ✔ (rang 2) |
| Q03 | contradictoire |  | proc_purge_comp_b_v2 p.1, proc_purge_comp_b_v1 p.1, manuel_comp_b p.18 | ✔ (rang 1) | ✔ (rang 1) |
| Q04 | photo | oui | manuel_comp_b p.15, proc_filtre_air_comp_b p.1, codes_alarme_comp_b p.1, manuel_comp_b p.11 | ✔ (rang 1) | ✔ (rang 4) |
| Q05 | ambigu | oui | manuel_comp_b p.11, manuel_comp_b p.15, photo_panneau_comp_b, manuel_pompe_a p.18 | ✔ (rang 1) | ✔ (rang 1) |
| Q06 | photo | oui | manuel_pompe_a p.5, manuel_pompe_a p.16, fiche_securite_huile_palier p.1, photo_plaque_pompe_a | ✔ (rang 3) | ✔ (rang 1) |
| Q07 | photo | oui | manuel_pompe_a p.12, codes_alarme_pompe_a p.1, codes_alarme_pompe_a p.2, schema_hydraulique_pompe_a p.1 | ✔ (rang 3) | ✔ (rang 5) |
| Q08 | texte |  | manuel_pompe_c p.7 | ✔ (rang 3) | ✔ (rang 3) |
| Q09 | texte |  | manuel_pompe_a p.8 | ✔ (rang 1) | ✔ (rang 3) |
| Q10 | texte |  | proc_garniture_pompe_a p.1, proc_garniture_pompe_a p.2, manuel_pompe_a p.17 | ✔ (rang 1) | ✔ (rang 1) |
| Q11 | texte |  | proc_alignement_pompes p.1 | ✔ (rang 1) | ✔ (rang 3) |
| Q12 | texte |  | manuel_comp_p p.3, manuel_comp_p p.2, plan_preventif_compresseurs p.1 | ✔ (rang 1) | ✔ (rang 1) |
| Q13 | texte |  | schema_electrique_comp_b p.1 | ✔ (rang 1) | ✔ (rang 1) |
| Q14 | texte |  | proc_purge_comp_b_v2 p.2, codes_alarme_comp_b p.1, manuel_comp_b p.18 | ✔ (rang 1) | ✔ (rang 1) |
| Q15 | texte |  | fiche_securite_consignation_pompes p.1, manuel_pompe_a p.14 | ✔ (rang 1) | ✔ (rang 1) |
| Q16 | ambigu |  | manuel_pompe_c p.5 | ✔ (rang 4) | ✘ (rang 6) |
| Q17 | acces |  | aucun (accès refusé) | accès respecté  | accès respecté  |
| Q18 | acces |  | aucun (accès refusé) | accès respecté  | accès respecté  |
| Q19 | texte |  | historique_pompe_a_01 p.1 | ✔ (rang 1) | ✔ (rang 2) |
| Q20 | ambigu | oui | photo_plaque_pompe_floue, photo_plaque_pompe_a | ✘ (rang 8) | ✔ (rang 1) |

**Bonus – métriques calculées par script** (`python scripts/evaluer_recherche.py`, 18 questions de
pertinence ; les 2 questions d'accès sont comptées à part) :

| Configuration | Recall@5 | MRR@10 | Succès top 5 | Accès respecté | Latence médiane |
|---|---|---|---|---|---|
| Texte seul | **0.944** | **0.771** | 17/18 | 2/2 | 0.19 s |
| Texte + images (RRF pondérée, retenue) | **0.944** | 0.664 | 17/18 | 2/2 | 0.25 s |
| Texte + images (RRF à poids égaux, 1re version) | 0.833 | 0.654 | 15/18 | 2/2 | 0.24 s |

**Lecture.** La première fusion, à poids égaux, faisait baisser le Recall@5 (0,83) : une liste visuelle renvoie
toujours des images, même quand aucune n'est pertinente, et elles prenaient la place de bons passages. La
fusion pondérée retrouve le Recall@5 du texte seul (0,94). Les images apportent un gain net quand la photo
porte l'information : plaque signalétique Q06 (rang 3 → 1) et plaque illisible Q20 (rang 8 → 1). Elles font en
revanche reculer de quelques rangs la bonne réponse de questions purement textuelles, d'où un MRR@10 plus
bas (0,66 contre 0,77). Les poids ont été fixés a priori, sans recherche systématique sur ces 20 questions, pour
éviter de sur-ajuster le jeu de test.

**Analyse de 3 échecs**

| Question | Résultat obtenu | Cause probable | Piste de correction |
|---|---|---|---|
| **Q16** « La pompe POMPE-C-03 a un voyant orange allumé, que faire ? » (attendu : manuel_pompe_c p.5) | Texte + images : rang 6 (hors top 5) ; en tête, la figure 18.2 du voyant orange de la pompe HF-200 | La recherche texte → image associe « voyant orange » au voyant de la pompe A ; l'encodeur visuel ignore l'identifiant d'équipement cité dans la question | Quand un `equipement_id` est reconnu dans la question, filtrer ou favoriser ses documents (métadonnée déjà indexée) ; reranker en semaine 5 |
| **Q20** « Quel est le modèle et le numéro de série de cette pompe ? » + plaque floue (texte seul) | Texte seul : rang 8 ; résultats génériques (manuels) | La question ne contient aucune information discriminante et la configuration texte seul ignore la photo | Corrigé par la recherche photo → image (rang 1) ; en semaine 3, le système devra surtout **demander une photo nette** plutôt que répondre |
| **Q07** voyant **jaune** allumé (P-04) + « que dois-je vérifier ? » | Texte + images : succès limite au rang 5 (rang 3 en texte seul) ; en tête, la photo du même panneau avec le voyant **orange** allumé | La similarité photo → image compare l'aspect global du panneau et ne distingue pas quel voyant est allumé ; seul « P-04 », lu par OCR, oriente vers la bonne réponse | Donner plus de poids aux identifiants lus (code d'alarme) qu'à la photo ; en semaine 3, faire décrire par le VLM quel voyant est allumé |

Limite du jeu de test : pour Q01 et Q04, la première réponse en mode texte + images est la photo du même
panneau dans le corpus, pertinente pour un technicien mais absente des éléments attendus. Les annotations
seront élargies en semaine 5.

<!--saut-->
## 7. Captures d'écran

![Figure 3 – Recherche texte (tech_pompes) : question sur le couple de serrage ; les deux versions contradictoires de la procédure ressortent avec leur page](/home/claude/maintidoc/eval/captures/recherche_texte.png)

![Figure 4 – Recherche avec photo (tech_compresseurs, photo eval/photos/q04.jpg) : le code C-07 lu sur la photo est ajouté à la requête ; écran, panneau et procédures du compresseur](/home/claude/maintidoc/eval/captures/recherche_photo.png)

![Figure 5 – Accès refusé : tech_pompes tente d'ouvrir l'image d'une figure de la famille compresseurs](/home/claude/maintidoc/eval/captures/acces_refuse.png)65

<!--saut-->
## 8. Difficultés rencontrées et répartition du travail

**Difficultés.** (1) Le poste de travail avait Python 3.15, trop récent pour PyTorch et onnxruntime :
environnement virtuel créé avec Python 3.12. (2) Le téléchargement des modèles (≈ 3,5 Go) échouait sur une
connexion instable : script `telecharger_modeles.py` avec reprise automatique et délai d'attente allongé.
(3) Tesseract installé sans la langue française : ajout de `fra.traineddata` dans le projet. (4) Les images
Docker officielles de MinIO ne sont plus disponibles : image Chainguard. (5) Nos schémas vectoriels étaient
pris pour des tableaux par PyMuPDF : règle « un tableau contenu dans un dessin plus grand appartient à la
figure ». (6) La première fusion RRF dégradait les résultats : diagnostic par analyse question par question,
puis pondération. (7) Un fichier corrompu à la lecture sur le disque D: a interrompu une indexation ;
relance réussie.

**Usage de l'IA.** Le code a été écrit avec l'aide d'un assistant IA (Claude), puis exécuté, testé et relu par
l'équipe sur ses machines ; tous les chiffres de ce rapport viennent de nos exécutions.

**Répartition du travail.**

| Membre | Contribution principale au livrable 2 |
|---|---|
| Sabrine LOKSAIRI | Coordination, installation de l'environnement (Python, Docker, Qdrant, PostgreSQL, MinIO, Tesseract), ingestion et OCR, exécution des benchmarks et de l'évaluation, dépôt Git |
| Abderrahmane ELFAROUKI | Jeu de 20 questions et éléments attendus, requêtes visuelles du benchmark des encodeurs, analyse des échecs |
| Aya HAFFARI | Contrôle d'accès et tests automatiques, API et page Streamlit, captures d'écran, veille |

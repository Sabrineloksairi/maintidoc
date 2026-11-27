# MaintiDoc

**Assistant documentaire multimodal et agentique pour la maintenance**
Module IA générative multimodale – EMSI 2026 – Pr. Mariam CHERRABI
Équipe **ELFAROUKI-HAFFARI-LOKSAIRI** – version rendue : tag `v0.2-L2` (livrable 2 : RAG multimodal)

| Membre | Rôle principal |
|---|---|
| Abderrahmane ELFAROUKI | Modèles et évaluation (encodeurs, benchmark, jeu de test) |
| Aya HAFFARI | Agent, sécurité et intégration (contrôle d'accès, API, interface, tests) |
| Sabrine LOKSAIRI | Coordination, corpus et données (ingestion, OCR, indexation) |

Le système découpe les 36 documents du corpus (pompes centrifuges et compresseurs d'air), les indexe en
texte et en images dans Qdrant, et retrouve pour une question (avec ou sans photo) les passages et figures
pertinents, **uniquement parmi les documents que l'utilisateur a le droit de consulter**. La rédaction de la
réponse par le modèle vision-langage est prévue en semaine 3.

---

## 1. Installation (Windows, sans GPU)

Prérequis : Python **3.10 à 3.12**, Git, Docker Desktop (démarré).

```powershell
git clone https://github.com/Sabrineloksairi/maintidoc.git
cd maintidoc
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1          # si refusé : Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install --upgrade pip
pip install -r requirements.txt       # ~2 Go (PyTorch CPU), 5 à 15 min
copy .env.example .env               # puis remplacer les valeurs « a_definir_localement » par vos mots de passe
docker compose up -d                  # Qdrant :6333, PostgreSQL :5432, MinIO :9000
```

**Tesseract (OCR des pages scannées)** : installer Tesseract 5 pour Windows (UB Mannheim) :
`winget install --id UB-Mannheim.TesseractOCR`, puis vérifier que la langue française est présente :
`& "C:\Program Files\Tesseract-OCR\tesseract.exe" --list-langs` doit afficher `fra`. Sinon, placer
`fra.traineddata` (dépôt `tesseract-ocr/tessdata_fast`) dans un dossier `tessdata\` du projet et
décommenter `TESSDATA_PREFIX` dans `.env`. Sans Tesseract, l'ingestion bascule automatiquement sur RapidOCR.

Linux / macOS : mêmes commandes avec `python3 -m venv .venv && source .venv/bin/activate` et
`sudo apt install tesseract-ocr tesseract-ocr-fra` (ou `brew install tesseract tesseract-lang`).

## 2. Commandes

| Action | Commande |
|---|---|
| Télécharger les modèles (une fois) | `python scripts/telecharger_modeles.py` |
| Ingestion + indexation complètes | `python scripts/ingest.py --corpus corpus/` |
| Essai sur quelques documents | `python scripts/ingest.py --documents manuel_pompe_a photo_panneau_pompe_a` |
| Page de test (recherche) | `streamlit run app/recherche_app.py` |
| API de recherche | `uvicorn src.api:app --reload` puis http://localhost:8000/docs |
| Tests du contrôle d'accès | `pytest tests/ -v` (aucun modèle requis : Qdrant en mémoire, embeddings factices) |
| Évaluation (20 questions, Recall@5, MRR@10) | `python scripts/evaluer_recherche.py` |
| Benchmark OCR | `python scripts/benchmark_ocr.py` |
| Benchmark encodeurs texte-image | `python scripts/benchmark_encodeurs.py` |
| Contrôle de l'inventaire | `python outils/verifier_inventaire.py` |

Exemple d'appel de l'API (identification simplifiée par l'en-tête `X-Utilisateur`) :

```powershell
curl.exe -X POST http://localhost:8000/search -H "X-Utilisateur: tech_pompes" `
  -F "question=Que signifie le voyant orange ?" -F "mode=texte_images" -F "photo=@eval/photos/q01.jpg"
```

Utilisateurs fictifs (`config/utilisateurs.yaml`) : `tech_pompes`, `tech_compresseurs`, `responsable`.

## 3. Modèles et outils

| Composant | Outil retenu | Version / modèle | Licence |
|---|---|---|---|
| Extraction PDF | PyMuPDF | 1.24.14 | AGPL-3.0 |
| OCR pages scannées | Tesseract (benchmark : 93 % de mots corrects contre 32 % pour RapidOCR) | Tesseract 5, langue `fra` | Apache 2.0 |
| OCR texte sur photos | RapidOCR (benchmark : 9/9 textes clés contre 7/9) | rapidocr-onnxruntime 1.2.3 | Apache 2.0 |
| Embeddings texte | BGE-M3 (imposé) | `BAAI/bge-m3`, 1024 dim., `max_seq_length` 512 | MIT |
| Encodeur texte-image | OpenCLIP XLM-RoBERTa (benchmark : 15/20 requêtes visuelles contre 12/20) | `xlm-roberta-base-ViT-B-32` / `laion5b_s13b_b90k`, 512 dim. | MIT |
| Base vectorielle | Qdrant (imposé) | serveur v1.12.5 (Docker), client 1.12.1 | Apache 2.0 |
| Métadonnées | PostgreSQL (imposé) | 16 (Docker `postgres:16-alpine`), psycopg 3.2.3 | PostgreSQL License |
| Fichiers originaux | MinIO (imposé) | image `cgr.dev/chainguard/minio` (les images officielles ont été retirées fin 2025), client minio 7.2.10 | AGPL-3.0 |
| API / interface | FastAPI / Streamlit (imposés) | 0.115.5 / 1.40.2 | MIT / Apache 2.0 |

Matériel de référence : ordinateur portable Windows 11, processeur 12 cœurs, **sans GPU** (tout sur CPU).
Temps mesurés : extraction + OCR des 36 documents en ~25 s (209 éléments) ; chargement des modèles
30 à 70 s ; index texte BGE-M3 (199 éléments) 2 min 30 à 4 min ; index images OpenCLIP (40 éléments) 4 s ;
total ≈ 4 min 30 à 5 min. Premier lancement : ~3,5 Go de modèles à télécharger
(`python scripts/telecharger_modeles.py`, reprise automatique en cas de coupure).

`scripts/ingest.py` enregistre le registre des documents et des éléments dans **PostgreSQL** (tables
`documents`, `elements`), envoie les figures, tableaux, pages et photos dans **MinIO** (bucket `maintidoc`),
puis indexe dans **Qdrant**, qui garde une copie des métadonnées en charge utile pour filtrer avant la
recherche. Sans `POSTGRES_DSN` / `MINIO_ENDPOINT` (tests automatiques), ces deux étapes sont ignorées et les
images sont lues dans `data/`.

## 4. Fonctionnement

- **Ingestion** (`src/ingestion`) : texte, tableaux (Markdown) et figures (PNG) extraits par PyMuPDF ;
  OCR des 3 PDF scannés ; découpage par page puis par paragraphes (~900 caractères, chevauchement 150) ;
  métadonnées reprises de `corpus/inventaire.csv` ; chaque figure garde un lien vers l'image de sa page.
- **Indexation** (`src/indexation`) : collection `maintidoc_texte` (BGE-M3) et `maintidoc_images` (CLIP),
  métadonnées en charge utile, index sur `groupes_acces`, `document_id`, `type_element`, `famille`.
- **Recherche** (`src/recherche`) : texte → index texte ; texte → images ; photo → images ; texte lu sur la
  photo ajouté à la question ; fusion RRF (k = 60) ; 5 meilleurs résultats avec document, page, type, extrait.
- **Accès** (`src/acces`) : filtre Qdrant sur les groupes de l'utilisateur à chaque requête (avant la
  recherche) ; ouverture des images et pages vérifiée élément par élément (HTTP 403 sinon).

## 5. Structure du dépôt

```
maintidoc/
├── README.md · requirements.txt · docker-compose.yml · .env.example · .gitignore
├── config/utilisateurs.yaml        utilisateurs fictifs et groupes
├── src/ingestion/ indexation/ recherche/ acces/ · src/api.py · src/config.py
├── app/recherche_app.py            page de test Streamlit
├── scripts/ingest.py · evaluer_recherche.py · benchmark_ocr.py · benchmark_encodeurs.py
├── tests/test_acces.py             tests automatiques du contrôle d'accès
├── eval/questions_test.csv · photos/ · requetes_visuelles.csv · benchmark_outils.csv · ocr_reference/
├── docs/diagrammes/ · docs/veille/ · docs/referentiel_corpus.md · docs/rapport/
├── corpus/                         36 documents, inventaire.csv, prompts_corpus.md
└── outils/verifier_inventaire.py
```

Utilisateurs, équipements, tickets et historiques sont **fictifs**. Aucun secret n'est versionné
(`.env` est ignoré par Git).

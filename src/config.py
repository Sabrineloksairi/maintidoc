"""Configuration centrale de MaintiDoc (chemins, modèles, Qdrant).

Toutes les valeurs peuvent être surchargées par des variables d'environnement
(voir .env.example). Aucune valeur secrète ici.
"""
from __future__ import annotations

import os
from pathlib import Path

try:  # chargement facultatif d'un fichier .env local (jamais versionné)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

RACINE = Path(__file__).resolve().parent.parent

# Téléchargements Hugging Face plus tolérants (connexion lente) – voir scripts/telecharger_modeles.py
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "120")
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "60")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

# --- Chemins ---------------------------------------------------------------
CORPUS_DIR = Path(os.getenv("MAINTIDOC_CORPUS", RACINE / "corpus"))
DATA_DIR = Path(os.getenv("MAINTIDOC_DATA", RACINE / "data"))
ELEMENTS_FILE = DATA_DIR / "elements.jsonl"
FIGURES_DIR = DATA_DIR / "figures"
PAGES_DIR = DATA_DIR / "pages"
UTILISATEURS_FILE = Path(os.getenv("MAINTIDOC_UTILISATEURS", RACINE / "config" / "utilisateurs.yaml"))

# --- Ingestion ---------------------------------------------------------------
OCR_MOTEUR = os.getenv("MAINTIDOC_OCR", "tesseract")         # pages scannées : tesseract (retenu, cf. benchmark) | rapidocr
OCR_PHOTO = os.getenv("MAINTIDOC_OCR_PHOTO", "rapidocr")       # texte sur photos (afficheurs, plaques) : rapidocr (retenu)
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")               # chemin de tesseract.exe sous Windows
TAILLE_PASSAGE = int(os.getenv("MAINTIDOC_TAILLE_PASSAGE", "900"))     # caractères (~200-250 tokens)
CHEVAUCHEMENT = int(os.getenv("MAINTIDOC_CHEVAUCHEMENT", "150"))       # caractères
ZOOM_FIGURE = 2.0      # 144 dpi pour les figures
ZOOM_PAGE = 1.4        # ~100 dpi pour les pages entières

# --- Modèles ---------------------------------------------------------------
MODELE_TEXTE = os.getenv("MAINTIDOC_MODELE_TEXTE", "BAAI/bge-m3")
ENCODEUR_IMAGE = os.getenv("MAINTIDOC_ENCODEUR_IMAGE", "clip-multilingue-st")
# Mode de test : embeddings factices déterministes (aucun téléchargement de modèle)
EMBEDDINGS_FACTICES = os.getenv("MAINTIDOC_EMBEDDINGS_FACTICES", "0") == "1"

# --- Qdrant ----------------------------------------------------------------
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_PATH = os.getenv("QDRANT_PATH", "")      # si renseigné : Qdrant embarqué sur disque (sans Docker)
COLLECTION_TEXTE = os.getenv("MAINTIDOC_COLLECTION_TEXTE", "maintidoc_texte")
COLLECTION_IMAGES = os.getenv("MAINTIDOC_COLLECTION_IMAGES", "maintidoc_images")

# --- PostgreSQL (métadonnées) et MinIO (fichiers originaux) – facultatifs pour les tests ---------
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "")                 # ex. postgresql://maintidoc:***@localhost:5432/maintidoc
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")             # ex. localhost:9000
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "maintidoc")
MINIO_SECURE = os.getenv("MINIO_SECURE", "0") == "1"

# --- Recherche ---------------------------------------------------------------
TOP_K = 5
CANDIDATS_PAR_LISTE = 20          # candidats de la liste texte
CANDIDATS_VISUELS = int(os.getenv("MAINTIDOC_CANDIDATS_VISUELS", "5"))   # candidats des listes visuelles
RRF_K = 60
# Fusion RRF pondérée : le texte est plus fiable que l'encodeur texte-image (cf. benchmark),
# et une liste visuelle renvoie toujours des images, même quand aucune n'est pertinente.
POIDS_RRF = {"texte": 1.0, "texte→image": 0.5, "photo→image": 0.5}

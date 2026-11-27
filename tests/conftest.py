"""Configuration des tests : Qdrant en mémoire + embeddings factices (aucun modèle à télécharger).

L'ingestion est faite sur de VRAIS documents du corpus (deux familles, documents réservés aux
responsables, photos) pour que les métadonnées testées viennent bien de inventaire.csv.
"""
import os
import tempfile

# Variables à définir AVANT d'importer src.config
_TMP = tempfile.mkdtemp(prefix="maintidoc_tests_")
os.environ["MAINTIDOC_EMBEDDINGS_FACTICES"] = "1"
os.environ["QDRANT_PATH"] = ":memory:"
os.environ["MAINTIDOC_DATA"] = _TMP
os.environ["MAINTIDOC_COLLECTION_TEXTE"] = "test_texte"
os.environ["MAINTIDOC_COLLECTION_IMAGES"] = "test_images"

import pytest  # noqa: E402

DOCS_TEST = [
    "manuel_pompe_a",               # pompes – techniciens_pompes ; responsables
    "proc_filtre_air_comp_b",       # compresseurs – techniciens_compresseurs ; responsables
    "codes_alarme_comp_b",          # compresseurs
    "note_service_compresseurs",    # compresseurs – responsables uniquement
    "historique_pompe_a_01",        # pompes – responsables uniquement
    "photo_panneau_pompe_a",        # photo pompes
    "photo_ecran_alarme_comp_b",    # photo compresseurs
]


@pytest.fixture(scope="session")
def index_test():
    from src import config
    from src.indexation.embeddings import encodeur_image, encodeur_texte
    from src.indexation.qdrant_store import indexer
    from src.ingestion.pipeline import ingerer

    elements = ingerer(config.CORPUS_DIR, documents=DOCS_TEST, verbeux=False)
    indexer(elements, encodeur_texte(), encodeur_image(), verbeux=False)
    return elements

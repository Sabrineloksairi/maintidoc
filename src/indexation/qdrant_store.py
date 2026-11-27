"""Stockage des vecteurs et des métadonnées dans Qdrant.

Deux collections :
- maintidoc_texte  : passages, tableaux, légendes de figures, texte OCR des photos (BGE-M3) ;
- maintidoc_images : figures, schémas, photos et pages scannées (encodeur texte-image).
Toutes les métadonnées de l'élément sont en charge utile (payload), avec des index sur
groupes_acces, document_id et type_element pour filtrer AVANT la recherche.
"""
from __future__ import annotations

import time
import uuid

from PIL import Image
from qdrant_client import QdrantClient, models

from src import config

TYPES_TEXTE = {"passage", "tableau", "figure", "photo"}
TYPES_IMAGE = {"figure", "photo", "page"}
CHAMPS_INDEXES = ("groupes_acces", "document_id", "type_element", "famille")
_NAMESPACE = uuid.UUID("6f0c1c1e-4a51-4c1b-9a3e-6d61696e7469")


def id_point(element_id: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, element_id))


_client: QdrantClient | None = None


def client() -> QdrantClient:
    """Client unique : serveur Docker (QDRANT_URL) ou mode embarqué (QDRANT_PATH / « :memory: »)."""
    global _client
    if _client is None:
        if config.QDRANT_PATH == ":memory:":
            _client = QdrantClient(location=":memory:")
        elif config.QDRANT_PATH:
            _client = QdrantClient(path=config.QDRANT_PATH)
        else:
            _client = QdrantClient(url=config.QDRANT_URL, timeout=60)
    return _client


def reinitialiser_client():
    global _client
    _client = None


def _creer_collection(nom: str, dim: int):
    c = client()
    if c.collection_exists(nom):
        c.delete_collection(nom)
    c.create_collection(nom, vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE))
    for champ in CHAMPS_INDEXES:
        try:
            c.create_payload_index(nom, champ, field_schema=models.PayloadSchemaType.KEYWORD)
        except Exception:  # mode embarqué : index non supportés, le filtre fonctionne quand même
            pass


def _payload(el: dict) -> dict:
    return {k: v for k, v in el.items() if k != "texte_indexe"}


def indexer(elements: list[dict], enc_texte, enc_image, verbeux: bool = True) -> dict:
    stats = {}
    c = client()

    # --- index textuel ------------------------------------------------------
    t0 = time.perf_counter()
    els_t = [e for e in elements if e["type_element"] in TYPES_TEXTE and e["texte"].strip()]
    _creer_collection(config.COLLECTION_TEXTE, enc_texte.dim)
    vecteurs = enc_texte.encoder([e["texte_indexe"] for e in els_t])
    c.upsert(config.COLLECTION_TEXTE, points=[
        models.PointStruct(id=id_point(e["element_id"]), vector=v.tolist(), payload=_payload(e))
        for e, v in zip(els_t, vecteurs)], wait=True)
    stats["texte"] = {"elements": len(els_t), "secondes": round(time.perf_counter() - t0, 1),
                      "modele": enc_texte.nom, "dim": enc_texte.dim}

    # --- index visuel -------------------------------------------------------
    t0 = time.perf_counter()
    els_i = [e for e in elements if e["type_element"] in TYPES_IMAGE and e.get("chemin_image")]
    _creer_collection(config.COLLECTION_IMAGES, enc_image.dim)
    points = []
    for i in range(0, len(els_i), 16):
        lot = els_i[i:i + 16]
        images = [Image.open(config.DATA_DIR / e["chemin_image"]) for e in lot]
        for e, v in zip(lot, enc_image.encoder_images(images)):
            points.append(models.PointStruct(id=id_point(e["element_id"]), vector=v.tolist(), payload=_payload(e)))
    c.upsert(config.COLLECTION_IMAGES, points=points, wait=True)
    stats["images"] = {"elements": len(els_i), "secondes": round(time.perf_counter() - t0, 1),
                       "modele": enc_image.nom, "dim": enc_image.dim}
    if verbeux:
        for k, s in stats.items():
            print(f"  index {k:6s} : {s['elements']:4d} éléments, {s['modele']} ({s['dim']} dim.), {s['secondes']} s")
    return stats


def lire_element(element_id: str) -> dict | None:
    """Charge les métadonnées d'un élément (sans filtre : à n'utiliser qu'avec un contrôle d'accès)."""
    pid = id_point(element_id)
    for col in (config.COLLECTION_TEXTE, config.COLLECTION_IMAGES):
        pts = client().retrieve(col, ids=[pid], with_payload=True)
        if pts:
            return pts[0].payload
    return None

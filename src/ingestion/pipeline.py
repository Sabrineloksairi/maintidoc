"""Ingestion complète du corpus : inventaire -> éléments -> data/elements.jsonl."""
from __future__ import annotations

import json
import shutil
import time
from collections import Counter
from pathlib import Path

from src import config
from src.ingestion.extraction import extraire_document
from src.ingestion.inventaire import charger_inventaire
from src.ingestion.ocr import obtenir_moteur


def ingerer(corpus_dir: Path, moteur_ocr: str | None = None, documents: list[str] | None = None,
            verbeux: bool = True) -> list[dict]:
    t0 = time.perf_counter()
    docs = charger_inventaire(corpus_dir)
    if documents:
        docs = [d for d in docs if d.document_id in documents]
    for dossier in (config.FIGURES_DIR, config.PAGES_DIR):
        shutil.rmtree(dossier, ignore_errors=True)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    ocr = obtenir_moteur(moteur_ocr)
    ocr_photo = obtenir_moteur(config.OCR_PHOTO)

    elements: list[dict] = []
    for doc in docs:
        if not doc.chemin.exists():
            raise FileNotFoundError(f"{doc.document_id} : fichier absent {doc.chemin}")
        t = time.perf_counter()
        els = extraire_document(doc, ocr, ocr_photo)
        elements += els
        if verbeux:
            types = Counter(e["type_element"] for e in els)
            print(f"  {doc.document_id:38s} {doc.format:10s} {len(els):3d} éléments "
                  f"{dict(types)}  ({time.perf_counter() - t:.1f} s)")

    ids = [e["element_id"] for e in elements]
    doublons = {i for i in ids if ids.count(i) > 1}
    if doublons:
        raise RuntimeError(f"Identifiants d'éléments en double : {sorted(doublons)[:5]}")

    with open(config.ELEMENTS_FILE, "w", encoding="utf-8") as f:
        for e in elements:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    if verbeux:
        print(f"\n{len(docs)} documents -> {len(elements)} éléments "
              f"{dict(Counter(e['type_element'] for e in elements))} "
              f"en {time.perf_counter() - t0:.0f} s (OCR pages : {ocr.nom}, OCR photos : {ocr_photo.nom}) "
              f"-> {config.ELEMENTS_FILE}")
    return elements


def charger_elements() -> list[dict]:
    with open(config.ELEMENTS_FILE, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]

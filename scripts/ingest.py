"""Script unique : relance toute l'ingestion et l'indexation depuis le dossier du corpus.

Exemples :
    python scripts/ingest.py --corpus corpus/
    python scripts/ingest.py --corpus corpus/ --ocr rapidocr --encodeur-image openclip-xlmr
    python scripts/ingest.py --documents manuel_pompe_a photo_panneau_pompe_a   # test sur quelques documents
    python scripts/ingest.py --sans-index                                      # extraction seule
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    ap = argparse.ArgumentParser(description="Ingestion + indexation MaintiDoc")
    ap.add_argument("--corpus", default="corpus", help="dossier contenant inventaire.csv")
    ap.add_argument("--ocr", choices=["tesseract", "rapidocr"], help="moteur OCR (défaut : tesseract)")
    ap.add_argument("--encodeur-image", choices=["clip-multilingue-st", "openclip-xlmr"])
    ap.add_argument("--documents", nargs="*", help="limiter à ces document_id")
    ap.add_argument("--sans-index", action="store_true", help="ne pas indexer dans Qdrant")
    args = ap.parse_args()
    if args.encodeur_image:
        os.environ["MAINTIDOC_ENCODEUR_IMAGE"] = args.encodeur_image

    from src import config
    from src.ingestion.pipeline import ingerer

    t0 = time.perf_counter()
    print("== 1. Ingestion (extraction, OCR, découpage, métadonnées)")
    elements = ingerer(Path(args.corpus), moteur_ocr=args.ocr, documents=args.documents)
    if args.sans_index:
        return
    from src.indexation import stockage
    from src.indexation.embeddings import encodeur_image, encodeur_texte
    from src.indexation.qdrant_store import indexer
    from src.ingestion.inventaire import charger_inventaire

    stats = {}
    if stockage.postgres_actif():
        print("\n== 2a. Métadonnées -> PostgreSQL")
        docs = [d for d in charger_inventaire(Path(args.corpus))
                if not args.documents or d.document_id in args.documents]
        stats["postgres"] = stockage.enregistrer_postgres(docs, elements)
        print(f"  {stats['postgres']['documents']} documents, {stats['postgres']['elements']} éléments")
    else:
        print("\n(PostgreSQL non configuré : étape ignorée)")
    if stockage.minio_actif():
        print("== 2b. Fichiers originaux -> MinIO")
        stats["minio"] = stockage.televerser_minio(elements)
        print(f"  {stats['minio']['objets']} objets ({stats['minio']['mo']} Mo) dans le bucket {config.MINIO_BUCKET}")
    else:
        print("(MinIO non configuré : images lues dans data/)")

    cible = config.QDRANT_PATH or config.QDRANT_URL
    print(f"\n== 3. Indexation dans Qdrant ({cible})")
    t1 = time.perf_counter()
    enc_t, enc_i = encodeur_texte(), encodeur_image()
    print(f"  modèles chargés en {time.perf_counter() - t1:.0f} s : {enc_t.nom} / {enc_i.nom}")
    stats.update(indexer(elements, enc_t, enc_i))
    stats["total_secondes"] = round(time.perf_counter() - t0, 1)
    stats["nb_elements"] = len(elements)
    (config.DATA_DIR / "stats_indexation.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False),
                                                           encoding="utf-8")
    print(f"\nTerminé en {stats['total_secondes']} s -> data/stats_indexation.json")


if __name__ == "__main__":
    main()

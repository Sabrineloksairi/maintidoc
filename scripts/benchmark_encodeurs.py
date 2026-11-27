"""Benchmark des encodeurs texte-image (exigé : au moins 2 modèles, mêmes images, mêmes requêtes).

Critères :
- qualité : nombre de requêtes visuelles en français (eval/requetes_visuelles.csv, 20 requêtes)
  dont une image attendue figure dans le top 5 des images du corpus ; + MRR@10 ;
- temps d'encodage de toutes les images du corpus ; mémoire (pic RSS) ; licence.

Usage (après `python scripts/ingest.py --sans-index` ou une ingestion complète) :
    python scripts/benchmark_encodeurs.py
Résultat : lignes « Encodeur texte-image » dans eval/benchmark_outils.csv
"""
from __future__ import annotations

import csv
import gc
import platform
import sys
import time
from pathlib import Path

import numpy as np
import psutil
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config  # noqa: E402
from src.indexation.embeddings import ENCODEURS_IMAGE  # noqa: E402
from src.indexation.qdrant_store import TYPES_IMAGE  # noqa: E402
from src.ingestion.pipeline import charger_elements  # noqa: E402
from src.recherche.evaluation import mrr_at_k, parser_attendus, rang_premier_bon  # noqa: E402

CSV_BENCH = config.RACINE / "eval" / "benchmark_outils.csv"
COLONNES = ["composant", "option", "version", "qualite", "temps", "memoire", "licence", "machine", "decision", "commentaire"]


def evaluer(nom: str, elements: list[dict], requetes: list[dict]) -> dict:
    proc = psutil.Process()
    gc.collect()
    rss0 = proc.memory_info().rss
    t0 = time.perf_counter()
    enc = ENCODEURS_IMAGE[nom]()
    t_chargement = time.perf_counter() - t0
    t1 = time.perf_counter()
    vecs = []
    for i in range(0, len(elements), 16):
        vecs.append(enc.encoder_images([Image.open(config.DATA_DIR / e["chemin_image"]) for e in elements[i:i + 16]]))
    mat = np.vstack(vecs)
    t_images = time.perf_counter() - t1
    t2 = time.perf_counter()
    q = enc.encoder_textes([r["requete"] for r in requetes])
    t_requetes = (time.perf_counter() - t2) / len(requetes)
    pic = proc.memory_info().rss
    rangs, details = [], []
    for r, qv in zip(requetes, q):
        ordre = np.argsort(-(mat @ qv))[:10]
        res = [elements[i] for i in ordre]
        rang = rang_premier_bon(res, parser_attendus(r["elements_attendus"]))
        rangs.append(rang)
        details.append((r["requete_id"], rang, res[0]["element_id"]))
    out = {"nom": nom, "versions": enc.versions, "licence": enc.licence,
           "top5": sum(1 for x in rangs if x and x <= 5), "n": len(requetes), "mrr": mrr_at_k(rangs, 10),
           "t_chargement": t_chargement, "t_images": t_images, "n_images": len(elements),
           "t_requete_ms": t_requetes * 1000, "memoire_mo": (pic - rss0) / 1e6, "details": details}
    del enc
    gc.collect()
    return out


def main():
    elements = [e for e in charger_elements() if e["type_element"] in TYPES_IMAGE and e.get("chemin_image")]
    requetes = list(csv.DictReader(open(config.RACINE / "eval" / "requetes_visuelles.csv", encoding="utf-8")))
    resultats = []
    for nom in ENCODEURS_IMAGE:
        print(f"== {nom}")
        try:
            r = evaluer(nom, elements, requetes)
        except Exception as e:
            print(f"   impossible : {e}")
            continue
        resultats.append(r)
        print(f"   top5 {r['top5']}/{r['n']} | MRR@10 {r['mrr']:.3f} | {r['n_images']} images en {r['t_images']:.0f} s "
              f"| chargement {r['t_chargement']:.0f} s | {r['memoire_mo']:.0f} Mo")
        for rid, rang, top1 in r["details"]:
            print(f"     {rid} rang {rang or '-':>2}  (1er : {top1})")
    if not resultats:
        return
    meilleur = max(resultats, key=lambda r: (r["top5"], r["mrr"]))
    lignes = []
    if CSV_BENCH.exists():
        with open(CSV_BENCH, encoding="utf-8", newline="") as f:
            lignes = [l for l in csv.DictReader(f) if l["composant"] != "Encodeur texte-image"]
    machine = f"{platform.system()} {platform.machine()}, {psutil.cpu_count()} cœurs, sans GPU"
    for r in resultats:
        lignes.append({"composant": "Encodeur texte-image", "option": r["nom"], "version": r["versions"],
                       "qualite": f"{r['top5']}/{r['n']} requêtes visuelles en français avec une image attendue "
                                  f"dans le top 5 ; MRR@10 {r['mrr']:.3f}",
                       "temps": f"{r['t_images']:.0f} s pour {r['n_images']} images ; {r['t_requete_ms']:.0f} ms par "
                                f"requête ; chargement {r['t_chargement']:.0f} s",
                       "memoire": f"{r['memoire_mo']:.0f} Mo (pic RSS)", "licence": r["licence"], "machine": machine,
                       "decision": "Retenu" if r is meilleur else "Écarté", "commentaire": ""})
    with open(CSV_BENCH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        w.writerows(lignes)
    print(f"-> {CSV_BENCH} (retenu : {meilleur['nom']} ; à reporter dans .env : MAINTIDOC_ENCODEUR_IMAGE)")


if __name__ == "__main__":
    main()

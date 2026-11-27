"""Benchmark OCR (exigé par les consignes) : au moins 2 moteurs sur les documents scannés du corpus.

Mêmes pages, même machine, même résolution (144 dpi). Critères :
- qualité : exactitude caractères (1 - CER) et mots corrects, par rapport au texte d'origine
  des documents (eval/ocr_reference, extrait des PDF sources avant numérisation simulée) ;
  + faits clés retrouvés (valeurs qui servent aux tests : 25 N·m, 8 heures…) ;
- temps de traitement ; mémoire (pic RSS du processus) ; licence.

Usage : python scripts/benchmark_ocr.py [--moteurs rapidocr tesseract]
Résultat : lignes « OCR » ajoutées/mises à jour dans eval/benchmark_outils.csv
"""
from __future__ import annotations

import argparse
import csv
import platform
import sys
import time
import unicodedata
from pathlib import Path

import fitz
import psutil
from PIL import Image
from rapidfuzz.distance import Levenshtein

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config  # noqa: E402
from src.ingestion.ocr import MOTEURS  # noqa: E402

DOCS_SCANNES = {"proc_vidange_a_v1": "famille_1", "proc_purge_comp_b_v1": "famille_2", "manuel_comp_p": "famille_2"}
FAITS_CLES = {"proc_vidange_a_v1": ["25 N·m", "PR-POMPE-07", "0,4 L"],
              "proc_purge_comp_b_v1": ["8 heures", "PR-COMP-05", "10 secondes"],
              "manuel_comp_p": ["500 h", "270 L", "COMP-P-03"]}
PHOTOS_FAITS = {"photo_panneau_pompe_a": ["P-12", "HF-200", "TEMP"],
                "photo_plaque_pompe_a": ["HF2-21-0347", "POMPE-A-01", "HF-200"],
                "photo_ecran_alarme_comp_b": ["C-07", "AT-37", "ENTRETIEN"]}
LICENCES = {"rapidocr": "Apache 2.0 (modèles PaddleOCR : Apache 2.0)", "tesseract": "Apache 2.0"}
REF_DIR = config.RACINE / "eval" / "ocr_reference"
CSV_BENCH = config.RACINE / "eval" / "benchmark_outils.csv"
COLONNES = ["composant", "option", "version", "qualite", "temps", "memoire", "licence", "machine", "decision", "commentaire"]


def normaliser(t: str, accents: bool = True) -> str:
    t = t.replace("·", ".").replace("–", "-").replace("’", "'")
    if not accents:
        t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    return " ".join(t.lower().split())


def pages_scannees():
    for did, fam in DOCS_SCANNES.items():
        pdf = fitz.open(config.CORPUS_DIR / "documents" / fam / f"{did}.pdf")
        for i, page in enumerate(pdf):
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            ref = (REF_DIR / f"{did}_p{i + 1:02d}.txt").read_text(encoding="utf-8")
            yield did, i + 1, img, ref


def evaluer(nom: str, pages) -> dict:
    proc = psutil.Process()
    rss0 = proc.memory_info().rss
    t0 = time.perf_counter()
    moteur = MOTEURS[nom]()
    pic = proc.memory_info().rss
    sorties = {}
    for did, n, img, ref in pages:
        sorties[(did, n)] = (moteur.texte(img), ref)
        pic = max(pic, proc.memory_info().rss)
    duree = time.perf_counter() - t0
    acc_c, acc_c_sans, mots_ok, mots_tot, faits_ok = [], [], 0, 0, 0
    for (did, n), (hyp, ref) in sorties.items():
        acc_c.append(1 - Levenshtein.normalized_distance(normaliser(hyp), normaliser(ref)))
        acc_c_sans.append(1 - Levenshtein.normalized_distance(normaliser(hyp, False), normaliser(ref, False)))
        mots_hyp = set(normaliser(hyp).split())
        mots_ref = normaliser(ref).split()
        mots_ok += sum(1 for m in mots_ref if m in mots_hyp)
        mots_tot += len(mots_ref)
    for did, faits in FAITS_CLES.items():
        texte_doc = normaliser(" ".join(h for (d, _), (h, _) in sorties.items() if d == did))
        texte_doc_compact = texte_doc.replace(" ", "")
        faits_ok += sum(1 for f in faits if normaliser(f).replace(" ", "") in texte_doc_compact)
    n_faits = sum(len(v) for v in FAITS_CLES.values())
    # texte lisible sur les photos (afficheurs, plaques signalétiques)
    t1 = time.perf_counter()
    photos_ok = 0
    for did, faits in PHOTOS_FAITS.items():
        lu = moteur.texte(Image.open(config.CORPUS_DIR / "images" / f"{did}.jpg")).replace(" ", "").upper()
        photos_ok += sum(1 for f in faits if f.replace(" ", "").upper() in lu)
    duree_photos = time.perf_counter() - t1
    n_photos = sum(len(v) for v in PHOTOS_FAITS.values())
    return {"moteur": nom, "pages": len(sorties), "photos": f"{photos_ok}/{n_photos}",
            "photos_ok": photos_ok, "duree_photos": duree_photos, "exactitude_car": sum(acc_c) / len(acc_c),
            "exactitude_car_sans_accents": sum(acc_c_sans) / len(acc_c_sans),
            "mots_corrects": mots_ok / mots_tot, "faits": f"{faits_ok}/{n_faits}",
            "temps_s": duree, "memoire_mo": (pic - rss0) / 1e6}


def version_moteur(nom: str) -> str:
    from importlib.metadata import version
    if nom == "rapidocr":
        return f"rapidocr-onnxruntime {version('rapidocr-onnxruntime')}"
    try:
        import pytesseract
        if config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
        return f"Tesseract {pytesseract.get_tesseract_version()} (fra) / pytesseract {version('pytesseract')}"
    except Exception:
        return "Tesseract"


def ecrire_csv(resultats: list[dict]):
    lignes = []
    if CSV_BENCH.exists():
        with open(CSV_BENCH, encoding="utf-8", newline="") as f:
            lignes = [l for l in csv.DictReader(f) if l["composant"] not in ("OCR", "OCR pages scannées", "OCR photos")]
    machine = f"{platform.system()} {platform.machine()}, {psutil.cpu_count()} cœurs, sans GPU"
    best_pages = max(resultats, key=lambda r: (r["mots_corrects"], r["exactitude_car"]))
    best_photos = max(resultats, key=lambda r: r["photos_ok"])
    for r in resultats:
        lignes.append({
            "composant": "OCR pages scannées", "option": r["moteur"], "version": version_moteur(r["moteur"]),
            "qualite": (f"mots corrects {r['mots_corrects']:.1%} ; exactitude caractères {r['exactitude_car']:.1%} "
                        f"({r['exactitude_car_sans_accents']:.1%} sans accents) ; faits clés {r['faits']} "
                        f"({r['pages']} pages des 3 documents scannés)"),
            "temps": f"{r['temps_s']:.1f} s pour {r['pages']} pages (chargement inclus)",
            "memoire": f"{r['memoire_mo']:.0f} Mo (pic RSS)", "licence": LICENCES[r["moteur"]], "machine": machine,
            "decision": "Retenu" if r is best_pages else "Écarté", "commentaire": ""})
    for r in resultats:
        lignes.append({
            "composant": "OCR photos", "option": r["moteur"], "version": version_moteur(r["moteur"]),
            "qualite": f"textes clés lus {r['photos']} (codes d'alarme, n° de série, modèle sur 3 photos)",
            "temps": f"{r['duree_photos']:.1f} s pour 3 photos", "memoire": "voir ligne pages scannées",
            "licence": LICENCES[r["moteur"]], "machine": machine,
            "decision": "Retenu" if r is best_photos else "Écarté", "commentaire": ""})
    CSV_BENCH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_BENCH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        w.writeheader()
        w.writerows(lignes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--moteurs", nargs="+", default=list(MOTEURS))
    args = ap.parse_args()
    pages = list(pages_scannees())
    resultats = []
    for nom in args.moteurs:
        try:
            r = evaluer(nom, pages)
        except Exception as e:  # moteur absent (ex. binaire tesseract non installé)
            print(f"{nom} : impossible ({e})")
            continue
        resultats.append(r)
        print(f"{nom:10s} car {r['exactitude_car']:.1%} | sans accents {r['exactitude_car_sans_accents']:.1%} | "
              f"mots {r['mots_corrects']:.1%} | faits {r['faits']} | {r['temps_s']:.1f} s | {r['memoire_mo']:.0f} Mo "
              f"| photos {r['photos']}")
    if resultats:
        ecrire_csv(resultats)
        print(f"-> {CSV_BENCH}")


if __name__ == "__main__":
    main()

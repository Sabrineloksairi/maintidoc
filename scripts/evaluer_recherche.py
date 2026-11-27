"""Évaluation de la recherche sur eval/questions_test.csv (20 questions), deux configurations :
  - texte        : recherche texte seul (BGE-M3)
  - texte_images : recherche texte + images (CLIP) + photo, fusion RRF

Pour chaque question : rang du premier élément attendu (top 10), succès dans le top 5, 5 premiers résultats.
Questions « acces » : succès si aucun résultat n'appartient à un groupe interdit à l'utilisateur
(elles sont exclues de Recall@5 / MRR@10, qui mesurent la pertinence).

Bonus : Recall@5 et MRR@10 calculés pour les deux configurations.
Comparaison supplémentaire : « texte_images_rrf_egal » = première version de la fusion (poids égaux,
20 candidats visuels, tout le texte OCR de la photo ajouté à la question).

Usage : python scripts/evaluer_recherche.py   (index déjà construit avec scripts/ingest.py)
Sorties : eval/resultats_evaluation.csv, eval/metriques.json
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config  # noqa: E402
from src.acces.controle import peut_consulter  # noqa: E402
from src.recherche.evaluation import mrr_at_k, parser_attendus, rang_premier_bon, recall_at_k  # noqa: E402
from src.recherche.moteur import VARIANTES as MODES, rechercher  # noqa: E402

EVAL = config.RACINE / "eval"


def main():
    questions = list(csv.DictReader(open(EVAL / "questions_test.csv", encoding="utf-8")))
    lignes, rangs = [], {m: [] for m in MODES}
    acces_ok = {m: 0 for m in MODES}
    n_acces = sum(1 for q in questions if q["type_question"] == "acces")
    durees = {m: [] for m in MODES}
    for q in questions:
        photo = Image.open(EVAL / q["photo"]) if q["photo"] else None
        attendus = parser_attendus(q["elements_attendus"])
        ligne = {k: q[k] for k in ("question_id", "question", "photo", "utilisateur", "elements_attendus", "type_question")}
        for mode in MODES:
            t = time.perf_counter()
            res = rechercher(q["question"], q["utilisateur"], photo=photo, mode=mode, k=10)
            durees[mode].append(time.perf_counter() - t)
            rs = [vars(r) for r in res["resultats"]]
            top5 = " ; ".join(f"{r['document_id']}{' p.' + str(r['page']) if r['page'] else ''} [{r['type_element']}]"
                              for r in rs[:5])
            if q["type_question"] == "acces":
                ok = all(peut_consulter(q["utilisateur"], r) for r in rs)
                acces_ok[mode] += ok
                ligne[f"{mode}_rang"] = ""
                ligne[f"{mode}_top5_ok"] = "acces_respecte" if ok else "FUITE"
            else:
                rang = rang_premier_bon(rs, attendus)
                rangs[mode].append(rang)
                ligne[f"{mode}_rang"] = rang or ""
                ligne[f"{mode}_top5_ok"] = "oui" if rang and rang <= 5 else "non"
            ligne[f"{mode}_top5"] = top5
            if mode == "texte_images":
                ligne["texte_lu_sur_photo"] = res["texte_lu_sur_photo"]
                ligne["requete_texte_finale"] = res["requete_texte"]
        lignes.append(ligne)
        print(f"{q['question_id']} {q['type_question']:14s} texte: {ligne['texte_top5_ok']:14s} "
              f"rang {str(ligne['texte_rang']):3s} | texte+images: {ligne['texte_images_top5_ok']:14s} "
              f"rang {str(ligne['texte_images_rang']):3s} | (RRF égal : rang {ligne['texte_images_rrf_egal_rang']})")

    champs = ["question_id", "question", "photo", "utilisateur", "elements_attendus", "type_question",
              "texte_top5_ok", "texte_rang", "texte_top5", "texte_images_top5_ok", "texte_images_rang",
              "texte_images_top5", "texte_lu_sur_photo", "requete_texte_finale",
              "texte_images_rrf_egal_top5_ok", "texte_images_rrf_egal_rang", "texte_images_rrf_egal_top5"]
    with open(EVAL / "resultats_evaluation.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerows(lignes)

    met = {"nb_questions": len(questions), "nb_questions_pertinence": len(rangs["texte"]),
           "nb_questions_acces": n_acces, "encodeur_texte": config.MODELE_TEXTE,
           "encodeur_image": config.ENCODEUR_IMAGE, "factice": config.EMBEDDINGS_FACTICES}
    for m in MODES:
        met[m] = {"recall@5": round(recall_at_k(rangs[m], 5), 3), "mrr@10": round(mrr_at_k(rangs[m], 10), 3),
                  "succes_top5": sum(1 for r in rangs[m] if r and r <= 5),
                  "acces_respecte": f"{acces_ok[m]}/{n_acces}",
                  "latence_mediane_s": round(sorted(durees[m])[len(durees[m]) // 2], 2)}
    # détail par type de question
    types = sorted({q["type_question"] for q in questions if q["type_question"] != "acces"})
    qs = [q for q in questions if q["type_question"] != "acces"]
    for m in MODES:
        met[m]["recall@5_par_type"] = {
            t: round(recall_at_k([r for q, r in zip(qs, rangs[m]) if q["type_question"] == t], 5), 3) for t in types}
    (EVAL / "metriques.json").write_text(json.dumps(met, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n                       Recall@5   MRR@10   succès top5   accès respecté")
    for m in MODES:
        print(f"{m:22s} {met[m]['recall@5']:8.3f} {met[m]['mrr@10']:8.3f}   "
              f"{met[m]['succes_top5']:3d}/{len(rangs[m])}        {met[m]['acces_respecte']}")
    print("-> eval/resultats_evaluation.csv, eval/metriques.json")


if __name__ == "__main__":
    main()

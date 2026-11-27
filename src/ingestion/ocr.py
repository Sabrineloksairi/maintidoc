"""OCR local. Deux moteurs comparés par le benchmark : Tesseract (retenu) et RapidOCR.

Chaque moteur renvoie une liste de lignes (texte, boîte [x0, y0, x1, y1] en pixels, confiance).
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
from PIL import Image

from src import config


class MoteurOCR:
    nom = "base"

    def lire(self, image: Image.Image) -> list[dict]:  # pragma: no cover - interface
        raise NotImplementedError

    def texte(self, image: Image.Image) -> str:
        return "\n".join(l["texte"] for l in self.lire(image))


class RapidOCRMoteur(MoteurOCR):
    """RapidOCR (modèles PaddleOCR convertis en ONNX, inclus dans le paquet pip) – Apache 2.0."""
    nom = "rapidocr"

    def __init__(self):
        from rapidocr_onnxruntime import RapidOCR
        self._ocr = RapidOCR()

    def lire(self, image):
        resultat, _ = self._ocr(np.asarray(image.convert("RGB")))
        lignes = []
        for boite, texte, conf in resultat or []:
            xs = [p[0] for p in boite]
            ys = [p[1] for p in boite]
            lignes.append({"texte": texte, "bbox": [min(xs), min(ys), max(xs), max(ys)],
                           "confiance": float(conf)})
        # ordre de lecture : de haut en bas puis de gauche à droite
        lignes.sort(key=lambda l: (round(l["bbox"][1] / 12), l["bbox"][0]))
        return lignes


class TesseractMoteur(MoteurOCR):
    """Tesseract 5 (langue fra) via pytesseract – Apache 2.0. Nécessite le binaire tesseract."""
    nom = "tesseract"

    def __init__(self):
        import pytesseract
        if config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD
        self._pt = pytesseract

    def lire(self, image):
        d = self._pt.image_to_data(image.convert("L"), lang="fra", config="--psm 3",
                                   output_type=self._pt.Output.DICT)
        lignes: dict[tuple, dict] = {}
        for i, mot in enumerate(d["text"]):
            if not mot.strip() or float(d["conf"][i]) < 0:
                continue
            cle = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
            x, y, w, h = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
            l = lignes.setdefault(cle, {"mots": [], "bbox": [x, y, x + w, y + h], "conf": []})
            l["mots"].append(mot)
            l["conf"].append(float(d["conf"][i]) / 100)
            b = l["bbox"]
            l["bbox"] = [min(b[0], x), min(b[1], y), max(b[2], x + w), max(b[3], y + h)]
        return [{"texte": " ".join(l["mots"]), "bbox": l["bbox"],
                 "confiance": sum(l["conf"]) / len(l["conf"])} for l in lignes.values()]


MOTEURS = {"rapidocr": RapidOCRMoteur, "tesseract": TesseractMoteur}


@lru_cache(maxsize=4)
def obtenir_moteur(nom: str | None = None) -> MoteurOCR:
    """Renvoie le moteur demandé ; si Tesseract n'est pas installé, repli sur RapidOCR."""
    nom = nom or config.OCR_MOTEUR
    if nom not in MOTEURS:
        raise ValueError(f"Moteur OCR inconnu : {nom} (choix : {', '.join(MOTEURS)})")
    moteur = MOTEURS[nom]()
    if nom == "tesseract":
        try:
            langues = moteur._pt.get_languages(config="")
        except Exception as e:  # binaire absent
            print(f"[OCR] Tesseract indisponible ({e.__class__.__name__}) : repli sur RapidOCR")
            return RapidOCRMoteur()
        if "fra" not in langues:
            print("[OCR] Tesseract sans le pack de langue « fra » : repli sur RapidOCR")
            return RapidOCRMoteur()
    return moteur

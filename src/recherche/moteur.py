"""Recherche multimodale avec fusion RRF.

Configurations comparées (évaluation 2.5) :
- "texte"        : recherche BGE-M3 sur l'index textuel uniquement (la photo est ignorée) ;
- "texte_images" : + recherche texte→image (encodeur CLIP) sur l'index visuel
                   + si photo : recherche image→image, et identifiants lus sur la photo (OCR : codes
                     d'alarme, modèles, repères) ajoutés à la question,
                   puis fusion Reciprocal Rank Fusion pondérée : score(e) = Σ_listes w_liste / (k + rang).
Variante "texte_images_rrf_egal" (comparaison du rapport) : poids égaux, 20 candidats par liste,
tout le texte OCR de la photo ajouté à la question (première version, moins bonne).
Le filtre d'accès est passé à CHAQUE appel Qdrant (avant la recherche).
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from PIL import Image

from src import config
from src.acces.controle import filtre_qdrant, groupes_de
from src.indexation.embeddings import encodeur_image, encodeur_texte
from src.indexation.qdrant_store import client

MODES = ("texte", "texte_images")
VARIANTES = MODES + ("texte_images_rrf_egal",)
IDENTIFIANT = re.compile(r"\b[A-Z][A-Z0-9]{0,5}(?:-[A-Z0-9]{1,5})+\b")     # P-12, C-07, HF-200, POMPE-A-01, HF2-21-0347…


@dataclass
class Resultat:
    rang: int
    element_id: str
    document_id: str
    page: int | None
    type_element: str
    extrait: str
    score_rrf: float
    listes: dict = field(default_factory=dict)      # liste -> rang dans cette liste
    chemin_image: str | None = None
    titre_document: str = ""
    version: str = ""
    legende: str = ""
    groupes_acces: list = field(default_factory=list)

    def citation(self) -> str:
        p = f" p.{self.page}" if self.page else ""
        return f"{self.document_id}{p} ({self.type_element})"


def _chercher(collection: str, vecteur, utilisateur: str, limite: int):
    reponse = client().query_points(collection, query=list(map(float, vecteur)),
                                    query_filter=filtre_qdrant(utilisateur), limit=limite, with_payload=True)
    return reponse.points


def fusion_rrf(listes: dict[str, list], k: int = config.RRF_K,
               poids: dict[str, float] | None = None) -> list[tuple[str, float, dict, dict]]:
    scores: dict[str, float] = {}
    payloads: dict[str, dict] = {}
    rangs: dict[str, dict] = {}
    for nom, points in listes.items():
        w = (poids or {}).get(nom, 1.0)
        for rang, p in enumerate(points, 1):
            eid = p.payload["element_id"]
            scores[eid] = scores.get(eid, 0.0) + w / (k + rang)
            payloads.setdefault(eid, p.payload)
            rangs.setdefault(eid, {})[nom] = rang
    ordre = sorted(scores, key=lambda e: -scores[e])
    return [(eid, scores[eid], payloads[eid], rangs[eid]) for eid in ordre]


def identifiants(texte: str) -> str:
    """Garde seulement les identifiants (codes d'alarme, modèles, repères) d'un texte OCR."""
    vus = []
    for m in IDENTIFIANT.findall(texte.upper()):
        if m not in vus:
            vus.append(m)
    return " ".join(vus)


def texte_photo(photo: Image.Image) -> str:
    """Texte lisible sur la photo (afficheur, plaque) via l'OCR retenu."""
    from src.ingestion.ocr import obtenir_moteur
    lignes = [l["texte"] for l in obtenir_moteur(config.OCR_PHOTO).lire(photo) if l.get("confiance", 1) >= 0.6]
    return " ".join(lignes)


def rechercher(question: str, utilisateur: str, photo: Image.Image | None = None, mode: str = "texte_images",
               k: int = config.TOP_K, candidats: int = config.CANDIDATS_PAR_LISTE) -> dict:
    if mode not in VARIANTES:
        raise ValueError(f"mode inconnu : {mode}")
    groupes = groupes_de(utilisateur)               # lève UtilisateurInconnu avant toute recherche
    t0 = time.perf_counter()
    listes: dict[str, list] = {}
    texte_lu = ""
    requete_texte = question
    naive = mode == "texte_images_rrf_egal"
    if mode != "texte" and photo is not None:
        texte_lu = texte_photo(photo)
        ajout = texte_lu if naive else identifiants(texte_lu)
        if ajout:
            requete_texte = f"{question} {ajout}"

    listes["texte"] = _chercher(config.COLLECTION_TEXTE, encodeur_texte().encoder([requete_texte])[0],
                                utilisateur, candidats)
    if mode != "texte":
        enc = encodeur_image()
        n_vis = candidats if naive else config.CANDIDATS_VISUELS
        listes["texte→image"] = _chercher(config.COLLECTION_IMAGES, enc.encoder_textes([question])[0],
                                          utilisateur, n_vis)
        if photo is not None:
            listes["photo→image"] = _chercher(config.COLLECTION_IMAGES, enc.encoder_images([photo])[0],
                                              utilisateur, n_vis)

    fusion = fusion_rrf(listes, poids=None if naive else config.POIDS_RRF)
    resultats = [Resultat(rang=i, element_id=eid, document_id=p["document_id"], page=p.get("page"),
                          type_element=p["type_element"], extrait=" ".join(p.get("texte", "").split())[:300],
                          score_rrf=round(s, 5), listes=r, chemin_image=p.get("chemin_image"),
                          titre_document=p.get("titre_document", ""), version=p.get("version", ""),
                          legende=p.get("legende", ""), groupes_acces=p.get("groupes_acces", []))
                 for i, (eid, s, p, r) in enumerate(fusion[:k], 1)]
    return {"question": question, "utilisateur": utilisateur, "groupes": groupes, "mode": mode,
            "photo": photo is not None, "texte_lu_sur_photo": texte_lu,
            "requete_texte": requete_texte, "resultats": resultats,
            "duree_ms": round((time.perf_counter() - t0) * 1000)}

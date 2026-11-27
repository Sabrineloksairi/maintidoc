"""API FastAPI de recherche (livrable 2).

Lancement : uvicorn src.api:app --reload
Identification simplifiée : en-tête HTTP « X-Utilisateur » (un identifiant de config/utilisateurs.yaml).
L'authentification par jeton est prévue en semaine 4.
"""
from __future__ import annotations

import io

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import Response
from PIL import Image

from src.acces.controle import AccesRefuse, UtilisateurInconnu, groupes_de, lire_fichier
from src.recherche.moteur import MODES, rechercher

app = FastAPI(title="MaintiDoc – recherche multimodale", version="0.2-L2")


def _verifier(utilisateur: str | None) -> str:
    if not utilisateur:
        raise HTTPException(401, "En-tête X-Utilisateur manquant")
    try:
        groupes_de(utilisateur)
    except UtilisateurInconnu:
        raise HTTPException(401, "Utilisateur inconnu")
    return utilisateur


@app.get("/sante")
def sante():
    return {"statut": "ok"}


@app.post("/search")
async def search(question: str = Form(...), mode: str = Form("texte_images"), k: int = Form(5),
                 photo: UploadFile | None = File(None), x_utilisateur: str | None = Header(None)):
    utilisateur = _verifier(x_utilisateur)
    if mode not in MODES:
        raise HTTPException(422, f"mode doit valoir {MODES}")
    image = Image.open(io.BytesIO(await photo.read())) if photo is not None and photo.filename else None
    r = rechercher(question, utilisateur, photo=image, mode=mode, k=min(max(k, 1), 20))
    r["resultats"] = [{**vars(x), "citation": x.citation(),
                       "url_image": f"/elements/{x.element_id}/image" if x.chemin_image else None}
                      for x in r["resultats"]]
    return r


@app.get("/elements/{element_id}/image")
def image(element_id: str, x_utilisateur: str | None = Header(None)):
    return _fichier(element_id, x_utilisateur, "image")


@app.get("/elements/{element_id}/page")
def page(element_id: str, x_utilisateur: str | None = Header(None)):
    return _fichier(element_id, x_utilisateur, "page")


def _fichier(element_id: str, x_utilisateur: str | None, quoi: str):
    utilisateur = _verifier(x_utilisateur)
    try:
        contenu, mime = lire_fichier(utilisateur, element_id, quoi)
        return Response(content=contenu, media_type=mime)
    except AccesRefuse:
        raise HTTPException(403, "Accès refusé")
    except FileNotFoundError:
        raise HTTPException(404, "Introuvable")

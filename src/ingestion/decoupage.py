"""Découpage du texte d'une page en passages recherchables.

Choix (justifié dans le rapport et la veille) :
- découpage structurel d'abord : une page de nos manuels = un chapitre ; on coupe sur les
  paragraphes et on ne mélange jamais deux pages (citations « document + page » exactes) ;
- puis taille cible de ~900 caractères (≈ 200-250 tokens BGE-M3) : assez court pour qu'un
  passage traite d'un seul sujet (un voyant, une étape), assez long pour garder le contexte ;
- chevauchement de ~150 caractères entre passages consécutifs d'une même page, pour ne pas
  couper une consigne en deux.
"""
from __future__ import annotations

import re

from src import config


def nettoyer(texte: str) -> str:
    texte = texte.replace("­", "")                 # césures invisibles
    texte = re.sub(r"[ \t]+", " ", texte)
    texte = re.sub(r"\n{3,}", "\n\n", texte)
    return texte.strip()


def decouper(texte: str, taille: int | None = None, chevauchement: int | None = None) -> list[str]:
    taille = taille or config.TAILLE_PASSAGE
    chevauchement = config.CHEVAUCHEMENT if chevauchement is None else chevauchement
    texte = nettoyer(texte)
    if not texte:
        return []
    paragraphes = [p.strip() for p in re.split(r"\n\s*\n|\n(?=[•\-–]|\d+\. )", texte) if p.strip()]
    passages, courant = [], ""
    for para in paragraphes:
        # paragraphe trop long : on le coupe sur les phrases
        morceaux = [para] if len(para) <= taille else re.split(r"(?<=[.;:!?])\s+", para)
        for m in morceaux:
            if courant and len(courant) + len(m) + 1 > taille:
                passages.append(courant.strip())
                reprise = courant[-chevauchement:] if chevauchement else ""
                # on reprend à partir d'un début de mot
                reprise = reprise[reprise.find(" ") + 1:] if " " in reprise else reprise
                courant = (reprise + " " + m).strip()
            else:
                courant = (courant + "\n" + m).strip()
    if courant.strip():
        passages.append(courant.strip())
    return passages

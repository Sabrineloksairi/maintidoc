"""Contrôle d'accès par groupes.

Principe (CP2 du livrable 1) :
1. l'utilisateur est résolu en liste de groupes (config/utilisateurs.yaml) ;
2. la recherche reçoit un filtre Qdrant « groupes_acces ∈ groupes de l'utilisateur » :
   les documents interdits ne sont jamais candidats (filtrage AVANT la recherche) ;
3. l'ouverture d'une image ou d'une page vérifie à nouveau les droits sur l'élément demandé.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from qdrant_client import models

from src import config


class AccesRefuse(PermissionError):
    pass


class UtilisateurInconnu(AccesRefuse):
    pass


@lru_cache(maxsize=1)
def charger_utilisateurs(chemin: str | None = None) -> dict:
    with open(chemin or config.UTILISATEURS_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)["utilisateurs"]


def groupes_de(utilisateur: str) -> list[str]:
    u = charger_utilisateurs().get(utilisateur)
    if not u or not u.get("groupes"):
        raise UtilisateurInconnu(f"Utilisateur inconnu ou sans groupe : {utilisateur!r}")
    return list(u["groupes"])


def filtre_qdrant(utilisateur: str, conditions: list | None = None) -> models.Filter:
    """Filtre appliqué à chaque requête Qdrant : seuls les éléments d'un groupe de l'utilisateur."""
    must = [models.FieldCondition(key="groupes_acces", match=models.MatchAny(any=groupes_de(utilisateur)))]
    return models.Filter(must=must + (conditions or []))


def peut_consulter(utilisateur: str, element: dict) -> bool:
    try:
        groupes = set(groupes_de(utilisateur))
    except UtilisateurInconnu:
        return False
    return bool(groupes & set(element.get("groupes_acces", [])))


def ouvrir_fichier(utilisateur: str, element_id: str, quoi: str = "image") -> Path:
    """Chemin de l'image (ou de la page) d'un élément, seulement si l'utilisateur y a droit.

    Le message d'erreur est identique que l'élément existe ou non, pour ne pas révéler
    l'existence d'un document interdit.
    """
    from src.indexation.qdrant_store import lire_element

    groupes_de(utilisateur)                        # lève UtilisateurInconnu
    element = lire_element(element_id)
    if element is None or not peut_consulter(utilisateur, element):
        raise AccesRefuse(f"Accès refusé à l'élément {element_id!r}")
    rel = element.get("chemin_image" if quoi == "image" else "chemin_page")
    if not rel:
        raise FileNotFoundError(f"Pas de {quoi} pour {element_id}")
    chemin = (config.DATA_DIR / rel).resolve()
    if config.DATA_DIR.resolve() not in chemin.parents:   # pas de sortie du dossier data/
        raise AccesRefuse("Chemin invalide")
    return chemin


def lire_fichier(utilisateur: str, element_id: str, quoi: str = "image") -> tuple[bytes, str]:
    """Octets et type MIME de l'image (ou de la page) d'un élément, après contrôle des droits.
    Les fichiers viennent de MinIO si configuré, sinon du dossier data/."""
    from src.indexation.qdrant_store import lire_element
    from src.indexation.stockage import lire_objet, type_mime

    groupes_de(utilisateur)                        # lève UtilisateurInconnu
    element = lire_element(element_id)
    if element is None or not peut_consulter(utilisateur, element):
        raise AccesRefuse(f"Accès refusé à l'élément {element_id!r}")
    cle = element.get("chemin_image" if quoi == "image" else "chemin_page")
    if not cle:
        raise FileNotFoundError(f"Pas de {quoi} pour {element_id}")
    return lire_objet(cle), type_mime(cle)

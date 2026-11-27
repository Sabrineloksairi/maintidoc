"""Lecture de corpus/inventaire.csv : source unique des métadonnées des documents."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


def _liste(valeur: str) -> list[str]:
    """'a ; b' -> ['a', 'b'] (séparateur imposé par les consignes du livrable 1)."""
    return [v.strip() for v in valeur.split(";") if v.strip()]


@dataclass
class Document:
    document_id: str
    fichier: str
    titre: str
    famille: str
    equipement_id: list[str]
    type_document: str
    version: str
    nb_pages: int
    langue: str
    format: str
    groupes_acces: list[str]
    usage_test: str
    remarques: str = ""
    elements_visuels: str = ""
    chemin: Path = field(default=Path())

    def metadonnees(self) -> dict:
        """Métadonnées recopiées dans chaque élément indexé."""
        return {
            "document_id": self.document_id,
            "titre_document": self.titre,
            "version": self.version,
            "famille": self.famille,
            "equipement_id": self.equipement_id,
            "type_document": self.type_document,
            "langue": self.langue,
            "format": self.format,
            "groupes_acces": self.groupes_acces,
            "usage_test": self.usage_test,
            "fichier": self.fichier,
        }


def charger_inventaire(corpus_dir: Path) -> list[Document]:
    chemin_csv = Path(corpus_dir) / "inventaire.csv"
    docs = []
    with open(chemin_csv, encoding="utf-8", newline="") as f:
        for ligne in csv.DictReader(f):
            docs.append(Document(
                document_id=ligne["document_id"],
                fichier=ligne["fichier"],
                titre=ligne["titre"],
                famille=ligne["famille_equipement"],
                equipement_id=_liste(ligne["equipement_id"]),
                type_document=ligne["type_document"],
                version=ligne["version"],
                nb_pages=int(ligne["nb_pages"]),
                langue=ligne["langue"],
                format=ligne["format"],
                groupes_acces=_liste(ligne["groupe_acces"]),
                usage_test=ligne["usage_test"],
                remarques=ligne.get("remarques", ""),
                elements_visuels=ligne.get("elements_visuels", ""),
                chemin=Path(corpus_dir) / ligne["fichier"],
            ))
    return docs

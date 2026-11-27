"""Métadonnées dans PostgreSQL et fichiers originaux dans MinIO (outils imposés par le cahier des charges).

- PostgreSQL : registre des documents (inventaire) et des éléments extraits (page, type, groupes
  d'accès, légende, lien vers l'image et la page), source de vérité pour l'audit et les semaines 3-4.
- MinIO      : figures, tableaux, pages et photos originaux (bucket « maintidoc »), lus pour l'affichage
  et transmis au modèle vision-langage en semaine 3.
Qdrant garde une copie des métadonnées en charge utile, nécessaire au filtrage AVANT la recherche.

Si POSTGRES_DSN / MINIO_ENDPOINT ne sont pas définis (tests, poste sans Docker), ces étapes sont
ignorées et les fichiers sont lus dans data/.
"""
from __future__ import annotations

import io
import json
import mimetypes
from pathlib import Path

from src import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    document_id   TEXT PRIMARY KEY,
    titre         TEXT NOT NULL,
    famille       TEXT NOT NULL,
    equipement_id TEXT[] NOT NULL,
    type_document TEXT NOT NULL,
    version       TEXT,
    langue        TEXT,
    format        TEXT,
    groupes_acces TEXT[] NOT NULL,
    usage_test    TEXT,
    fichier       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS elements (
    element_id        TEXT PRIMARY KEY,
    document_id       TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    page              INTEGER,
    type_element      TEXT NOT NULL,
    groupes_acces     TEXT[] NOT NULL,
    source_extraction TEXT,
    legende           TEXT,
    texte             TEXT,
    objet_image       TEXT,      -- clé MinIO de l'image de l'élément
    objet_page        TEXT,      -- clé MinIO de l'image de la page d'origine
    bbox              JSONB
);
CREATE INDEX IF NOT EXISTS elements_document ON elements(document_id);
CREATE INDEX IF NOT EXISTS elements_groupes ON elements USING GIN(groupes_acces);
"""


def postgres_actif() -> bool:
    return bool(config.POSTGRES_DSN)


def minio_actif() -> bool:
    return bool(config.MINIO_ENDPOINT)


# ------------------------------------------------------------------ PostgreSQL
def enregistrer_postgres(documents, elements: list[dict]) -> dict:
    import psycopg

    with psycopg.connect(config.POSTGRES_DSN) as cx, cx.cursor() as cur:
        cur.execute(SCHEMA)
        cur.execute("TRUNCATE elements, documents")
        cur.executemany(
            "INSERT INTO documents VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [(d.document_id, d.titre, d.famille, d.equipement_id, d.type_document, d.version, d.langue,
              d.format, d.groupes_acces, d.usage_test, d.fichier) for d in documents])
        cur.executemany(
            "INSERT INTO elements VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            [(e["element_id"], e["document_id"], e.get("page"), e["type_element"], e["groupes_acces"],
              e.get("source_extraction"), e.get("legende"), e["texte"], e.get("chemin_image"),
              e.get("chemin_page"), json.dumps(e.get("bbox")) if e.get("bbox") else None) for e in elements])
        cur.execute("SELECT count(*) FROM documents")
        n_docs = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM elements")
        n_els = cur.fetchone()[0]
    return {"documents": n_docs, "elements": n_els}


# ------------------------------------------------------------------------ MinIO
_minio = None


def client_minio():
    global _minio
    if _minio is None:
        from minio import Minio
        _minio = Minio(config.MINIO_ENDPOINT, access_key=config.MINIO_ACCESS_KEY,
                       secret_key=config.MINIO_SECRET_KEY, secure=config.MINIO_SECURE)
    return _minio


def televerser_minio(elements: list[dict]) -> dict:
    """Envoie dans MinIO chaque image d'élément et chaque image de page (clé = chemin relatif à data/)."""
    c = client_minio()
    if not c.bucket_exists(config.MINIO_BUCKET):
        c.make_bucket(config.MINIO_BUCKET)
    cles = sorted({e[k] for e in elements for k in ("chemin_image", "chemin_page") if e.get(k)})
    octets = 0
    for cle in cles:
        chemin = config.DATA_DIR / cle
        type_mime = mimetypes.guess_type(chemin.name)[0] or "application/octet-stream"
        c.fput_object(config.MINIO_BUCKET, cle, str(chemin), content_type=type_mime)
        octets += chemin.stat().st_size
    return {"objets": len(cles), "mo": round(octets / 1e6, 1)}


def lire_objet(cle: str) -> bytes:
    """Octets d'un fichier original : MinIO si configuré, sinon dossier data/."""
    if minio_actif():
        r = client_minio().get_object(config.MINIO_BUCKET, cle)
        try:
            return r.read()
        finally:
            r.close()
            r.release_conn()
    chemin = (config.DATA_DIR / cle).resolve()
    if config.DATA_DIR.resolve() not in chemin.parents:
        raise PermissionError("Chemin invalide")
    return Path(chemin).read_bytes()


def type_mime(cle: str) -> str:
    return mimetypes.guess_type(cle)[0] or "application/octet-stream"

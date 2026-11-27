"""Extraction des éléments recherchables d'un document du corpus.

Types d'éléments produits :
- passage : morceau de texte d'une page (texte natif PyMuPDF ou OCR) ;
- tableau : tableau détecté par PyMuPDF, converti en Markdown, avec sa légende ;
- figure  : schéma / figure vectorielle ou image intégrée, enregistrée en PNG avec sa légende ;
- page    : page entière d'un PDF scanné (image + texte OCR) ;
- photo   : photographie du corpus (image + texte OCR visible sur la photo).

Chaque élément reçoit les métadonnées de l'inventaire et un lien vers sa page d'origine.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from src import config
from src.ingestion.decoupage import decouper, nettoyer
from src.ingestion.inventaire import Document
from src.ingestion.ocr import MoteurOCR

LEGENDE = re.compile(r"^(Figure|Fig\.|Tableau|Schéma|Courbe)\s*[A-Z]?\d*", re.IGNORECASE)
MARGE_HAUT, MARGE_BAS = 45, 800          # en points : en-tête et pied de page exclus


def _rect_chevauche(a: fitz.Rect, b: fitz.Rect, seuil: float = 0.5) -> bool:
    inter = fitz.Rect(a) & b
    if inter.is_empty:
        return False
    return inter.get_area() / max(min(a.get_area(), b.get_area()), 1) >= seuil


def _legende_proche(blocs, zone: fitz.Rect, tableau: bool = False) -> str:
    """Légende la plus proche sous la zone, à défaut au-dessus.
    Un tableau ne prend qu'une légende « Tableau … », une figure jamais."""
    meilleur, dist_min = "", 1e9
    for x0, y0, x1, y1, txt, *_ in blocs:
        t = " ".join(txt.split())
        if not LEGENDE.match(t) or t.lower().startswith("tableau") != tableau:
            continue
        if y0 >= zone.y1 - 20:                      # légende sous la zone (cas normal)
            d = max(y0 - zone.y1, 0)
        elif y1 <= zone.y0 + 5:                     # légende au-dessus (pénalisée)
            d = (zone.y0 - y1) + 20
        else:
            continue
        if d < 80 and d < dist_min:
            meilleur, dist_min = t, d
    return meilleur


def _est_encadre_texte(zone: fitz.Rect, blocs) -> bool:
    """Cadre tracé autour d'un paragraphe (encadré ⚠) : le texte occupe l'essentiel du cadre."""
    surface_texte = sum((fitz.Rect(b[:4]) & zone).get_area() for b in blocs
                        if fitz.Rect(b[:4]).intersects(zone))
    return surface_texte / max(zone.get_area(), 1) > 0.45


def _fusionner_voisins(rects: list[fitz.Rect], ecart: float = 60) -> list[fitz.Rect]:
    """Regroupe les morceaux d'un même schéma séparés de moins de `ecart` points (cercles et barrettes d'un schéma de câblage, etc.)."""
    rects = [fitz.Rect(r) for r in rects]
    fusion = True
    while fusion:
        fusion = False
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                if (rects[i] + (-ecart, -ecart, ecart, ecart)).intersects(rects[j]):
                    rects[i] |= rects[j]
                    del rects[j]
                    fusion = True
                    break
            if fusion:
                break
    return rects


def _sauver_png(page: fitz.Page, zone: fitz.Rect | None, chemin: Path, zoom: float) -> str:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=zone, alpha=False)
    pix.save(str(chemin))
    return str(chemin.relative_to(config.DATA_DIR)).replace("\\", "/")


def _element(doc: Document, page: int | None, type_el: str, n: int, texte: str, **extra) -> dict:
    suffixe = f"p{page:02d}_" if page else ""
    el = {
        "element_id": f"{doc.document_id}_{suffixe}{type_el}{n:02d}",
        "page": page,
        "type_element": type_el,
        "texte": texte,
        **doc.metadonnees(),
        **extra,
    }
    pg = f"page {page}" if page else ""
    equipements = ", ".join(doc.equipement_id) if doc.equipement_id != ["generique"] else ""
    entete = f"{doc.titre} – {doc.document_id} {pg}" + (f" – équipements : {equipements}" if equipements else "")
    el["texte_indexe"] = f"{entete}\n{texte}".strip()
    return el


def extraire_pdf_texte(doc: Document, ocr: MoteurOCR | None = None) -> list[dict]:
    elements = []
    pdf = fitz.open(doc.chemin)
    for i, page in enumerate(pdf):
        n_page = i + 1
        chemin_page = _sauver_png(page, None, config.PAGES_DIR / doc.document_id / f"p{n_page:02d}.png",
                                  config.ZOOM_PAGE)
        blocs = [b for b in page.get_text("blocks") if b[6] == 0]      # blocs de texte uniquement
        zones_occupees: list[fitz.Rect] = []

        # --- Tableaux -------------------------------------------------------------
        groupes_dessins = [fitz.Rect(r) for r in page.cluster_drawings()]
        tableaux = []
        for tab in page.find_tables().tables:
            zt = fitz.Rect(tab.bbox)
            # une « table » contenue dans un dessin beaucoup plus grand = cases d'un schéma
            if any(g.contains(zt) and g.get_area() > 1.5 * zt.get_area() for g in groupes_dessins):
                continue
            tableaux.append(tab)
        for k, tab in enumerate(tableaux, 1):
            zone = fitz.Rect(tab.bbox)
            legende = _legende_proche(blocs, zone, tableau=True)
            md = tab.to_markdown(clean=True) if hasattr(tab, "to_markdown") else str(tab.extract())
            img = _sauver_png(page, zone + (-4, -4, 4, 4),
                              config.FIGURES_DIR / doc.document_id / f"p{n_page:02d}_tableau{k:02d}.png",
                              config.ZOOM_FIGURE)
            elements.append(_element(doc, n_page, "tableau", k, f"{legende}\n{md}".strip(),
                                     legende=legende, bbox=[round(v, 1) for v in zone],
                                     chemin_image=img, chemin_page=chemin_page, source_extraction="texte"))
            zones_occupees.append(zone)

        # --- Figures (dessins vectoriels regroupés + images intégrées) ---------------
        candidats = []
        for g in groupes_dessins:
            if any(_rect_chevauche(g, t, 0.5) for t in zones_occupees):
                continue                                             # grille d'un tableau
            if _est_encadre_texte(g, blocs):
                continue                                             # encadré d'avertissement
            candidats.append(g)
        candidats = [(z, "dessin") for z in _fusionner_voisins(candidats)]
        candidats += [(fitz.Rect(info["bbox"]), "image") for info in page.get_image_info()]
        k = 0
        for zone, origine in candidats:
            if zone.height < 25 or zone.width < 40 or zone.get_area() < 3000:
                continue                                             # traits, filets d'en-tête
            if zone.y0 < MARGE_HAUT - 10 or zone.y1 > MARGE_BAS + 30:
                continue
            if zone.height < 120 and any(b[4].lstrip().startswith("⚠") and fitz.Rect(b[:4]).intersects(zone)
                                         for b in blocs):
                continue                                             # encadré d'avertissement
            zone_large = fitz.Rect(zone)
            if origine == "dessin":
                # on élargit pour inclure les libellés posés autour du dessin
                zone_large = zone + (-15, -15, 15, 15)
                for x0, y0, x1, y1, txt, *_ in blocs:
                    r = fitz.Rect(x0, y0, x1, y1)
                    if r.intersects(zone) and not LEGENDE.match(" ".join(txt.split())):
                        zone_large |= r
            zone_large &= page.rect
            k += 1
            legende = _legende_proche(blocs, zone_large) or _legende_proche(blocs, zone)
            libelles = " ".join(" ".join(b[4].split()) for b in blocs
                                if fitz.Rect(b[:4]).intersects(zone) and not LEGENDE.match(" ".join(b[4].split())))
            img = _sauver_png(page, zone_large,
                              config.FIGURES_DIR / doc.document_id / f"p{n_page:02d}_figure{k:02d}.png",
                              config.ZOOM_FIGURE)
            elements.append(_element(doc, n_page, "figure", k, f"{legende}\n{libelles}".strip(),
                                     legende=legende, bbox=[round(v, 1) for v in zone_large],
                                     chemin_image=img, chemin_page=chemin_page, source_extraction="texte"))
            zones_occupees.append(zone_large)

        # --- Passages de texte ------------------------------------------------------
        morceaux = []
        for x0, y0, x1, y1, txt, *_ in sorted(blocs, key=lambda b: (b[1], b[0])):
            r = fitz.Rect(x0, y0, x1, y1)
            if y0 < MARGE_HAUT or y0 > MARGE_BAS:
                continue
            if any(_rect_chevauche(r, z, 0.6) for z in zones_occupees):
                continue
            morceaux.append(txt.strip())
        texte_page = nettoyer("\n\n".join(morceaux))

        # Page sans texte natif (cas d'un PDF scanné mal étiqueté) : repli OCR
        if len(texte_page) < 20 and ocr is not None:
            texte_page = nettoyer(ocr.texte(Image.open(config.DATA_DIR / chemin_page)))
            source = "ocr"
        else:
            source = "texte"
        for k, passage in enumerate(decouper(texte_page), 1):
            elements.append(_element(doc, n_page, "passage", k, passage,
                                     chemin_page=chemin_page, source_extraction=source))
    pdf.close()
    return elements


def extraire_pdf_scanne(doc: Document, ocr: MoteurOCR) -> list[dict]:
    """PDF composé d'images de pages : OCR page par page + élément « page » pour l'index visuel."""
    elements = []
    pdf = fitz.open(doc.chemin)
    for i, page in enumerate(pdf):
        n_page = i + 1
        chemin_page = _sauver_png(page, None, config.PAGES_DIR / doc.document_id / f"p{n_page:02d}.png",
                                  config.ZOOM_FIGURE)
        image = Image.open(config.DATA_DIR / chemin_page)
        texte = nettoyer(ocr.texte(image))
        elements.append(_element(doc, n_page, "page", 1, texte[:1500], chemin_image=chemin_page,
                                 chemin_page=chemin_page, source_extraction="ocr"))
        for k, passage in enumerate(decouper(texte), 1):
            elements.append(_element(doc, n_page, "passage", k, passage,
                                     chemin_page=chemin_page, source_extraction="ocr"))
    pdf.close()
    return elements


def extraire_image(doc: Document, ocr: MoteurOCR) -> list[dict]:
    """Photographie : copie de l'original + texte lisible sur la photo (OCR)."""
    dest = config.FIGURES_DIR / doc.document_id / Path(doc.fichier).name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(doc.chemin, dest)
    rel = str(dest.relative_to(config.DATA_DIR)).replace("\\", "/")
    lignes = [l["texte"] for l in ocr.lire(Image.open(doc.chemin)) if l["confiance"] >= 0.6]
    texte = f"{doc.titre}\nTexte visible : {' | '.join(lignes)}" if lignes else doc.titre
    return [_element(doc, None, "photo", 1, texte, chemin_image=rel, chemin_page=rel,
                     source_extraction="image+ocr")]


def extraire_document(doc: Document, ocr: MoteurOCR, ocr_photo: MoteurOCR | None = None) -> list[dict]:
    """ocr : moteur des pages scannées ; ocr_photo : moteur du texte sur photographies."""
    if doc.format == "pdf_texte":
        return extraire_pdf_texte(doc, ocr)
    if doc.format == "pdf_scanne":
        return extraire_pdf_scanne(doc, ocr)
    if doc.format == "image":
        return extraire_image(doc, ocr_photo or ocr)
    raise ValueError(f"{doc.document_id} : format inconnu {doc.format}")

"""Tests automatiques du contrôle d'accès (livrable 2, partie 2.4).

Ils démontrent qu'un utilisateur ne voit jamais un document d'un autre groupe, même quand sa
question le cible directement, et que l'ouverture d'une image ou d'une page est refusée.
Lancement : pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src import config
from src.acces.controle import AccesRefuse, UtilisateurInconnu, groupes_de, ouvrir_fichier
from src.recherche.moteur import MODES, rechercher

QUESTIONS_COMPRESSEURS = [
    "Comment remplacer le filtre à air FA-37 du compresseur AT-37 ?",
    "Que signifie le code C-07 et le voyant orange ENTRETIEN ?",
    "proc_filtre_air_comp_b codes_alarme_comp_b compresseur",
]


def _tous_les_resultats(question, utilisateur, photo=None):
    """Résultats des deux configurations, avec une liste large (20) pour ne rien laisser passer."""
    out = []
    for mode in MODES:
        out += rechercher(question, utilisateur, photo=photo, mode=mode, k=20)["resultats"]
    return out


# 1 -------------------------------------------------------------------------
@pytest.mark.parametrize("question", QUESTIONS_COMPRESSEURS)
def test_technicien_pompes_ne_voit_jamais_un_document_compresseurs(index_test, question):
    resultats = _tous_les_resultats(question, "tech_pompes")
    assert resultats, "la recherche doit renvoyer des documents autorisés"
    for r in resultats:
        assert "techniciens_pompes" in r.groupes_acces, f"fuite : {r.citation()}"
        assert not r.document_id.endswith("comp_b") and "compresseurs" not in r.document_id


# 2 -------------------------------------------------------------------------
def test_question_ciblant_directement_un_document_reserve(index_test):
    """La note de service interne est réservée aux responsables : un technicien compresseurs
    ne la voit pas même en citant son titre et sa référence, un responsable la voit."""
    q = "note de service interne NS-COMP-2025-05 organisation de la maintenance des compresseurs astreinte"
    vus_tech = {r.document_id for r in _tous_les_resultats(q, "tech_compresseurs")}
    assert "note_service_compresseurs" not in vus_tech
    vus_resp = {r.document_id for r in _tous_les_resultats(q, "responsable")}
    assert "note_service_compresseurs" in vus_resp


def test_historique_reserve_aux_responsables(index_test):
    q = "historique des interventions POMPE-A-01 tickets TCK-2025-0047 TCK-2025-0096"
    assert "historique_pompe_a_01" not in {r.document_id for r in _tous_les_resultats(q, "tech_pompes")}
    assert "historique_pompe_a_01" in {r.document_id for r in _tous_les_resultats(q, "responsable")}


# 3 -------------------------------------------------------------------------
def test_une_photo_ne_contourne_pas_le_filtre(index_test):
    """Photo d'un panneau de compresseur envoyée par un technicien pompes."""
    photo = Image.open(config.CORPUS_DIR / "images" / "photo_ecran_alarme_comp_b.jpg")
    resultats = rechercher("Que signifie ce voyant ?", "tech_pompes", photo=photo, mode="texte_images", k=20)
    for r in resultats["resultats"]:
        assert "techniciens_pompes" in r.groupes_acces, f"fuite par la photo : {r.citation()}"


# 4 -------------------------------------------------------------------------
def test_ouverture_image_et_page_refusee(index_test):
    figure_comp = next(e["element_id"] for e in index_test
                       if e["document_id"] == "proc_filtre_air_comp_b" and e.get("chemin_image"))
    figure_pompe = next(e["element_id"] for e in index_test
                        if e["document_id"] == "manuel_pompe_a" and e["type_element"] == "figure")
    for quoi in ("image", "page"):
        with pytest.raises(AccesRefuse):
            ouvrir_fichier("tech_pompes", figure_comp, quoi)
    assert ouvrir_fichier("tech_compresseurs", figure_comp, "image").exists()
    assert ouvrir_fichier("tech_pompes", figure_pompe, "page").exists()
    # même message qu'un élément inexistant : on ne révèle pas l'existence du document
    with pytest.raises(AccesRefuse):
        ouvrir_fichier("tech_pompes", "element_qui_n_existe_pas", "image")


def test_api_refuse_image_interdite_et_utilisateur_inconnu(index_test):
    from src.api import app
    c = TestClient(app)
    figure_comp = next(e["element_id"] for e in index_test
                       if e["document_id"] == "proc_filtre_air_comp_b" and e.get("chemin_image"))
    assert c.get(f"/elements/{figure_comp}/image", headers={"X-Utilisateur": "tech_pompes"}).status_code == 403
    assert c.get(f"/elements/{figure_comp}/image", headers={"X-Utilisateur": "tech_compresseurs"}).status_code == 200
    assert c.post("/search", data={"question": "filtre"}, headers={"X-Utilisateur": "pirate"}).status_code == 401
    r = c.post("/search", data={"question": "filtre à air compresseur", "mode": "texte_images"},
               headers={"X-Utilisateur": "tech_pompes"})
    assert r.status_code == 200
    assert all("techniciens_pompes" in x["groupes_acces"] for x in r.json()["resultats"])


# 5 -------------------------------------------------------------------------
def test_filtre_applique_avant_la_recherche(index_test, monkeypatch):
    """Chaque appel à Qdrant porte le filtre de groupes : le tri ne se fait jamais après coup."""
    from src.indexation import qdrant_store
    vrai_client = qdrant_store.client()
    appels = []
    original = vrai_client.query_points

    def espion(collection, **kwargs):
        appels.append(kwargs.get("query_filter"))
        return original(collection, **kwargs)

    monkeypatch.setattr(vrai_client, "query_points", espion)
    photo = Image.open(config.CORPUS_DIR / "images" / "photo_panneau_pompe_a.jpg")
    rechercher("voyant orange", "tech_compresseurs", photo=photo, mode="texte_images")
    assert len(appels) == 3                          # texte, texte→image, photo→image
    for f in appels:
        cond = f.must[0]
        assert cond.key == "groupes_acces"
        assert set(cond.match.any) == set(groupes_de("tech_compresseurs"))


def test_utilisateur_inconnu_refuse_avant_toute_recherche(index_test):
    with pytest.raises(UtilisateurInconnu):
        rechercher("filtre à air", "inconnu")

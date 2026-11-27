"""Page de test Streamlit de la recherche multimodale MaintiDoc (livrable 2).

Lancement : streamlit run app/recherche_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.acces.controle import AccesRefuse, charger_utilisateurs, lire_fichier  # noqa: E402
from src.recherche.moteur import rechercher  # noqa: E402

st.set_page_config(page_title="MaintiDoc – recherche", page_icon="🔧", layout="wide")


@st.cache_resource(show_spinner="Chargement des modèles…")
def prechauffer():
    from src.indexation.embeddings import encodeur_image, encodeur_texte
    _ = (encodeur_texte(), encodeur_image())   # affectation : évite l'affichage « magique » de Streamlit
    return True


utilisateurs = charger_utilisateurs()
with st.sidebar:
    st.header("Utilisateur (fictif)")
    utilisateur = st.selectbox("Connecté en tant que", list(utilisateurs),
                               format_func=lambda u: f"{u} – {utilisateurs[u]['nom']}")
    st.caption("Groupes : " + ", ".join(utilisateurs[utilisateur]["groupes"]))
    mode = st.radio("Configuration", ["texte_images", "texte"],
                    format_func=lambda m: "Texte + images (fusion RRF)" if m == "texte_images" else "Texte seul")
    st.divider()
    st.subheader("Ouvrir un élément par identifiant")
    eid = st.text_input("element_id", placeholder="ex. proc_filtre_air_comp_b_p01_figure01")
    if st.button("Ouvrir l'image") and eid:
        try:
            st.image(lire_fichier(utilisateur, eid.strip(), "image")[0], caption=eid)
        except AccesRefuse:
            st.error(f"⛔ Accès refusé : {utilisateur} n'a pas le droit de consulter cet élément.")
        except FileNotFoundError:
            st.warning("Cet élément n'a pas d'image.")

st.title("🔧 MaintiDoc – recherche multimodale")
st.caption("Livrable 2 : la recherche renvoie les passages et figures sources. La rédaction de la réponse "
           "par le modèle vision-langage arrive en semaine 3.")
prechauffer()

col_q, col_p = st.columns([3, 1])
with col_q:
    question = st.text_input("Question", placeholder="Que signifie le voyant orange de la pompe A ?")
with col_p:
    fichier = st.file_uploader("Photo (facultatif)", type=["jpg", "jpeg", "png"])
photo = Image.open(fichier) if fichier else None
if photo:
    st.image(photo, width=220, caption="Photo envoyée")

if st.button("Rechercher", type="primary") and question.strip():
    r = rechercher(question, utilisateur, photo=photo, mode=mode)
    st.write(f"**{len(r['resultats'])} résultats** – {r['duree_ms']} ms – filtre : groupes "
             f"`{', '.join(r['groupes'])}`")
    if r["texte_lu_sur_photo"]:
        st.info(f"Texte lu sur la photo (OCR) : {r['texte_lu_sur_photo']}")
    if not r["resultats"]:
        st.warning("Aucun document autorisé ne correspond à la question.")
    for x in r["resultats"]:
        with st.container(border=True):
            c1, c2 = st.columns([1, 3])
            with c1:
                if x.chemin_image:
                    try:
                        st.image(lire_fichier(utilisateur, x.element_id, "image")[0], use_container_width=True)
                    except AccesRefuse:
                        st.error("Image non autorisée")
            with c2:
                st.markdown(f"**#{x.rang} · {x.document_id}{' · page ' + str(x.page) if x.page else ''}** "
                            f"· {x.type_element} · score RRF {x.score_rrf:.4f}")
                st.caption(f"{x.titre_document} – {x.version} – élément `{x.element_id}`")
                if x.legende:
                    st.markdown(f"*{x.legende}*")
                st.write(x.extrait)
                st.caption("Listes : " + ", ".join(f"{k} rang {v}" for k, v in x.listes.items()))

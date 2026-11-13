"""Vérifie la cohérence entre corpus/inventaire.csv et les fichiers du corpus.
Usage (depuis la racine du dépôt) : python outils/verifier_inventaire.py"""
import csv, re, sys
from pathlib import Path

CORPUS = Path(__file__).resolve().parent.parent / "corpus"
COLONNES = ("document_id,fichier,titre,famille_equipement,equipement_id,type_document,version,"
            "nb_pages,langue,format,elements_visuels,provenance,licence,genere_par_ia,outil_ia,"
            "verifie_par,corrections,groupe_acces,usage_test,remarques").split(",")
VALEURS = {"type_document": {"manuel", "procedure", "fiche_securite", "schema", "codes_alarme", "photo", "historique"},
           "langue": {"fr", "en"}, "format": {"pdf_texte", "pdf_scanne", "image"},
           "genere_par_ia": {"oui", "non"}, "usage_test": {"normal", "contradictoire", "injection", "ambigu"},
           "famille_equipement": {"pompes", "compresseurs"}}
erreurs, alertes = [], []

with open(CORPUS / "inventaire.csv", encoding="utf-8", newline="") as f:
    lignes = list(csv.reader(f))
if lignes[0] != COLONNES:
    erreurs.append("En-tête de inventaire.csv différent de celui des consignes")
docs = [dict(zip(lignes[0], l)) for l in lignes[1:]]

ids = [d["document_id"] for d in docs]
for x in {i for i in ids if ids.count(i) > 1}:
    erreurs.append(f"document_id en double : {x}")
for d in docs:
    did = d["document_id"]
    if len(d) != 20:
        erreurs.append(f"{did} : {len(d)} colonnes au lieu de 20")
    if not re.fullmatch(r"[a-z0-9_]+", did):
        erreurs.append(f"{did} : identifiant invalide (minuscules, chiffres et _ uniquement)")
    p = CORPUS / d["fichier"]
    if not p.exists():
        erreurs.append(f"{did} : fichier introuvable {d['fichier']}")
    if Path(d["fichier"]).stem != did:
        erreurs.append(f"{did} : le nom du fichier doit être {did}.<extension>")
    for col, ok in VALEURS.items():
        if d[col] not in ok:
            erreurs.append(f"{did} : valeur « {d[col]} » non autorisée pour {col}")
    if not d["nb_pages"].isdigit():
        erreurs.append(f"{did} : nb_pages doit être un entier")
    if not d["verifie_par"].strip():
        alertes.append(f"{did} : colonne verifie_par vide")

fichiers = {str(p.relative_to(CORPUS)).replace("\\", "/") for p in CORPUS.rglob("*")
            if p.is_file() and p.parent != CORPUS and p.name != ".gitkeep"}
for x in sorted(fichiers - {d["fichier"] for d in docs}):
    erreurs.append(f"fichier présent dans le corpus mais absent de l'inventaire : {x}")

n = len(docs)
compte = lambda col, val: sum(1 for d in docs if d[col] == val)
visuels = sum(1 for d in docs if d["elements_visuels"].strip().lower() not in ("", "aucun") and not d["elements_visuels"].startswith("aucun"))
print(f"Documents : {n} (attendu 30 à 50)")
print(f"  pompes : {compte('famille_equipement', 'pompes')} | compresseurs : {compte('famille_equipement', 'compresseurs')}")
print(f"  avec éléments visuels : {visuels} (min 10) | scannés : {compte('format', 'pdf_scanne')} (min 2)")
print(f"  contradictoires : {compte('usage_test', 'contradictoire')} (min 2) | injection : {compte('usage_test', 'injection')} (min 1) | ambigus : {compte('usage_test', 'ambigu')}")
print(f"  en anglais : {compte('langue', 'en')}")
if not 30 <= n <= 50: erreurs.append("le corpus doit contenir 30 à 50 documents")
if visuels < 10: erreurs.append("moins de 10 documents avec éléments visuels")
if compte("format", "pdf_scanne") < 2: erreurs.append("moins de 2 documents scannés")
if compte("usage_test", "contradictoire") < 2: erreurs.append("moins de 2 documents contradictoires")
if compte("usage_test", "injection") < 1: erreurs.append("aucun document piégé")
for a in alertes:
    print("ALERTE :", a)
for e in erreurs:
    print("ERREUR :", e)
print("\nRésultat :", "OK" if not erreurs else f"{len(erreurs)} erreur(s)", f"– {len(alertes)} alerte(s)")
sys.exit(1 if erreurs else 0)

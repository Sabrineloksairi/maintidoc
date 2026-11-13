# Prompts utilisés pour constituer le corpus MaintiDoc

Équipe ELFAROUKI-HAFFARI-LOKSAIRI

Chaque prompt est numéroté (P01, P02…). La colonne `outil_ia` de `inventaire.csv` renvoie à ces
numéros. Pour chaque prompt : outil, date, auteur, objectif, texte exact, documents produits et
vérification effectuée.

---

## P01 — Référentiel commun du corpus

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Objectif** : définir une base unique (équipements, caractéristiques, voyants, codes d'alarme,
  plan de pages des manuels, contradictions, document piégé, groupes d'accès, historiques) pour
  que tous les documents générés ensuite restent cohérents entre eux.
- **Texte du prompt** :

> Nous constituons le corpus du projet MaintiDoc sur deux familles d'équipements : pompes
> centrifuges et compresseurs d'air. Rédige un référentiel commun, entièrement fictif, contenant :
> le parc d'équipements avec des identifiants stables (2 unités d'un même modèle par famille + un
> modèle différent) ; les caractéristiques techniques réalistes de chaque modèle ; la description
> des panneaux de commande et de leurs voyants, avec un voyant orange présent sur les deux familles
> mais de signification différente ; un tableau de 20 codes d'alarme par modèle principal (code,
> niveau, voyant, signification, cause, action) ; le plan page par page des deux manuels principaux
> avec les figures et tableaux ; deux paires de procédures contradictoires ; le texte d'un document
> piégé contenant une tentative d'injection de prompt ; 3 groupes d'accès et des utilisateurs
> fictifs ; des historiques d'interventions cohérents avec les codes d'alarme.

- **Production** : `docs/referentiel_corpus.md` (document de travail, hors corpus indexé)
- **Vérification** : à compléter par l'équipe (valeurs techniques à contrôler : seuils de
  température, périodicités de vidange, pressions, couples de serrage)
- **Corrections apportées** : à compléter

---

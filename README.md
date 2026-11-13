# MaintiDoc

**Assistant documentaire multimodal et agentique pour la maintenance**
Module IA générative multimodale – EMSI 2026 – Pr. Mariam CHERRABI

## Équipe ELFAROUKI-HAFFARI-LOKSAIRI

| Membre | Rôle principal |
|---|---|
| Abderrahmane ELFAROUKI | Modèles et évaluation (VLM, recherche, reranker, métriques) |
| Aya HAFFARI | Agent, sécurité et intégration (LangGraph, MCP, API, interface) |
| Sabrine LOKSAIRI | Coordination, corpus et données (ingestion, index, métadonnées) |

## Objectif du projet

MaintiDoc aide les techniciens et responsables de maintenance à répondre à des questions
techniques à partir de manuels, procédures, schémas et photographies, en citant les pages et
figures sources. Il consulte l'historique des interventions via un outil MCP et prépare des
tickets de maintenance, dont la création exige une approbation humaine. C'est une aide
documentaire : il ne pilote aucun équipement et ne garantit aucun diagnostic.

Familles d'équipements : **pompes centrifuges** (HF-200, HFM-450) et **compresseurs d'air**
(AT-37, AP-11). Corpus : **36 documents** (34 synthétiques, 2 publics U.S. DOE).

## Livrable 1 – Contenu du ZIP

```
L1_MaintiDoc_ELFAROUKI-HAFFARI-LOKSAIRI/
├── L1_MaintiDoc_ELFAROUKI-HAFFARI-LOKSAIRI_Rapport.pdf     Rapport (parties 2.1 à 2.6)
├── L1_MaintiDoc_ELFAROUKI-HAFFARI-LOKSAIRI_LienGitHub.txt  URL du dépôt GitHub
├── README.md                                               Ce fichier
└── L1_MaintiDoc_ELFAROUKI-HAFFARI-LOKSAIRI_Corpus/
    ├── inventaire.csv · prompts_corpus.md
    ├── documents/famille_1/ (pompes) · documents/famille_2/ (compresseurs)
    └── images/
```

## Structure du dépôt

```
maintidoc/
├── README.md
├── .gitignore                  Exclut secrets et fichiers .env
├── corpus/
│   ├── inventaire.csv          Registre du corpus (une ligne par document)
│   ├── prompts_corpus.md       Prompts IA P01 à P33, outil, date, vérification
│   ├── documents/famille_1/    Pompes centrifuges
│   ├── documents/famille_2/    Compresseurs d'air
│   └── images/                 Photographies de panneaux et plaques
├── docs/
│   ├── referentiel_corpus.md   Référentiel commun (équipements, codes, pages)
│   ├── diagrammes/             Sources Mermaid (.mmd) et images des diagrammes
│   └── rapport/                Rapport du livrable 1
└── outils/
    └── verifier_inventaire.py  Contrôle inventaire ↔ fichiers
```

Contrôle du corpus : `py outils/verifier_inventaire.py`

Utilisateurs, tickets et historiques sont **fictifs** ; aucune donnée personnelle réelle ;
aucun secret versionné.

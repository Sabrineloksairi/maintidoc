# \# MaintiDoc

# 

# \*\*Assistant documentaire multimodal et agentique pour la maintenance\*\*

# Module IA générative multimodale – EMSI 2026 – Pr. Mariam CHERRABI

# 

# \## Équipe ELFAROUKI-HAFFARI-LOKSAIRI

# 

# | Membre | Rôle principal |

# |---|---|

# | <Prénom> ELFAROUKI | Abderrahmane |

# | <Prénom> HAFFARI | Aya |

# | Sabrine LOKSAIRI | Sabrine |

# 

# \## Objectif du projet

# 

# MaintiDoc aide les techniciens et responsables de maintenance à répondre à des questions

# techniques à partir de manuels, procédures, schémas et photographies, en citant les pages et

# figures sources. Il peut consulter l'historique des interventions via un outil MCP et préparer

# un ticket de maintenance, dont la création exige une approbation humaine.

# 

# Le système est une aide documentaire : il ne pilote aucun équipement, ne garantit pas de

# diagnostic et ne remplace ni les procédures de sécurité ni un technicien habilité.

# 

# Familles d'équipements couvertes : \*\*pompes centrifuges\*\* et \*\*compresseurs d'air\*\*.

# 

# \## Livrable 1 – Contenu du ZIP

# 

# ```

# L1\_MaintiDoc\_ELFAROUKI-HAFFARI-LOKSAIRI/

# ├── L1\_MaintiDoc\_ELFAROUKI-HAFFARI-LOKSAIRI\_Rapport.pdf     Rapport (cadrage, corpus, architecture, flux, risques, planning)

# ├── L1\_MaintiDoc\_ELFAROUKI-HAFFARI-LOKSAIRI\_LienGitHub.txt  URL du dépôt GitHub

# ├── README.md                                               Ce fichier

# └── L1\_MaintiDoc\_ELFAROUKI-HAFFARI-LOKSAIRI\_Corpus/         Documents, inventaire.csv, prompts\_corpus.md

# ```

# 

# \## Structure du dépôt

# 

# ```

# maintidoc/

# ├── README.md

# ├── .gitignore               Exclut secrets et fichiers .env

# ├── docs/

# │   └── diagrammes/          Sources des diagrammes (draw.io / Mermaid)

# └── corpus/

# &#x20;   ├── inventaire.csv       Registre du corpus : une ligne par document

# &#x20;   ├── prompts\_corpus.md    Prompts IA utilisés (P01, P02…), outil et date

# &#x20;   ├── documents/

# &#x20;   │   ├── famille\_1/       Pompes centrifuges

# &#x20;   │   └── famille\_2/       Compresseurs d'air

# &#x20;   └── images/              Photographies de panneaux et voyants

# ```

# 

# \## Règles

# 

# \- Utilisateurs, tickets et historiques sont \*\*fictifs\*\* ; aucune donnée personnelle réelle.

# \- Chaque document du corpus est vérifié par un membre et figure dans `inventaire.csv`.

# \- Aucun secret (clé d'API, mot de passe) n'est versionné.


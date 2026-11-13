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

## P02 — Manuel d'utilisation de la pompe HF-200

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Objectif** : produire le manuel principal de la famille pompes, conforme au plan de pages
  du référentiel (§5.1), pour que les citations « page + figure » soient vérifiables.
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF le manuel
> d'utilisation et d'entretien fictif de la pompe centrifuge HydroFlux HF-200 (équipements
> POMPE-A-01 et POMPE-A-02), version v1.2 (2025-03), en français, exactement 20 pages, en
> respectant le plan de pages du §5.1 : un chapitre par page, avec les figures 4.1, 6.1, 8.1,
> 11.1 (panneau de commande), 16.1 (bouchons du palier), 18.2 (détail du voyant orange), la
> courbe 13.1 et les tableaux 5.1, 12.1, 15.1, 19.1 (codes P-01 à P-20) et 20.1. Reprends sans
> les modifier les caractéristiques (§2.1), les voyants (§3.1) et les codes (§4.1). Le couple de
> serrage du bouchon de vidange doit être 35 N·m. Ajoute des renvois vers les autres documents
> du corpus par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_1/manuel_pompe_a.pdf` (20 pages)
- **Vérification** : à compléter par l'équipe — contrôler que chaque valeur (débit, pression,
  seuils 80 °C / 95 °C, couple 35 N·m, huile ISO VG 68 0,4 L) et chaque code correspond au
  référentiel, et que chaque figure est à la page annoncée.
- **Corrections apportées** :
  - Incohérence repérée dans le référentiel v1.0 : il indiquait un afficheur « 2 caractères »
    alors que les codes (« P-12 ») en comptent 4 → référentiel corrigé en « 4 caractères ».
  - Étiquettes des figures 4.1 et 16.1 qui se chevauchaient → repositionnées.
  - (à compléter par l'équipe après relecture)

---

## P03 — Fiche des codes d'alarme HF-200

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Objectif** : détailler les 20 codes P-xx (cause probable et action) en complément du
  tableau 19.1 du manuel.
- **Texte du prompt** :

> À partir du §4.1 du référentiel, génère en PDF la fiche « Codes d'alarme – Pompe HydroFlux
> HF-200 » (v2.0, 2025-03) pour POMPE-A-01 et POMPE-A-02 : un tableau des codes P-01 à P-20
> (code, niveau A/D, voyant, signification, cause probable, action recommandée), sans changer
> aucune valeur du référentiel. Ajoute une page de remarques qui explique les deux états du
> voyant orange V2 (fixe = P-12, clignotant = P-06), le risque de confusion avec le voyant jaune
> V3, et le fait que POMPE-C-03 et les compresseurs utilisent d'autres codes.

- **Production** : `documents/famille_1/codes_alarme_pompe_a.pdf` (2 pages)
- **Vérification** : à compléter — comparer chaque ligne au §4.1 du référentiel.
- **Corrections apportées** : à compléter

---

## P04 — Procédure de vidange HF-200, version 1 (obsolète, contradictoire)

- **Outil** : Claude (Anthropic) + script de simulation de scan (`simuler_scan.py`)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Objectif** : créer l'ancienne version d'une procédure qui contredit la version en vigueur,
  pour tester la gestion des sources contradictoires (semaine 5), et un document scanné pour
  tester l'OCR.
- **Texte du prompt** :

> Génère l'ancienne version v1 (2023-06) de la procédure PR-POMPE-07 « Vidange de l'huile du
> palier » de la pompe HF-200, 4 pages, avec un schéma du palier page 2. Elle doit contenir
> volontairement deux différences avec la version en vigueur, conformément au §6 du
> référentiel : couple de serrage du bouchon de vidange de 25 N·m (au lieu de 35 N·m) et
> aucune étape de consignation électrique. Le reste doit rester techniquement plausible.
> Convertis ensuite le PDF en document scanné (images seules, sans texte sélectionnable,
> légère inclinaison et bruit).

- **Production** : `documents/famille_1/proc_vidange_a_v1.pdf` (4 pages, scanné)
- **Vérification** : à compléter — vérifier que le texte n'est pas sélectionnable dans le PDF et
  que les deux différences (25 N·m, absence de consignation) sont bien présentes et lisibles.
- **Corrections apportées** : à compléter

---

## P05 — Procédure de vidange HF-200, version 2 (en vigueur, contradictoire)

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Objectif** : version correcte de la procédure, qui contredit la v1.
- **Texte du prompt** :

> Génère la version v2 (2025-04) de la procédure PR-POMPE-07 « Vidange de l'huile du palier » de
> la pompe HF-200, 4 pages, qui remplace la v1. Elle doit : rendre la consignation électrique
> obligatoire, indiquer un couple de serrage de 35 N·m cohérent avec manuel_pompe_a (p.5 et
> p.16), signaler explicitement en tête de document les changements par rapport à la v1, et
> contenir un historique des versions. Reprends le même schéma du palier avec la nouvelle valeur.

- **Production** : `documents/famille_1/proc_vidange_a_v2.pdf` (4 pages)
- **Vérification** : à compléter
- **Corrections apportées** : à compléter

---

## P06 — Schéma hydraulique station de pompage atelier A

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, le schéma hydraulique de principe de la station de pompage de l'atelier A (POMPE-A-01 en service, POMPE-A-02 en secours, montées en parallèle), 1 page : bâche, crépine CR1, vanne VA1, pressostat PS1 (seuil 0,3 bar → alarme P-04), clapets CA1/CA2, vannes VR1/VR2, manomètre PI1 et capteur PT1 (alarmes P-07 et P-08), avec un tableau des repères.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_1/schema_hydraulique_pompe_a.pdf` (1 page)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : schéma redessiné : libellé « Vers process » mal affiché

---

## P07 — Vue éclatée pompe HydroFlux HF-200

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, la vue éclatée de l'ensemble palier / hydraulique de la pompe HF-200, 1 page, avec des repères numérotés identiques au tableau 20.1 du manuel (01 à 10), une nomenclature et l'ordre de démontage conseillé.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_1/vue_eclatee_pompe_a.pdf` (1 page)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P08 — Procédure de remplacement de la garniture mécanique GM-28

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, la procédure PR-POMPE-11 de remplacement de la garniture mécanique GM-28 de la pompe HF-200, 2 pages : déclencheur P-14, consignation obligatoire, pièces et outillage, démontage, schéma de coupe de la garniture avec cote de pose, remontage, remise en service sans marche à sec.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_1/proc_garniture_pompe_a.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : étiquette « Arbre » et « Joint torique » illisibles sur la figure → corrigées

---

## P09 — Procédure d'alignement accouplement pompe / moteur

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, la procédure PR-POMPE-04 d'alignement de l'accouplement pompe / moteur, applicable aux trois pompes, avec une figure de principe, un tableau des tolérances (radial, angulaire, pied boiteux) et un mode opératoire numéroté.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_1/proc_alignement_pompes.pdf` (1 page)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : numérotation de page incorrecte (« 1 / 2 » sur un document d'une page) → corrigée

---

## P10 — Fiche de sécurité consignation des pompes

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, la fiche de sécurité FS-POMPE-01 « Consignation des pompes », 2 pages : les 6 étapes de consignation (préparer, séparer, condamner, signaler, vérifier, dissiper) avec la vérification associée, la déconsignation, et un formulaire de consignation à remplir.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_1/fiche_securite_consignation_pompes.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P11 — Fiche de données de sécurité simplifiée huile de palier HydroLub 68

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, une fiche de données de sécurité simplifiée et fictive pour l'huile de palier « HydroLub 68 » (ISO VG 68) utilisée sur les pompes HF-200, en 9 rubriques : identification, dangers, premiers secours, incendie, déversement, stockage, protection, propriétés, élimination. Préciser qu'elle ne remplace pas la FDS réelle d'un fournisseur.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_1/fiche_securite_huile_palier.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P12 — Plan de maintenance préventive pompes

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, le plan de maintenance préventive des trois pompes, 2 pages : tableau des périodicités par équipement en renvoyant au document du corpus concerné, règles générales, calendrier type 2026 de POMPE-A-01. Respecter le fait que la HFM-450 a des roulements graissés à vie.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_1/plan_preventif_pompes.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P13 — Guide de dépannage pompes centrifuges HF-200

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, un guide de dépannage des pompes HF-200, 2 pages : un logigramme « pompe bruyante » qui distingue cavitation (voyant orange clignotant, P-06) et température palier (orange fixe, P-12), un tableau symptômes / codes / causes / actions renvoyant aux procédures du corpus, et des points d'attention.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_1/guide_depannage_pompes.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P14 — Manuel de la pompe HFM-450 (POMPE-C-03)

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel (§2.2 et §4.2), génère en PDF le manuel d'utilisation fictif de la pompe
> multicellulaire HydroFlux HFM-450 (POMPE-C-03), v2.1 (2023-11), 8 pages, un chapitre par page :
> sécurité et description (figure des 5 étages), caractéristiques, installation, panneau de
> commande (figure ; préciser qu'il n'a que deux voyants, vert et rouge, et pas de voyant orange),
> entretien (roulements graissés à vie, aucune vidange), tableau des codes H-01 à H-08, pièces de
> rechange. Insister sur les différences avec la HF-200 pour éviter les confusions.

- **Production** : `documents/famille_1/manuel_pompe_c.pdf` (8 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** :
  - Le référentiel v1.0 plaçait les codes H-xx « p.14 » du manuel, alors qu'un manuel de 8 pages a
    été jugé suffisant → référentiel corrigé (codes en p.7, tableau 7.1).

---

## P15 — Historique des interventions POMPE-A-01

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> Génère en PDF l'extraction fictive de l'historique des interventions de POMPE-A-01 (1 page,
> extraction du 2025-10-01), en reprenant exactement les 6 lignes du §9.1 du référentiel (date,
> ticket, code, intervention, intervenant, statut). Ajoute les observations du responsable : deux
> P-12 en moins de 3 mois, aucun ticket ouvert, et le fait que l'historique à jour se consulte via
> l'outil MCP. Mentionne que la diffusion est limitée au groupe responsables.

- **Production** : `documents/famille_1/historique_pompe_a_01.pdf` (1 page)
- **Vérification** : à compléter — comparer ligne à ligne avec le §9.1 du référentiel.
- **Corrections apportées** : à compléter

---

## P16 — Photographies synthétiques famille pompes

- **Outil** : script Python (Pillow) écrit avec l'aide de Claude (Anthropic) — images dessinées
  par programme, aucune photo réelle ni image trouvée sur internet
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> Écris un script Python qui dessine trois « photographies » synthétiques réalistes (fond texturé,
> légère inclinaison, bruit, JPEG) : (1) le panneau de commande HF-200 avec V1 vert et V2 orange
> allumés et l'afficheur « P-12 », libellés conformes au §3.1 du référentiel ; (2) la plaque
> signalétique lisible de POMPE-A-01 (HF-200, n° de série HF2-21-0347, caractéristiques du §2.1) ;
> (3) la plaque de POMPE-A-02 photographiée floue, sombre et avec un reflet, de sorte que le
> repère et le numéro de série soient illisibles.

- **Production** : `images/photo_panneau_pompe_a.jpg`, `images/photo_plaque_pompe_a.jpg`,
  `images/photo_plaque_pompe_floue.jpg`
- **Vérification** : à compléter
- **Corrections apportées** :
  - Libellés des voyants V2 / V3 qui se chevauchaient sur la première version du panneau →
    police réduite et espacement agrandi.

---

## P17 — Manuel d'utilisation et d'entretien compresseur AiroTech AT-37

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, le manuel d'utilisation et d'entretien fictif du compresseur à vis AiroTech AT-37 (COMP-B-01, COMP-B-02), v3.0 (2024-09), exactement 20 pages selon le plan du §5.2 du référentiel (un chapitre par page), avec les figures 4.1, 6.1, 8.1, 10.1 (panneau et écran LCD), 15.1 (filtre FA-37) et les tableaux 5.1, 11.1, 14.1, 17.1 (codes C-01 à C-20) et 20.1. Reprends sans les modifier le §2.3, le §3.2 et le §4.3, et ajoute une mise en garde sur la différence entre le voyant orange du compresseur et celui des pompes.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/manuel_comp_b.pdf` (20 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P18 — Codes d'alarme compresseur AiroTech AT-37

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, la fiche « Codes d'alarme – Compresseur AiroTech AT-37 » (v3.0, 2024-09), 2 pages : tableau des codes C-01 à C-20 (niveau, voyant, signification, cause, action) conforme au §4.3, et une page de remarques sur le sens du voyant orange L2 et la différence avec les pompes HF-200.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/codes_alarme_comp_b.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P19 — Procédure de vidange huile compresseur AT-37

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, la procédure PR-COMP-03 de vidange de l'huile du compresseur AT-37 (déclencheur C-09, 4 000 h), 2 pages : consignation et dépressurisation, matériel, vidange, remplacement du filtre à huile FH-37 et du séparateur SP-37, remplissage de 18 L d'huile synthétique, réarmement du compteur.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/proc_vidange_huile_comp_b.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P20 — Procédure de purge des condensats compresseur AT-37 (v1)

- **Outil** : Claude (Anthropic) + script de simulation de scan (`simuler_scan.py`)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, l'ancienne version v1 (2022-02) de la procédure PR-COMP-05 « Purge des condensats » du compresseur AT-37, 2 pages avec schéma, qui prescrit une purge manuelle toutes les 8 heures (contradiction volontaire du §6 du référentiel). Convertis ensuite le PDF en document scanné (images seules).
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/proc_purge_comp_b_v1.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P21 — Procédure de purge des condensats compresseur AT-37 (v2)

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, la version v2 (2024-10) de la procédure PR-COMP-05 « Purge des condensats », 2 pages, qui remplace la v1 : purgeur électronique automatique, contrôle hebdomadaire, conduite à tenir sur l'alarme C-11, changement par rapport à la v1 signalé en tête de document, historique des versions.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/proc_purge_comp_b_v2.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P22 — Procédure de remplacement du filtre à air compresseur AT-37

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, la procédure PR-COMP-02 de remplacement du filtre à air FA-37 (déclencheurs : voyant orange L2 fixe C-07 ou 2 000 h), 2 pages, avec une figure comparant une cartouche neuve et une cartouche colmatée, le mode opératoire et le réarmement du compteur.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/proc_filtre_air_comp_b.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P23 — Schéma pneumatique et circuit d'huile compresseur AT-37

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, le schéma pneumatique et le circuit d'huile du compresseur AT-37, 1 page : filtre à air, vanne d'admission, bloc vis, réservoir séparateur, vanne de pression minimale, soupape de sécurité 8,8 bar, refroidisseur, purgeur, thermostat, radiateur et filtre à huile, avec un tableau des repères.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/schema_pneumatique_comp_b.pdf` (1 page)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P24 — Schéma électrique démarrage étoile-triangle compresseur AT-37

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, le schéma électrique simplifié du démarrage étoile-triangle du compresseur AT-37 (disjoncteur, contacteurs KM1, KM2, KM3, temporisation 8 s, automate), 1 page, avec la séquence de démarrage et les liens avec les défauts C-04 et C-16.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/schema_electrique_comp_b.pdf` (1 page)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P25 — Fiche de sécurité air comprimé et consignation compresseurs

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, la fiche de sécurité FS-COMP-01 « Air comprimé et consignation des compresseurs », 2 pages : dangers, consignation et dépressurisation pas à pas, interdits, conduite en cas d'accident.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/fiche_securite_air_comprime.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P26 — Fiche de données de sécurité simplifiée huiles compresseurs

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, une fiche de données de sécurité simplifiée et fictive pour les huiles des compresseurs (synthétique pour AT-37, minérale pour AP-11), 2 pages, en 8 rubriques, en insistant sur l'interdiction de mélanger les deux huiles.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/fiche_securite_huile_comp.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P27 — Plan de maintenance préventive compresseurs

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, le plan de maintenance préventive des trois compresseurs, 2 pages : tableau des périodicités par équipement (AT-37 et AP-11) renvoyant aux documents du corpus, règles, calendrier type 2026 de COMP-B-02.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/plan_preventif_compresseurs.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P28 — Notice d'utilisation compresseur à piston AiroTech AP-11

- **Outil** : Claude (Anthropic) + script de simulation de scan (`simuler_scan.py`)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, la notice fictive du compresseur à piston AiroTech AP-11 (COMP-P-03), édition 1.0 (2012-05), 3 pages : couverture avec figure, caractéristiques du §2.4, panneau à deux voyants sans codes, entretien (purge quotidienne, vidange 500 h), défaut thermique. Convertis-la ensuite en document scanné.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/manuel_comp_p.pdf` (3 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P29 — Historique des interventions COMP-B-02

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, l'extraction fictive de l'historique des interventions de COMP-B-02 (1 page, extraction du 2025-10-25), en reprenant exactement les 6 lignes du §9.2 du référentiel, dont le ticket ouvert TCK-2025-0188, avec les observations du responsable.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/historique_comp_b_02.pdf` (1 page)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P30 — Note de service compresseurs

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, une note de service fictive NS-COMP-2025-02 sur le nettoyage des radiateurs de COMP-B-02, 2 pages, d'apparence normale. En page 2, insère au milieu d'un paragraphe ordinaire le texte exact d'injection du §7 du référentiel. Ce document servira à tester la résistance de l'assistant aux injections de prompt.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/note_maintenance_piegee.pdf` (2 pages)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P31 — Note de service interne organisation maintenance compresseurs

- **Outil** : Claude (Anthropic)
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> À partir du référentiel commun (docs/referentiel_corpus.md), génère en PDF, en français, une note de service interne fictive NS-COMP-2025-05 sur l'organisation de la maintenance des compresseurs (astreinte, délai de traitement des C-07, indicateurs), 1 page, réservée aux responsables.
> Utilise uniquement les identifiants, codes et valeurs du référentiel et renvoie aux autres
> documents par leur document_id. Indique sur chaque page qu'il s'agit d'un document fictif.

- **Production** : `documents/famille_2/note_service_compresseurs.pdf` (1 page)
- **Vérification** : à compléter par l'équipe
- **Corrections apportées** : à compléter

---

## P32 — Photographies synthétiques famille compresseurs

- **Outil** : script Python (Pillow) écrit avec l'aide de Claude (Anthropic) — images dessinées par
  programme, aucune photo réelle
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> Complète le script de photos synthétiques avec deux images du compresseur AT-37 : (1) l'écran et
> le panneau lisibles, voyants L1 vert et L2 orange allumés, code « C-07 » à l'écran ; (2) une photo
> ambiguë du même panneau : cadrage serré, sombre et floue, écran et libellés illisibles, seul le
> voyant orange reste visible, pour qu'elle puisse être confondue avec le voyant orange d'une pompe.

- **Production** : `images/photo_ecran_alarme_comp_b.jpg`, `images/photo_panneau_comp_b.jpg`
- **Vérification** : à compléter
- **Corrections apportées** : à compléter

---

## P33 — Recherche de documents publics réutilisables (en anglais)

- **Outil** : Claude (Anthropic), avec recherche web
- **Date** : 2026-11-13
- **Lancé par** : Sabrine
- **Texte du prompt** :

> Trouve deux documents publics courts, en anglais, réutilisables légalement, l'un sur les pompes
> centrifuges et l'autre sur les compresseurs d'air (si possible sur le remplacement du filtre à
> air). Donne l'URL exacte, l'éditeur et la licence ou les conditions de réutilisation, avec la
> source de cette information.

- **Réponse de l'IA (résumé)** : deux fiches techniques (« tip sheets ») du U.S. Department of
  Energy, programme Industrial Technologies :
  - Pumping Systems Tip Sheet #3 « Select an Energy-Efficient Centrifugal Pump »,
    DOE/GO-102005-2157, octobre 2005 —
    https://www.energy.gov/sites/prod/files/2014/05/f16/efficient_centrifug_pumps.pdf
  - Compressed Air Tip Sheet #14 « Inlet Filter Replacement », août 2004 —
    https://www.energy.gov/sites/prod/files/2014/05/f16/compressed_air14.pdf
  - Licence : la page « Web Policies » de energy.gov indique que l'information gouvernementale des
    sites du DOE est dans le domaine public et peut être librement copiée et distribuée, avec une
    demande de mention du Department of Energy (https://www.energy.gov/about-us/web-policies).
- **Erreurs / pièges repérés dans les réponses de l'IA** :
  - Les « sourcebooks » complets du DOE ont d'abord été proposés, mais ils ont été écartés : ils sont
    très longs (plus de 100 pages) et co-rédigés avec des organismes privés (Hydraulic Institute,
    Compressed Air Challenge), ce qui rend leur statut de licence moins clair.
  - Plusieurs résultats de recherche renvoyaient vers des copies sur Scribd ou des sites de
    formation : écartés, seule la source officielle energy.gov est retenue.
- **Vérification par l'équipe** : à compléter — ouvrir chaque URL, vérifier qu'elle fonctionne,
  que le contenu correspond, compter les pages, et vérifier l'absence de mention de copyright
  contraire dans le document.

---

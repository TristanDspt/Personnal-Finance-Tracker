# 🏛️ ARCHITECTURE — Personal Finance Tracker

## Vue d'ensemble

Application Streamlit de suivi financier personnel.
La logique est **strictement séparée** de l'affichage :
- Les calculs vivent dans `st_logic.py`
- Les graphiques vivent dans `st_charts.py`
- Les pages Streamlit ne font qu'appeler ces fonctions et afficher les résultats

```
PostgreSQL (Vues SQL)
        ↓
dashboard/components/database.py   ← connexion + chargement des vues
        ↓
   dashboard/components/st_logic.py        ← calculs, transformations pandas
   dashboard/components/st_charts.py       ← figures Plotly
        ↓
     dashboard/app.py               ← point d'entrée Streamlit
   dashboard/pages/                 ← pages secondaires
```

---

## Fichiers

| Fichier | Rôle |
| :--- | :--- |
| `dashboard/app.py` | Point d'entrée Streamlit |
| `dashboard/components/database.py` | Connexion PostgreSQL + chargement des vues SQL en DataFrame |
| `dashboard/components/st_logic.py` | Toute la logique métier (calculs, transformations) — zéro Streamlit |
| `dashboard/components/st_charts.py` | Toutes les figures Plotly (KPIs + Dashboards) |
| `dashboard/pages/1_📊_KPIs.py` | Page KPIs globaux |
| `dashboard/pages/2_📈_Dashboards.py` | Dashboards par enveloppe |
| `dashboard/pages/3_🧾_Saisie.py` | Formulaire de saisie des mouvements |
| `scripts/` | ETL : scripts de mise à jour des données (update_pee.py, etc.) |
| `sql/` | Scripts SQL (schéma, vues) |

---

## 📁 Structure du Projet

```
├── dashboard/
│   ├── components/
│   │   ├── __init__.py
│   │   ├── database.py        ← Connexion PostgreSQL + chargement vues
│   │   ├── st_logic.py        ← Logique métier (calculs pandas)
│   │   └── st_charts.py       ← Figures Plotly
│   ├── pages/
│   │   ├── 1_📊_KPIs.py       ← KPIs globaux
│   │   ├── 2_📈_Dashboards.py ← Dashboards par enveloppe
│   │   └── 3_🧾_Saisie.py     ← Formulaire de saisie
│   ├── __init__.py
│   └── app.py                 ← Point d'entrée Streamlit
├── scripts/
│   ├── config.py              ← Paramètres DB (exclu du repo)
│   ├── update_pee.py          ← ETL mise à jour fonds PEE
│   ├── update_price.py        ← ETL mise à jour cours boursiers
│   └── imports/               ← Notebooks d'import historique
├── sql/
│   ├── schema/                ← Schéma DB (architect)
│   └── Script SQL/            ← Scripts de création et vues
├── docs/                      ← Assets visuels
├── run/                       ← Scripts de lancement
├── .streamlit/
│   └── secrets.toml           ← Secrets DB (exclu du repo)
├── ARCHITECTURE.md
├── roadmap.md
├── requirements.txt
└── .gitignore
```

---

## Vues SQL (Sources de données)

| Vue | Contenu |
| :--- | :--- |
| `view_global_portefeuille` | État instantané : capital, profit €/%, PRU par produit |
| `view_historique_portefeuille` | Reconstitution quotidienne du patrimoine par ptf_id (base des graphiques) |
| `view_historique_pdt` | Reconstitution quotidienne du patrimoine par pdt_id (dashboards détaillés) |
| `view_apports_mensuels` | Flux d'argent réels entrant/sortant par mois |
| `view_positions_actuelles` | Quantités détenues par produit |
| `view_pru` | Prix de revient unitaire par produit |

---

## Référence IDs

| PTF | Nom | PDT | Nom |
| :--- | :--- | :--- | :--- |
| 1 | PEA | 1 | S&P 500 |
| 2 | CTO | 2 | Gold |
| 3 | STEF | 3 | Action STEF |
| 4 | CiC | 4 | Oblig CiC |
| 6 | Livrets | 5 | Equi CiC |
| | | 6 | Strat CiC |
| | | 7 | Cash Bourso (PEA) |
| | | 8 | Cash TR (CTO) |
| | | 10 | Livret A |
| | | 11 | LEP |

---

## st_logic.py — Fonctions

### 1. Calculs Généraux
> Indépendants de la période. Basés sur `df` (view_global_portefeuille ou sous-ensemble filtré).

| Fonction | Entrée | Sortie |
| :--- | :--- | :--- |
| `get_patrimoine_total(df)` | df | `float` |
| `get_perf_marches(df)` | df | `dict {euro, pct}` |
| `get_poids_enveloppes(df)` | df | `dict {etf, pee, livret}` |
| `get_capital_net(df, liste_pdt)` | df, list[int] | `dict {pdt_id: net}` |
| `get_tri_ptf(df, engine, liste_ptf)` | df, engine, list | `float` |
| `get_tri_pdt(df, engine, liste_pdt)` | df, engine, list | `dict {pdt_id: float}` |

> ⚠️ `get_perf_etf` **supprimée** — doublon avec `get_perf_marches`. La perf ETF se calcule via `get_perf_marches(df.query("ptf_id in (1, 2)"))`.

> ⚠️ `get_capital_net` : prend une `liste_pdt` (list[int]), retourne `dict {pdt_id: net}`. Fiscalité par `pdt_id` : PEA/PEE 18.6% | CTO 31.4%.

> ⚠️ `get_tri_ptf` → TRI pour une ou plusieurs **enveloppes** (ptf_id) → `float`.
> `get_tri_pdt` → TRI pour un ou plusieurs **produits** (pdt_id) → `dict {pdt_id: float}`.

### 2. Logique Temporelle
> Liées au slider de période. Basées sur `df_histo` et `df_apports`.

| Fonction | Entrée | Sortie |
| :--- | :--- | :--- |
| `get_nb_mois(duree)` | `str` | `int` |
| `get_date_debut(duree)` | `str` | `pd.Timestamp` (normalisé minuit) |
| `get_df_periode(df_histo, date_debut)` | df_histo, date | `DataFrame` |
| `get_perf_etf_periode(df_histo, df_periode, date_debut, duree)` | df_histo, df_periode, date, str | `dict {euro, pct}` |
| `get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping)` | df_histo, df_periode, str, date, dict | `dict {nom: {euro, pct}, ...}` |
| `get_perf_pdt_periode(df_histo, df_periode, duree, date_debut, liste_pdt)` | df_histo, df_periode, str, date, list | `dict {pdt_id: {euro, pct}}` |
| `get_injecte_periode(df_histo, df_periode, duree, date_debut, liste_pdt)` | df_histo, df_periode, str, date, list | `float` |
| `get_tableau_mensuel_ptf(df_histo, df_apports, duree, mapping)` | df_histo, df_apports, str, dict | `tuple (df_tableau, df_tableau_buffer)` |
| `get_donnees_graph(df_tableau_buffer, df_apports, duree)` | df_tableau_buffer, df_apports, str | `tuple (df_apports_graph, df_capital_graph)` |

> ⚠️ `get_tableau_mensuel_ptf` retourne un tuple :
> - `df_tableau` : version nettoyée pour l'affichage (tri décroissant, 1er mois viré)
> - `df_tableau_buffer` : version avec mois de buffer pour `get_donnees_graph` (tri croissant, 1er mois conservé)

> ⚠️ `get_perf_etf_periode`, `get_perf_ptf_periode`, `get_perf_pdt_periode`, `get_injecte_periode` :
> Si `snap_debut['jour'] > date_debut`, la période remonte avant le 1er mouvement → traité comme "Max" (valeur totale).

> ⚠️ `get_perf_etf_periode` : présente dans `st_logic.py` mais **non appelée dans les pages**. Disponible si besoin.

---

## st_charts.py — Fonctions

| Fonction | Entrée | Sortie |
| :--- | :--- | :--- |
| `apply_style(fig)` | `go.Figure` | `None` (modifie en place) |
| `make_donuts(df, names, values, color_discrete_map, rotation, labels, poids, taille)` | DataFrame + params visuels | `go.Figure` |
| `make_graph_global(df_apports_graph, df_capital_graph)` | 2 DataFrames | `go.Figure` |

> ⚠️ `make_donuts` : `poids` optionnel (default `None`) — si absent, label centré sans valeur %. Paramètre `taille` (default `200`) contrôle la hauteur en pixels.

---

## Ordre d'appel dans KPIs.py
```python
# 1. Chargement des vues
df, df_histo, df_apports = ...

# 2. Sidebar : slider période + toggle 12m roulants
duree   = st.select_slider(...)
vue_12m = st.toggle(...)

# 3. Calculs généraux (indépendants de la période)
capital      = get_patrimoine_total(df)
perf_marches = get_perf_marches(df)
df_etf       = df.query("ptf_id in (1, 2)")
perf_etf     = get_perf_marches(df_etf)            # ← pas de get_perf_etf() dédiée
poids        = get_poids_enveloppes(df)
tri_global   = get_tri_ptf(df, engine, [1, 2, 3, 4])  # ← TRI global hors livrets

# 4. Logique temporelle
date_debut   = get_date_debut(duree)
df_periode   = get_df_periode(df_histo, date_debut)
mapping_ptf  = {1: "PEA", 2: "CTO", 3: "STEF", 4: "CiC"}
perf_ptf     = get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping_ptf)

# 5. Tableau (doit précéder le graph)
mapping_tableau = {1: "ETF", 2: "ETF", 3: "STEF", 4: "CiC", 6: "Livrets"}
df_tableau, df_tableau_buffer = get_tableau_mensuel_ptf(df_histo, df_apports, duree, mapping_tableau)

# 6. Données graph (reçoit df_tableau_buffer, pas df_tableau)
df_ap_graph, df_cap_graph = get_donnees_graph(df_tableau_buffer, df_apports, duree)

# 7. Interface
# KPIs haut de page :
#   col1 : Patrimoine Total
#   col2 : Performance Marchés (perf_marches)
#   col3 : Performance Annualisée (tri_global)
#
# Donuts (3 colonnes) :
#   fig_etf  → make_donuts(..., poids=poids['etf'])
#   fig_pee  → make_donuts(..., poids=poids['pee'])
#   fig_liv  → make_donuts(..., poids=poids['livret'])
#
# Journal de bord (4 colonnes, réactif slider) :
#   perf_ptf['PEA'] | perf_ptf['CTO'] | perf_ptf['STEF'] | perf_ptf['CiC']
#
# Tableau mensuel (vue_12m contrôle les colonnes Evo 12m)
# Graphique global (masqué si duree in ["1 Mois", "Début Mois"])
```

---

## Ordre d'appel dans Dashboards.py
```python
# 1. Chargement des vues
df, df_histo, df_apports = ...

# 2. Sidebar : choix enveloppe + slider période
choix_global = st.radio(...)
duree        = st.select_slider(...)

# 3. Logique temporelle commune
date_debut = get_date_debut(duree)
df_periode = get_df_periode(df_histo, date_debut)

# 4. Par dashboard (match/case)
match choix_global:

    case "ETF":
        capital    = get_patrimoine_total(df.query("ptf_id in (1, 2)"))
        perf       = get_perf_marches(df_etf)
        tri        = get_tri_ptf(df, engine, [1, 2])
        mapping    = {1: "PEA", 2: "CTO"}
        perf_ptf   = get_perf_ptf_periode(...)
        fig        = make_donuts(..., taille=194)          # sans poids

    case "PEA":
        capital      = get_patrimoine_total(df.query("ptf_id == 1"))
        perf         = get_perf_marches(df_pea)
        capital_net  = get_capital_net(df, [1, 7])
        tri          = get_tri_ptf(df, engine, [1])
        perf_ptf     = get_perf_ptf_periode(...)
        injecte      = get_injecte_periode(...)

    case "CTO":
        # Même pattern que PEA
        capital_net  = get_capital_net(df, [2])

    case "STEF":
        capital      = get_patrimoine_total(df.query("ptf_id == 3"))
        capital_net  = get_capital_net(df, [3])
        tri          = get_tri_ptf(df, engine, [3])
        abondement   = df_stef["abondement_recu"].sum()

    case "CiC":
        capital      = get_patrimoine_total(df.query("ptf_id == 4"))
        capital_net  = get_capital_net(df, [4, 5, 6])
        tri          = get_tri_ptf(df, engine, [4])
        tri_pdt      = get_tri_pdt(df, engine, [4, 5, 6])
        perf_pdt_max = get_perf_pdt_periode(..., duree='Max', date_debut=None, liste_pdt=[4, 5, 6])
        perf_pdt     = get_perf_pdt_periode(..., liste_pdt=[4, 5, 6])   # réactif slider
        fig          = make_donuts(...)    # par pdt_id : Obligation / Equilibre / Stratégie
```

---

## État des Dashboards

| Dashboard | État |
| :--- | :--- |
| ETF (PEA + CTO agrégés) | ✅ Complet |
| PEA | ✅ Complet |
| CTO | ✅ Complet |
| STEF | ✅ Complet |
| CiC | ✅ Complet |

---

## Conventions de nommage

| Préfixe | Usage |
| :--- | :--- |
| `get_` | Fonction qui calcule et retourne une valeur |
| `make_` | Fonction qui crée et retourne une figure Plotly |
| `df_` | DataFrame pandas |
| `fig_` | Figure Plotly (dans st_charts.py) |
| `pdt_` | Colonne liée à un produit financier (convention DB) |
| `ptf_` | Colonne liée à un portefeuille (convention DB) |
| `mvt_` | Colonne liée à un mouvement (convention DB) |
| `cot_` | Colonne liée à une cotation (convention DB) |

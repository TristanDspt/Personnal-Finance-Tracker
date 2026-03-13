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
scripts/database.py   ← connexion + chargement des vues
        ↓
   st_logic.py        ← calculs, transformations pandas
   st_charts.py       ← figures Plotly
        ↓
     Home.py          ← interface principale
   pages/Dashboards   ← interfaces secondaires
```

---

## Fichiers

| Fichier | Rôle |
| :--- | :--- |
| `scripts/database.py` | Connexion PostgreSQL + chargement des vues SQL en DataFrame |
| `scripts/st_logic.py` | Toute la logique métier (calculs, transformations) — zéro Streamlit |
| `scripts/st_charts.py` | Toutes les figures Plotly (Home + Dashboards) |
| `Home.py` | Page principale : appels des fonctions + affichage Streamlit |
| `pages/1_📊_Dashboards.py` | Dashboards par enveloppe |
| `pages/2_✍️_Saisie.py` | Formulaire de saisie des mouvements |

---

## Vues SQL (Sources de données)

| Vue | Contenu |
| :--- | :--- |
| `view_global_portefeuille` | État instantané : capital, profit €/%, PRU par produit |
| `view_historique_portefeuille` | Reconstitution quotidienne du patrimoine (base des graphiques) |
| `view_apports_mensuels` | Flux d'argent réels entrant/sortant par mois |
| `view_positions_actuelles` | Quantités détenues par produit |
| `view_pru` | Prix de revient unitaire par produit |

---

## st_logic.py — Fonctions

### 1. Calculs Généraux
> Indépendants de la période. Basés sur `df` (view_global_portefeuille ou sous-ensemble filtré).

| Fonction | Entrée | Sortie |
| :--- | :--- | :--- |
| `get_patrimoine_total(df)` | df | `float` |
| `get_perf_marches(df)` | df | `dict {euro, pct}` |
| `get_perf_etf(df)` | df | `dict {euro, pct}` |
| `get_poids_enveloppes(df)` | df | `dict {etf, pee, livret}` |
| `get_perf_nette(df, ptf_id)` | df, int | `dict {net, euro, pct}` |
| `get_tri_ptf(df, engine, liste_ptf)` | df, engine, list | `float` |

### 2. Logique Temporelle
> Liées au slider de période. Basées sur `df_histo` et `df_apports`.

| Fonction | Entrée | Sortie |
| :--- | :--- | :--- |
| `get_nb_mois(duree)` | `str` | `int` |
| `get_date_debut(duree)` | `str` | `pd.Timestamp` (normalisé minuit) |
| `get_df_periode(df_histo, date_debut)` | df_histo, date | `DataFrame` |
| `get_perf_etf_periode(df_histo, df_periode, date_debut, duree)` | df_histo, df_periode, date, str | `dict {euro, pct}` |
| `get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping)` | df_histo, df_periode, str, date, dict | `dict {nom: {euro, pct}, ...}` |
| `get_injecte_periode(df_histo, df_periode, duree, date_debut, liste_pdt)` | df_histo, df_periode, str, date, list | `float` |
| `get_perf_nette_periode(df_histo, df_periode, duree, date_debut, ptf_id)` | df_histo, df_periode, str, date, int | `dict {euro, pct}` |
| `get_tableau_mensuel(df_histo, df_apports, duree, mapping)` | df_histo, df_apports, str, dict | `tuple (df_tableau, df_tableau_buffer)` |
| `get_donnees_graph(df_tableau_buffer, df_apports, duree)` | df_tableau_buffer, df_apports, str | `tuple (df_apports_graph, df_capital_graph)` |

> ⚠️ `get_tableau_mensuel` retourne un tuple :
> - `df_tableau` : version nettoyée pour l'affichage (tri décroissant, 1er mois viré)
> - `df_tableau_buffer` : version avec mois de buffer pour `get_donnees_graph` (tri croissant, 1er mois conservé)

> ⚠️ `get_perf_etf_periode`, `get_perf_ptf_periode`, `get_injecte_periode` :
> Si `snap_debut['jour'] > date_debut`, la période remonte avant le 1er mouvement → traité comme "Max" (valeur totale).

---

## st_charts.py — Fonctions

| Fonction | Entrée | Sortie |
| :--- | :--- | :--- |
| `apply_style(fig)` | `go.Figure` | `None` (modifie en place) |
| `make_donuts(df, names, values, color_discrete_map, rotation, labels, poids)` | DataFrame + params visuels | `go.Figure` |
| `make_graph_global(df_apports_graph, df_capital_graph)` | 2 DataFrames | `go.Figure` |

---

## Ordre d'appel dans Home.py
```python
# 1. Chargement des vues
df, df_histo, df_apports = ...

# 2. Slider
duree = st.select_slider(...)

# 3. Calculs généraux (indépendants de la période)
capital        = get_patrimoine_total(df)
perf_marches   = get_perf_marches(df)
perf_etf       = get_perf_etf(df)
poids          = get_poids_enveloppes(df)

# 4. Logique temporelle
date_debut     = get_date_debut(duree)
df_periode     = get_df_periode(df_histo, date_debut)
perf_etf_p     = get_perf_etf_periode(df_histo, df_periode, date_debut, duree)
mapping_ptf    = {1: "PEA", 2: "CTO", 3: "STEF", 4: "CiC"}
perf_ptf       = get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping_ptf)

# 5. Tableau (doit précéder le graph)
# Retourne un tuple — df_tableau pour l'affichage, df_tableau_buffer pour le graph
mapping_tableau = {1: "ETF", 2: "ETF", 3: "STEF", 4: "CiC", 6: "Livrets"}
df_tableau, df_tableau_buffer = get_tableau_mensuel(df_histo, df_apports, duree, mapping_tableau)

# 6. Données graph (reçoit df_tableau_buffer, pas df_tableau)
df_ap_graph, df_cap_graph = get_donnees_graph(df_tableau_buffer, df_apports, duree)

# 7. Figures
fig_etf        = make_donuts(...)
fig_pee        = make_donuts(...)
fig_liv        = make_donuts(...)
fig_global     = make_graph_global(df_ap_graph, df_cap_graph)
```

## Ordre d'appel dans Dashboards.py
```python
# 1. Chargement des vues
df, df_histo, df_apports = ...

# 2. Sidebar : choix enveloppe + slider période
choix_global = st.radio(...)
duree        = st.select_slider(...)

# 3. Logique temporelle commune (tous les dashboards)
date_debut = get_date_debut(duree)
df_periode = get_df_periode(df_histo, date_debut)

# 4. Par dashboard (dans les blocs match/case)
# Filtres df, mappings, calculs et affichage sont tous dans le bloc dédié
match choix_global:
    case "PEA":
        df_pea        = df.query("ptf_id == 1")
        capital_pea   = get_patrimoine_total(df_pea)
        perf_pea      = get_perf_marches(df_pea)
        mapping_ptf   = {1: "PEA"}
        perf_ptf_pea  = get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping_ptf)
        liste_pdt     = [1]
        injecte_pea   = get_injecte_periode(df_histo, df_periode, duree, date_debut, liste_pdt)
        capital_net   = get_perf_nette(df, 1)
        ...
```

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
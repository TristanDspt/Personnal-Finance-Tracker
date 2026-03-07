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
| `pages/1_📊_Dashboards.py` | Dashboards par enveloppe — à venir |
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
> Indépendants de la période. Basés sur `df` (view_global_portefeuille).

| Fonction | Entrée | Sortie |
| :--- | :--- | :--- |
| `get_patrimoine_total(df)` | df | `float` |
| `get_perf_marches(df)` | df | `dict {euro, pct}` |
| `get_perf_etf(df)` | df | `dict {euro, pct}` |
| `get_poids_enveloppes(df)` | df | `dict {etf, pee, livret}` |

### 2. Logique Temporelle
> Liées au slider de période. Basées sur `df_histo` et `df_apports`.

| Fonction | Entrée | Sortie |
| :--- | :--- | :--- |
| `get_nb_mois(duree)` | `str` | `int` |
| `get_date_debut(duree)` | `str` | `pd.Timestamp` |
| `get_df_periode(df_histo, date_debut)` | df_histo, date | `DataFrame` |
| `get_perf_etf_periode(df_histo, df_periode, duree)` | df_histo, df_periode, str | `dict {euro, pct}` |
| `get_perf_ptf_periode(df_histo, df_periode, duree)` | df_histo, df_periode, str | `dict {PEA: {prof, pct}, CTO: {...}, ...}` |
| `get_tableau_mensuel(df_histo, df_apports, duree)` | df_histo, df_apports, str | `DataFrame` |
| `get_donnees_graph(df_tableau, df_apports, duree)` | df_tableau, df_apports, str | `tuple (df_apports_graph, df_capital_graph)` |

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
perf_etf_p     = get_perf_etf_periode(df_histo, df_periode, duree)
perf_ptf       = get_perf_ptf_periode(df_histo, df_periode, duree)

# 5. Tableau (doit précéder le graph)
df_tableau     = get_tableau_mensuel(df_histo, df_apports, duree)

# 6. Données graph (dépend de df_tableau)
df_ap_graph, df_cap_graph = get_donnees_graph(df_tableau, df_apports, duree)

# 7. Figures
fig_etf        = make_donuts(...)
fig_pee        = make_donuts(...)
fig_liv        = make_donuts(...)
fig_global     = make_graph_global(df_ap_graph, df_cap_graph)
```

---

## Dashboards (à venir)

| Page | Contenu prévu |
| :--- | :--- |
| ETF | Performance combinée PEA + CTO, historique des cours |
| PEA | Détail S&P500, évolution capital/profit |
| CTO | Détail Gold, évolution capital/profit |
| STEF | Actions STEF, historique PEE |
| CiC | Détail des 3 fonds (Obligation, Equilibre, Stratégie) |
| Livrets | Livret A + LEP, évolution des soldes |

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
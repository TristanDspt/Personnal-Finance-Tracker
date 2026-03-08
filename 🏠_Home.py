import streamlit as st
import pandas as pd
import subprocess
import time
import scripts.database as db
import scripts.st_logic as logic
import scripts.st_charts as charts

# =============================================================================
# Home.py
# Page principale de l'application Personal Finance Tracker.
# Ce fichier ne contient que : imports, chargement, sidebar, appels de fonctions
# et affichage Streamlit.
# Zéro calcul ici → st_logic.py | Zéro figure construite ici → st_charts.py
# =============================================================================


# --- 1. CONFIGURATION PAGE ---

st.set_page_config(page_title="PFT", page_icon="🏠", layout="wide")

# Centrage des métriques via CSS
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    [data-testid="stMetricLabel"] {
        justify-content: center;
        width: 100%;
    }
    [data-testid="stMetricValue"] {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)


# --- 2. CONNEXION & CHARGEMENT DES VUES SQL ---

engine = db.get_engine()

# Les trois vues SQL sont la source de toutes les données de l'app
df         = db.get_view("view_global_portefeuille", engine)      # snapshot instantané
df_histo   = db.get_view("view_historique_portefeuille", engine)  # historique quotidien
df_apports = db.get_view("view_apports_mensuels", engine)         # flux cash mensuels


# --- 3. SIDEBAR ---

with st.sidebar:
    st.title("⚙️ Menu")

    # Affichage du cash en attente sur les poches broker (alerte si > 400€ sur le PEA)
    st.subheader("💰 Cash en attente")
    cash_pea = df.query("pdt_id == 7")['capital_actuel'].fillna(0).iloc[0]
    cash_cto = df.query("pdt_id == 8")['capital_actuel'].fillna(0).iloc[0]
    st.write(f"**PEA :** `{cash_pea:,.2f} €`".replace(',', ' '))
    st.write(f"**CTO :** `{cash_cto:,.2f} €`".replace(',', ' '))
    if cash_pea > 400:
        st.warning(f"⚠️ {cash_pea:,.2f}€ sur le PEA !".replace(',', ' '))

    st.divider()

    # Slider de période — contrôle tous les blocs réactifs de la page
    st.subheader("🛠️ Configuration")
    duree = st.select_slider(
        "Période d'analyse",
        options=["Début Mois", "1 Mois", "3 Mois", "6 Mois", "1 An", "3 Ans", "5 Ans", "Max"],
        value="6 Mois"
    )
    # Toggle pour afficher les colonnes d'évolution sur 12 mois glissants dans le tableau
    vue_12m = st.toggle("12 mois roulants", value=False)

    st.divider()

    # Bouton de mise à jour manuelle des fonds PEE (lance update_pee.py en subprocess)
    if st.button("🔄 MAJ PEE"):
        result = subprocess.run(
            [st.secrets["venv_python"], r"scripts\update_pee.py"],
            capture_output=True, text=True
        )
        st.cache_data.clear()
        if result.stderr:
            st.error("⚠️ Erreur !")
            st.text(result.stderr)
        elif "non trouvé" in result.stdout:
            st.warning("⚠️ Fichiers absents...")
            st.text(result.stdout)
        else:
            st.success("🚀 Données envoyées !")
            st.text(result.stdout)
        time.sleep(8)
        st.rerun()
    st.caption("Telecharger les fichiers CSV avant mise à jour.")


# --- 4. CALCULS GÉNÉRAUX (indépendants de la période) ---
# Ces valeurs ne changent pas quand on bouge le slider

capital      = logic.get_patrimoine_total(df)
perf_marches = logic.get_perf_marches(df)
perf_etf     = logic.get_perf_etf(df)
poids        = logic.get_poids_enveloppes(df)


# --- 5. LOGIQUE TEMPORELLE (réactive au slider) ---
# Ces valeurs sont recalculées à chaque changement de période

date_debut = logic.get_date_debut(duree)
df_periode = logic.get_df_periode(df_histo, date_debut)
perf_etf_p = logic.get_perf_etf_periode(df_histo, df_periode, duree)
# Mapping ptf_id → nom affiché
mapping_ptf = {1: "PEA", 2: "CTO", 3: "STEF", 4: "CiC"}
perf_ptf   = logic.get_perf_ptf_periode(df_histo, df_periode, duree, mapping_ptf)

# Le tableau doit être calculé avant le graph — get_donnees_graph dépend de df_tableau_buffer
# df_tableau_buffer : version avec mois de buffer, pour le calcul de perf_graph via shift(1)
# Mapping ptf_id → enveloppe pour regrouper les lignes
mapping_tableau = {
    1: "ETF",
    2: "ETF",
    3: "STEF",
    4: "CiC",
    6: "Livrets",
}
df_tableau, df_tableau_buffer      = logic.get_tableau_mensuel(df_histo, df_apports, duree, mapping_tableau)
df_apports_graph, df_capital_graph = logic.get_donnees_graph(df_tableau_buffer, df_apports, duree)


# --- 6. INTERFACE GRAPHIQUE ---

st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>🏛️ Personnal Finance Tracker 🏛️</h1>", unsafe_allow_html=True)
st.divider()

# KPIs GÉNÉRAUX — Patrimoine total + perfs globales (hors période)
_, col1, col2, col3, _ = st.columns([0.5, 2, 2, 2, 0.5])

with col1:
    st.metric(
        label="Patrimoine Total",
        value=f"{capital:,.0f} €".replace(",", " "),
        help="Somme totale de tous les actifs (Cash + Titres)"
    )
with col2:
    st.metric(
        label="Performance Marchés",
        value=f"{perf_marches['pct']:.0f} %",
        delta=f"{perf_marches['euro']:,.0f} €".replace(",", " "),
        help="Rendement total par rapport au capital investi (Hors livrets d'épargne)"
    )
with col3:
    st.metric(
        label="Performance ETF",
        value=f"{perf_etf['pct']:.0f} %",
        delta=f"{perf_etf['euro']:,.0f} €".replace(",", " "),
        help="Rendement des enveloppes ETF"
    )

# DONUTS — Préparation des DataFrames filtrés par enveloppe
df_etf_donut = df.query("ptf_id in [1, 2]").groupby('ptf_id')['capital_actuel'].sum().reset_index()
df_etf_donut['nom_pour_legende'] = df_etf_donut['ptf_id'].map({1: "S&P 500", 2: "Gold"})

df_pee_donut = df.query("ptf_id in [3, 4]").groupby('ptf_id')['capital_actuel'].sum().reset_index()
df_pee_donut['nom_pour_legende'] = df_pee_donut['ptf_id'].map({3: "STEF", 4: "CiC"})

df_liv_donut = df.query("pdt_id in [10, 11]").groupby('pdt_id')['capital_actuel'].sum().reset_index()
df_liv_donut['nom_pour_legende'] = df_liv_donut['pdt_id'].map({10: "Livret A", 11: "LEP"})

# Création des 3 donuts via st_charts (même fonction, params différents)
fig_etf = charts.make_donuts(
    df=df_etf_donut, names='nom_pour_legende', values='capital_actuel',
    color_discrete_map={"S&P 500": "#822A2A", "Gold": "#D3AF37"},
    rotation=50, labels="Poids ETF", poids=poids['etf']
)
fig_pee = charts.make_donuts(
    df=df_pee_donut, names='nom_pour_legende', values='capital_actuel',
    color_discrete_map={"STEF": "#00519e", "CiC": "#018289"},
    rotation=80, labels="Poids PEE", poids=poids['pee']
)
fig_liv = charts.make_donuts(
    df=df_liv_donut, names='nom_pour_legende', values='capital_actuel',
    color_discrete_map={"Livret A": "#FF8C00", "LEP": "#540A88"},
    rotation=10, labels="Poids Livrets", poids=poids['livret']
)

col4, col5, col6 = st.columns(3)
with col4: st.plotly_chart(fig_etf, use_container_width=True, config={'displayModeBar': False})
with col5: st.plotly_chart(fig_pee, use_container_width=True, config={'displayModeBar': False})
with col6: st.plotly_chart(fig_liv, use_container_width=True, config={'displayModeBar': False})

st.divider()

# JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {duree}</h4>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Performance ETF",
        value=f"{perf_etf_p['euro']:,.0f} €".replace(",", " "),
        delta=f"{perf_etf_p['pct']:.0f} %",
    )
with col2:
    st.metric(
        label="Performance PEA",
        value=f"{perf_ptf['PEA']['euro']:,.0f} €".replace(",", " "),
        delta=f"{perf_ptf['PEA']['pct']:.0f} %"
    )
with col3:
    st.metric(
        label="Performance CTO",
        value=f"{perf_ptf['CTO']['euro']:,.0f} €".replace(",", " "),
        delta=f"{perf_ptf['CTO']['pct']:.0f} %"
    )
with col4:
    st.metric(
        label="Performance STEF",
        value=f"{perf_ptf['STEF']['euro']:,.0f} €".replace(",", " "),
        delta=f"{perf_ptf['STEF']['pct']:.0f} %"
    )
with col5:
    st.metric(
        label="Performance CiC",
        value=f"{perf_ptf['CiC']['euro']:,.0f} €".replace(",", " "),
        delta=f"{perf_ptf['CiC']['pct']:.0f} %"
    )

# TABLEAU MENSUEL
# La traduction des mois en français et le formatage restent ici — c'est du pur affichage
mois_fr = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}

df_affichage = df_tableau.copy()

# Colonnes 12m roulants — ajoutées uniquement si le toggle est activé
if vue_12m:
    df_affichage['Evo 12m (€)'] = df_affichage['Total'] - df_affichage['Total'].shift(-12)
    df_affichage['Evo 12m (%)'] = (df_affichage['Evo 12m (€)'] / df_affichage['Total'].shift(-12)) * 100

# Traduction de l'index datetime en label lisible (ex: "Octobre 2025")
df_affichage.index = df_affichage.index.map(lambda x: f"{mois_fr[x.month]} {x.year}")

# Format d'affichage complet — on filtre ensuite sur les colonnes réellement présentes
format_complet = {
    'ETF': "{:,.2f} €", 'STEF': "{:,.2f} €", 'CiC': "{:,.2f} €",
    'Livrets': "{:,.2f} €", 'Total': "{:,.2f} €", 'Evo Patrimoine': "{:,.2f} €",
    'Perf Marchés (€)': "{:,.2f} €", 'Evo 12m (€)': "{:,.0f} €",
    'Evo (%)': "{:.2f} %", 'Evo 12m (%)': "{:.1f} %"
}
format_filtre = {k: v for k, v in format_complet.items() if k in df_affichage.columns}

st.dataframe(
    df_affichage.style
    .format(format_filtre, na_rep='-', thousands=" ")
    # Coloration conditionnelle : rouge si négatif, vert si positif
    .applymap(
        lambda x: 'color: #ff4b4b' if x < 0 else 'color: #09ab3b',
        subset=[c for c in ['Evo Patrimoine', 'Evo (%)', 'Perf Marchés (€)'] if c in df_affichage.columns]
    ),
    column_config={"Mois": st.column_config.Column(width=140)},
    use_container_width=True,
    height=min(35 * len(df_affichage) + 38, 458)  # hauteur dynamique selon le nombre de lignes
)

st.divider()

# GRAPHIQUE GLOBAL — masqué sur les courtes périodes (pas assez de points pour être lisible)
if duree not in ("1 Mois", "Début Mois"):
    fig_global = charts.make_graph_global(df_apports_graph, df_capital_graph)
    st.plotly_chart(fig_global, use_container_width=True)
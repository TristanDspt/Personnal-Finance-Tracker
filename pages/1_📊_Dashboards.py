import streamlit as st
import pandas as pd
import time
import scripts.database as db
import scripts.st_logic as logic
import scripts.st_charts as charts

# =============================================================================
# Dashboards.py
# Page dédiée aux dashboards de l'application Personal Finance Tracker.
# Ce fichier ne contient que : imports, chargement, sidebar, appels de fonctions
# et affichage Streamlit.
# Zéro calcul ici → st_logic.py | Zéro figure construite ici → st_charts.py
# =============================================================================


# --- 1. CONFIGURATION PAGE ---
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

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

    # Choix de l'enveloppe
    choix_global = st.sidebar.radio("Choix", ["ETF", "PEA", "CTO", "STEF", "CiC", "Livrets"])

    st.divider()

    # Slider de période — contrôle tous les blocs réactifs de la page
    st.subheader("🛠️ Configuration")
    duree = st.select_slider(
        "Période d'analyse",
        options=["Début Mois", "1 Mois", "3 Mois", "6 Mois", "1 An", "3 Ans", "5 Ans", "Max"],
        value="6 Mois"
    )
    # Toggle pour afficher le graph d'historique des cours
    histo_cours = st.toggle("Historique", value=False)


# --- 4. LOGIQUE TEMPORELLE ---

date_debut = logic.get_date_debut(duree)
df_periode = logic.get_df_periode(df_histo, date_debut)


# --- 5. INTERFACE GRAPHIQUE ---

st.markdown("<h1 style='text-align: center;'>📊 Dashboards</h1>", unsafe_allow_html=True)

match choix_global:

# DASH ETF

    # case "CTO":


# DASH PEA

    case "PEA":

        df_pea = df.query("ptf_id == 1")
        df_cotation = db.get_cotations_pdt(engine, 1, date_debut)
        last = df_cotation.iloc[0]['cot_prix']
        capital_pea = logic.get_patrimoine_total(df_pea)
        perf_pea = logic.get_perf_marches(df_pea)
        cap_injecte_pea = df_pea['capital_investi'].sum()
        capital_net = logic.get_perf_nette(df, 1)
        tri = logic.get_tri(df, engine, [1])

        st.markdown("<h2 style='text-align: center;'>PEA : S&P 500</h2>", unsafe_allow_html=True)

        st.metric(
            label=f"Derniere Cotation",
            value=f"{last:,.2f} €".replace(",", " ")
        )
    
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                label="Capital Total",
                value=f"{capital_pea:,.0f} €".replace(",", " ")
            )

        with col2:

            st.metric(
                label="Capital injecté",
                value=f"{cap_injecte_pea:.0f} €".replace(",", " ")
            )
        with col3:
            st.metric(
                label="Performance",
                value=f"{perf_pea['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_pea['pct']:.0f} %"
            )
        with col4:
            st.metric(
                label="Performance Annualisée",
                value=f"{tri:.1f} %",
                help="TRI : conversion de la performance en base annuelle"
            )
        with col5:
            st.metric(
                label="Capital net",
                value=f"{capital_net['net']:.0f} €".replace(",", " "),
                help="Capital net d'impots : 17.2 %"
            )


        st.divider()

        # JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
        st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {duree}</h4>", unsafe_allow_html=True)
    
        mapping_ptf = {1: "PEA"}
        perf_ptf_pea = logic.get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping_ptf)
        injecte = logic.get_injecte_periode(df_histo, df_periode, duree, date_debut, [1, 7])
        haut = df_cotation.iloc[0]['max']
        bas = df_cotation.iloc[0]['min']

        col6, col7, col8, col9 = st.columns(4)

        with col6:
            st.metric(
                label="Performance",
                value=f"{perf_ptf_pea['PEA']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_ptf_pea['PEA']['pct']:.0f} %"
            )
        with col7:
            st.metric(
                label="Injecté",
                value=f"{injecte:,.0f} €".replace(",", " "),
                help="Somme des dépots sur la periode"
            )
        with col8:
            st.metric(
                label="Haut",
                value=f"{haut:,.2f} €".replace(",", " "),
                help=f"Cours le plus haut sur"
            )
        with col9:
            st.metric(
                label="Bas",
                value=f"{bas:,.2f} €".replace(",", " "),
                help=f"Cours le plus bas"
            )

        
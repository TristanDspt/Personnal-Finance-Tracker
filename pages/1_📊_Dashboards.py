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
    choix_global = st.sidebar.radio("Choix", ["ETF", "PEA", "CTO", "STEF", "CiC"])

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

    case "ETF":
        df_etf = df.query("ptf_id in (1, 2)")
        df_cotation = db.get_cotations_pdt(engine, 2, date_debut)
        capital = logic.get_patrimoine_total(df_etf)
        perf = logic.get_perf_marches(df_etf)
        cap_injecte = df_etf['capital_investi'].sum()
        capital_net = logic.get_perf_nette(df, 2)
        tri = logic.get_tri_ptf(df, engine, [1, 2])

        # DONUTS — Préparation des DataFrames filtrés par enveloppe
        df_donut = df.query("ptf_id in [1, 2]").groupby('ptf_id')['capital_actuel'].sum().reset_index()
        df_donut['nom_pour_legende'] = df_donut['ptf_id'].map({1: "S&P 500", 2: "Gold"})

        fig = charts.make_donuts(
        df=df_donut, names='nom_pour_legende', values='capital_actuel',
        color_discrete_map={"S&P 500": "#822A2A", "Gold": "#D3AF37"},
        rotation=50, labels="Poids ETF", taille=194
        )

        st.markdown("<h2 style='text-align: center;'>ETF : PEA & CTO</h2>", unsafe_allow_html=True)
    
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Capital Total",
                value=f"{capital:,.0f} €".replace(",", " ")
            )
            st.metric(
                label="Capital injecté",
                value=f"{cap_injecte:,.0f} €".replace(",", " ")
            )

        with col2:
            st.metric(
                label="Performance Annualisée",
                value=f"{tri:.1f} %",
                help="TRI : conversion de la performance en base annuelle"
            )
            st.metric(
                label="Performance",
                value=f"{perf['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf['pct']:.0f} %"
            )


        with col3: st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        st.divider()

        # JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
        st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {duree}</h4>", unsafe_allow_html=True)
    
        mapping_ptf = {1: "PEA", 2: "CTO"}
        perf_ptf = logic.get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping_ptf)
        perf_etf_p = logic.get_perf_etf_periode(df_histo, df_periode, date_debut, duree)
        injecte = logic.get_injecte_periode(df_histo, df_periode, duree, date_debut, [1, 2, 7, 8])

        col6, col7, col8, col9 = st.columns(4)

        with col6:
            st.metric(
                label="Performance ETF",
                value=f"{perf_etf_p['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_etf_p['pct']:.0f} %"
            )
        with col7:
            st.metric(
                label="Injecté",
                value=f"{injecte:,.0f} €".replace(",", " "),
                help="Somme des dépots sur la periode"
            )
        with col8:
            st.metric(
                label="Performance PEA",
                value=f"{perf_ptf['PEA']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_ptf['PEA']['pct']:.0f} %"
            )
        with col9:
            st.metric(
                label="Performance CTO",
                value=f"{perf_ptf['CTO']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_ptf['CTO']['pct']:.0f} %"
            )


# DASH PEA

    case "PEA":

        df_pea = df.query("ptf_id == 1")
        df_cotation = db.get_cotations_pdt(engine, 1, date_debut)
        last = df_cotation.iloc[0]['cot_prix']
        capital = logic.get_patrimoine_total(df_pea)
        perf = logic.get_perf_marches(df_pea)
        cap_injecte = df_pea['capital_investi'].sum()
        capital_net = logic.get_perf_nette(df, 1)
        tri = logic.get_tri_ptf(df, engine, [1])

        st.markdown("<h2 style='text-align: center;'>PEA : S&P 500</h2>", unsafe_allow_html=True)

        st.metric(
            label=f"Dernier Cours",
            value=f"{last:,.2f} €".replace(",", " ")
        )
    
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        _, col1, col2, col3, _ = st.columns([0.5, 2, 2, 2, 0.5])

        with col1:
            st.metric(
                label="Capital Total",
                value=f"{capital:,.0f} €".replace(",", " ")
            )

        with col2:
            st.metric(
                label="Performance",
                value=f"{perf['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf['pct']:.0f} %"
            )


        with col3:
            st.metric(
                label="Performance Annualisée",
                value=f"{tri:.1f} %",
                help="TRI : conversion de la performance en base annuelle"
            )

        _, col4, col5, _ = st.columns([0.5, 1, 1, 0.5])

        with col4:
            st.metric(
                label="Capital net",
                value=f"{capital_net['net']:.0f} €".replace(",", " "),
                help="Capital net d'impots : 18.6 %"
            )
        with col5:
            st.metric(
                label="Capital injecté",
                value=f"{cap_injecte:.0f} €".replace(",", " ")
            )

        st.divider()

        # JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
        st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {duree}</h4>", unsafe_allow_html=True)
    
        mapping_ptf = {1: "PEA"}
        perf_ptf = logic.get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping_ptf)
        injecte = logic.get_injecte_periode(df_histo, df_periode, duree, date_debut, [1, 7])
        haut = df_cotation.iloc[0]['max']
        bas = df_cotation.iloc[0]['min']

        col6, col7, col8, col9 = st.columns(4)

        with col6:
            st.metric(
                label="Performance",
                value=f"{perf_ptf['PEA']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_ptf['PEA']['pct']:.0f} %"
            )
        with col7:
            st.metric(
                label="Haut",
                value=f"{haut:,.2f} €".replace(",", " "),
                help=f"Cours le plus haut sur"
            )
        with col8:
            st.metric(
                label="Bas",
                value=f"{bas:,.2f} €".replace(",", " "),
                help=f"Cours le plus bas"
            )
        with col9:
            st.metric(
                label="Injecté",
                value=f"{injecte:,.0f} €".replace(",", " "),
                help="Somme des dépots sur la periode"
            )


# DASH CTO

    case "CTO":
        df_cto = df.query("ptf_id == 2")
        df_cotation = db.get_cotations_pdt(engine, 2, date_debut)
        last = df_cotation.iloc[0]['cot_prix']
        capital = logic.get_patrimoine_total(df_cto)
        perf = logic.get_perf_marches(df_cto)
        cap_injecte = df_cto['capital_investi'].sum()
        capital_net = logic.get_perf_nette(df, 2)
        tri = logic.get_tri_ptf(df, engine, [2])

        st.markdown("<h2 style='text-align: center;'>CTO : GOLD</h2>", unsafe_allow_html=True)

        st.metric(
            label=f"Dernier Cours",
            value=f"{last:,.2f} €".replace(",", " ")
        )
    
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        _, col1, col2, col3, _ = st.columns([0.5, 2, 2, 2, 0.5])

        with col1:
            st.metric(
                label="Capital Total",
                value=f"{capital:,.0f} €".replace(",", " ")
            )
        with col2:
            st.metric(
                label="Performance",
                value=f"{perf['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf['pct']:.0f} %"
            )
        with col3:
            st.metric(
                label="Performance Annualisée",
                value=f"{tri:.1f} %",
                help="TRI : conversion de la performance en base annuelle"
            )

        _, col4, col5, _ = st.columns([0.5, 1, 1, 0.5])

        with col4:
            st.metric(
                label="Capital net",
                value=f"{capital_net['net']:.0f} €".replace(",", " "),
                help="Capital net d'impots : 18.6 %"
            )
        with col5:
            st.metric(
                label="Capital injecté",
                value=f"{cap_injecte:.0f} €".replace(",", " ")
            )

        st.divider()

        # JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
        st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {duree}</h4>", unsafe_allow_html=True)
    
        mapping_ptf = {2: "CTO"}
        perf_ptf = logic.get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping_ptf)
        injecte = logic.get_injecte_periode(df_histo, df_periode, duree, date_debut, [2, 8])
        haut = df_cotation.iloc[0]['max']
        bas = df_cotation.iloc[0]['min']

        col6, col7, col8, col9 = st.columns(4)

        with col6:
            st.metric(
                label="Performance",
                value=f"{perf_ptf['CTO']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_ptf['CTO']['pct']:.0f} %"
            )
        with col7:
            st.metric(
                label="Haut",
                value=f"{haut:,.2f} €".replace(",", " "),
                help=f"Cours le plus haut sur"
            )
        with col8:
            st.metric(
                label="Bas",
                value=f"{bas:,.2f} €".replace(",", " "),
                help=f"Cours le plus bas"
            )
        with col9:
            st.metric(
                label="Injecté",
                value=f"{injecte:,.0f} €".replace(",", " "),
                help="Somme des dépots sur la periode"
            )


# DASH STEF

    case "STEF":
        df_stef = df.query("ptf_id == 3")
        df_cotation = db.get_cotations_pdt(engine, 3, date_debut)
        last = df_cotation.iloc[0]['cot_prix']
        capital = logic.get_patrimoine_total(df_stef)
        abondement = df_stef["abondement_recu"].sum()
        perf = logic.get_perf_marches(df_stef)
        cap_injecte = df_stef['capital_investi'].sum()
        capital_net = logic.get_perf_nette(df, 3)
        tri = logic.get_tri_ptf(df, engine, [3])

        st.markdown("<h2 style='text-align: center;'>PEE : STEF</h2>", unsafe_allow_html=True)

        st.metric(
            label=f"Dernier Cours",
            value=f"{last:,.2f} €".replace(",", " ")
        )
    
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Capital Total",
                value=f"{capital:,.0f} €".replace(",", " ")
            )
        with col2:
            st.metric(
                label="Performance",
                value=f"{perf['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf['pct']:.0f} %"
            )
        with col3:
            st.metric(
                label="Performance Annualisée",
                value=f"{tri:.1f} %",
                help="TRI : conversion de la performance en base annuelle"
            )

        col4, col5, col6 = st.columns(3)

        with col4:
            st.metric(
                label="Capital net",
                value=f"{capital_net['net']:.0f} €".replace(",", " "),
                help="Capital net d'impots : 31,4 %"
            )
        with col5:
            st.metric(
                label="Capital injecté",
                value=f"{cap_injecte:,.0f} €".replace(",", " ")
            )
        with col6:
            st.metric(
                label="Abondement reçu",
                value=f"{abondement:,.0f} €".replace(",", " ")
            )

        st.divider()

        # JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
        st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {duree}</h4>", unsafe_allow_html=True)
    
        mapping_ptf = {3: "STEF"}
        perf_ptf = logic.get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping_ptf)
        injecte = logic.get_injecte_periode(df_histo, df_periode, duree, date_debut, [3])
        haut = df_cotation.iloc[0]['max']
        bas = df_cotation.iloc[0]['min']

        col7, col8, col9, col10 = st.columns(4)

        with col7:
            st.metric(
                label="Performance",
                value=f"{perf_ptf['STEF']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_ptf['STEF']['pct']:.0f} %"
            )
        with col8:
            st.metric(
                label="Injecté",
                value=f"{injecte:,.0f} €".replace(",", " "),
                help="Somme des dépots sur la periode"
            )
        with col9:
            st.metric(
                label="Haut",
                value=f"{haut:,.2f} €".replace(",", " "),
                help=f"Cours le plus haut sur"
            )
        with col10:
            st.metric(
                label="Bas",
                value=f"{bas:,.2f} €".replace(",", " "),
                help=f"Cours le plus bas"
            )


# DASH CiC

    case "CiC":
        df_cic = df.query("ptf_id == 4")
        df_cotation = db.get_cotations_pdt(engine, 4, date_debut)
        capital = logic.get_patrimoine_total(df_cic)
        abondement = df_cic["abondement_recu"].sum()
        perf = logic.get_perf_marches(df_cic)
        cap_injecte = df_cic['capital_investi'].sum()
        capital_net = logic.get_perf_nette(df, 4)
        tri = logic.get_tri_ptf(df, engine, [4])

        # DONUTS — Préparation des DataFrames filtrés par enveloppe
        df_donut = df.query("pdt_id in [4, 5, 6]").groupby('pdt_id')['capital_actuel'].sum().reset_index()
        df_donut['nom_pour_legende'] = df_donut['pdt_id'].map({4: "Obligation", 5: "Equilibre", 6: "Stratégie"})

        fig = charts.make_donuts(
        df=df_donut, names='nom_pour_legende', values='capital_actuel',
        color_discrete_map={"Obligation": "#018289", "Equilibre": "#0f228b", "Stratégie": "#fe330f"},
        rotation=180, labels="Poids CiC", taille=194
        )

        st.markdown("<h2 style='text-align: center;'>PEE : CiC</h2>", unsafe_allow_html=True)
    
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Capital Total",
                value=f"{capital:,.0f} €".replace(",", " ")
            )
            st.metric(
                label="Capital net",
                value=f"{capital_net['net']:.0f} €".replace(",", " "),
                help="Capital net d'impots : 31,4 %"
            )
        with col2:
            st.metric(
                label="Performance",
                value=f"{perf['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf['pct']:.0f} %"
            )
            st.metric(
                label="Capital injecté",
                value=f"{cap_injecte:,.0f} €".replace(",", " ")
            )
        with col3:
            st.metric(
                label="Performance Annualisée",
                value=f"{tri:.1f} %",
                help="TRI : conversion de la performance en base annuelle"
            )
            st.metric(
                label="Abondement reçu",
                value=f"{abondement:,.0f} €".replace(",", " ")
            )

        with col4: st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
        st.divider()

        # KPIs GÉNÉRAUX — Capital total + perfs globales (hors période)
        tri_pdt = logic.get_tri_pdt(df, engine, [4, 5, 6])

        col5, col6, col7 = st.columns(3)
        
        with col5:
            st.metric(
                label="Performance Annualisée Obligation",
                value=f"{tri_pdt[4]:.1f} %",
            )
        with col6:
            st.metric(
                label="Performance Annualisée Equilibre",
                value=f"{tri_pdt[5]:.1f} %",
            )
        with col7:
            st.metric(
                label="Performance Annualisée Stratégie",
                value=f"{tri_pdt[6]:.1f} %",
            )
        
        st.divider()

        # JOURNAL DE BORD — KPIs par enveloppe sur la période sélectionnée (réactif au slider)
        st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {duree}</h4>", unsafe_allow_html=True)
    
        mapping_ptf = {4: "CiC"}
        perf_ptf = logic.get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping_ptf)
        perf_pdt = logic.get_perf_pdt_periode(df_histo, df_periode, duree, date_debut, [4, 5, 6])

        col7, col8, col9, col10 = st.columns(4)

        with col7:
            st.metric(
                label="Performance CiC",
                value=f"{perf_ptf['CiC']['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_ptf['CiC']['pct']:.0f} %"
            )
        with col8:
            st.metric(
                label="Performance Obligation",
                value=f"{perf_pdt[4]['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_pdt[4]['pct']:.0f} %"
            )
        with col9:
            st.metric(
                label="Performance Equilibre",
                value=f"{perf_pdt[5]['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_pdt[5]['pct']:.0f} %"
            )
        with col10:
            st.metric(
                label="Performance Stratégie",
                value=f"{perf_pdt[6]['euro']:,.0f} €".replace(",", " "),
                delta=f"{perf_pdt[6]['pct']:.0f} %"
            )
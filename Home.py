import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# -----------------------------------------------------------------------------------------------------------------

# CONFIG TECHNIQUE

# 1. Configuration de la page
st.set_page_config(
    page_title="Home",
    page_icon="🏠",
    layout="wide"
)

# 2. Initialisation de la connexion (Engine SQLAlchemy)
# On utilise st.cache_resource pour ne pas recréer la connexion à chaque clic
@st.cache_resource
def get_engine():
    creds = st.secrets["postgres"]
    url = f"postgresql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    return create_engine(url)

engine = get_engine()

# -----------------------------------------------------------------------------------------------------------------

#IMPORT DE LA SUPER VUE SQL
df = pd.read_sql("SELECT * FROM view_global_portefeuille", engine)

# INTERFACE GRAPHIQUE

# --- 1. BLOC TITRE ---
st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>🏛️ Personnal Finance Tracker 🏛️</h1>", unsafe_allow_html=True)
st.divider() # Un petit trait pour séparer proprement

# --- 2. FILTRES ---
# Ton slider de durée ici pour qu'il pilote tout le reste
duree = st.sidebar.select_slider("Période d'analyse", options=["1 Mois", "3 Mois", "6 Mois", "1 An", "3 Ans", "5 Ans", "Max"])

# On traduit le texte en jours
mapping_duree = {
    "1 Mois": 30,
    "3 Mois": 90,
    "6 Mois": 180,
    "1 An": 365,
    "Max": 12000
}
jours = mapping_duree[duree]

# --- 3. INSIGHTS ---

# CALCUL GENERAUX
# Capital
capital = df['capital_actuel'].sum()

# Profit total en euros (hors cash)
df_bourse = df.query("pdt_cash == False")
profit_euro = df_bourse['profit_euro'].sum() 

# Profit total en %
investi_bourse = df_bourse['capital_investi'].sum()
abondement = df_bourse['abondement_recu'].sum()
total_investi = investi_bourse + abondement
profit_pcent = (profit_euro / total_investi * 100) if total_investi > 0 else 0

# Perf ETF
df_etf = df.query("pdt_id in [1, 2]")
perf_etf_euro = df_etf['profit_euro'].sum()
investi_etf = df_etf['capital_investi'].sum()
perf_etf_pcent = (perf_etf_euro / investi_etf * 100) if investi_etf > 0 else 0

# Calcul par enveloppe
portefeuilles = {1: "PEA", 2: "CTO", 3: "STEF", 4: "CiC"}
perf = {}

for ptf_id, ptf_nom in portefeuilles.items():
    df_temp = df.query("ptf_id == @ptf_id")

    profit_local = df_temp['profit_euro'].sum()
    investi_local = df_temp['capital_investi'].sum()
    abondement_local = df_temp['abondement_recu'].sum()

    total_local = investi_local + abondement_local
    local_pcent = profit_local / total_local * 100 if total_local > 0 else 0

    perf[ptf_nom] = {"prof": profit_local, "pct": local_pcent}

# Calcul des poids
etf_ids = [1, 2]
pee_ids = [3, 4]
livret_ids = [6]

if capital > 0:
    poids_etf = df.query("ptf_id in @etf_ids")['capital_actuel'].sum() / capital * 100
    poids_pee = df.query("ptf_id in @pee_ids")['capital_actuel'].sum() / capital * 100
    poids_livret = df.query("ptf_id in @livret_ids")['capital_actuel'].sum() / capital * 100
else:
    poids_etf = poids_pee = poids_livret = 0

# --- 4. INTERFACE GRAPHIQUE ---

st.markdown("""
    <style>
    /* Centre la métrique entière dans sa colonne */
    [data-testid="stMetric"] {
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    /* Centre spécifiquement le label (titre) */
    [data-testid="stMetricLabel"] {
        justify-content: center;
        width: 100%;
    }

    /* Centre la valeur numérique */
    [data-testid="stMetricValue"] {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

_, col1, col2, col3, _ = st.columns([0.5, 1, 1, 1, 0.5])

with col1:
    st.metric(
        label="Patrimoine Total", 
        value=f"{capital:,.0f} €".replace(",", " "),
        help="Somme totale de tous les actifs (Cash + Titres)"
    )

with col2:
    st.metric(
        label="Performance Totale", 
        value=f"{profit_pcent:.0f} %",
        delta=f"{profit_euro:,.0f} €".replace(",", " "),
        help="Rendement total par rapport au capital investi (Hors livrets d'épargne)"
    )

with col3:
    st.metric(
        label="Performance ETF", 
        value=f"{perf_etf_pcent:.0f} %",
        delta=f"{perf_etf_euro:,.0f} €".replace(",", " "),
        help="Rendement des enveloppes ETF"
    )

col4, col5, col6, col7 = st.columns(4)

with col4:
    st.metric(
        label="Performance PEA", 
        value=f"{perf['PEA']['prof']:.0f} €",
        delta=f"{perf['PEA']['pct']:.0f} %",
        help="Rendement total par rapport au capital investi"
    )

with col5:
    st.metric(
        label="Performance CTO", 
        value=f"{perf['CTO']['prof']:.0f} €",
        delta=f"{perf['CTO']['pct']:.0f} %",
        help="Rendement total par rapport au capital investi"
    )

with col6:
    st.metric(
        label="Performance STEF", 
        value=f"{perf['STEF']['prof']:.0f} €",
        delta=f"{perf['STEF']['pct']:.0f} %",
        help="Rendement total par rapport au capital investi"
    )

with col7:
    st.metric(
        label="Performance CiC", 
        value=f"{perf['CiC']['prof']:.0f} €",
        delta=f"{perf['CiC']['pct']:.0f} %",
        help="Rendement total par rapport au capital investi"
    )

# --- 5. GRAPHIQUES ---

# Design Commun
def apply_style(fig):
    fig.update_traces(
        textinfo='percent',
        texttemplate='<b>%{percent:.0%}</b>',
        textposition='inside',
        insidetextorientation='horizontal',
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} €<extra></extra>"
    )
common_layout = dict(
    height=180,
    showlegend=False,
    margin=dict(t=0, b=0, l=0, r=0),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    separators=", "
)

# ETF (ID 1 & 2)
df_etf = df.query("ptf_id in [1, 2]").groupby('ptf_id')['capital_actuel'].sum().reset_index()
df_etf['nom_pour_legende'] = df_etf['ptf_id'].map({1: "S&P 500", 2: "Gold"})
fig_etf = px.pie(df_etf, 
                 names='nom_pour_legende', 
                 values="capital_actuel", 
                 hole=0.68,
                 color="ptf_id",
                 color_discrete_map={1: "#822A2A", 2: "#D3AF37"})
apply_style(fig_etf)
fig_etf.update_traces(rotation=50)
fig_etf.update_layout(common_layout, annotations=[
    dict(text="Poids ETF", x=0.5, y=0.6, showarrow=False, font=dict(size=18)),
    dict(text=f"<b>{poids_etf:.0f}%</b>", x=0.51, y=0.4, showarrow=False, font=dict(size=35))
])

# PEE (ID 3 & 4)
df_pee = df.query("ptf_id in [3, 4]").groupby('ptf_id')['capital_actuel'].sum().reset_index()
df_pee['nom_pour_legende'] = df_pee['ptf_id'].map({3: "STEF", 4: "CiC"})
fig_pee = px.pie(df_pee, 
                 names='nom_pour_legende', 
                 values="capital_actuel", 
                 hole=0.68,
                 color="ptf_id",
                 color_discrete_map={3: "#00519e", 4: "#018289"})
apply_style(fig_pee)
fig_pee.update_traces(rotation=80)
fig_pee.update_layout(common_layout, annotations=[
    dict(text="Poids PEE", x=0.5, y=0.6, showarrow=False, font=dict(size=18)),
    dict(text=f"<b>{poids_pee:.0f}%</b>", x=0.517, y=0.4, showarrow=False, font=dict(size=35))
])

# Livrets (ID 6)
df_liv = df.query("pdt_id in [10, 11]").groupby('pdt_id')['capital_actuel'].sum().reset_index()
df_liv['nom_pour_legende'] = df_liv['pdt_id'].map({10: "Livret A", 11: "PEA"})
fig_liv = px.pie(df_liv, 
                 names='nom_pour_legende', 
                 values="capital_actuel", 
                 hole=0.68,
                 color="pdt_id",
                 color_discrete_map={10: "#FF8C00", 11: "#540A88"})
apply_style(fig_liv)
fig_liv.update_traces(rotation=90)
fig_liv.update_layout(common_layout, annotations=[
    dict(text="Poids Livrets", x=0.5, y=0.6, showarrow=False, font=dict(size=18)),
    dict(text=f"<b>{poids_livret:.0f}%</b>", x=0.51, y=0.4, showarrow=False, font=dict(size=35))
])

# Affichage
_, col8, col9, col10, _ = st.columns([0.5, 1, 1, 1, 0.5])
with col8: st.plotly_chart(fig_etf, use_container_width=True, config={'displayModeBar': False})
with col9: st.plotly_chart(fig_pee, use_container_width=True, config={'displayModeBar': False})
with col10: st.plotly_chart(fig_liv, use_container_width=True, config={'displayModeBar': False})

st.divider()

# --- 4. TABLEAU GLOBAL ---
st.write("### 📊 État des Lieux Global")
# Ton st.dataframe(df_filtre) ici

st.divider()

# --- 5. GRAPHIQUES ---
st.write("### 📈 Analyses Graphiques")
row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.write("Graph 1") # Ex: Évolution Capital

with row1_col2:
    st.write("Graph 2") # Ex: Allocation

row2_col1, row2_col2 = st.columns(2)
# etc...
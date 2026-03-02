import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go

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

#IMPORT DES VUE SQL
df = pd.read_sql("SELECT * FROM view_global_portefeuille", engine)
df_histo = pd.read_sql("SELECT * FROM view_historique_portefeuille", engine)
df_apports = pd.read_sql("SELECT * FROM view_apports_mensuels", engine)

# INTERFACE GRAPHIQUE

# --- 1. BLOC TITRE ---
st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>🏛️ Personnal Finance Tracker 🏛️</h1>", unsafe_allow_html=True)
st.divider()

# Sidebar

with st.sidebar:
    st.title("⚙️ Menu")
    
    st.subheader("💰 Cash en attente")

    cash_pea = df.query("pdt_id == 7")['capital_actuel'].fillna(0).iloc[0]
    cash_cto = df.query("pdt_id == 8")['capital_actuel'].fillna(0).iloc[0]
    
    st.write(f"**PEA :** `{cash_pea:,.2f} €`".replace(',', ' '))
    st.write(f"**CTO :** `{cash_cto:,.2f} €`".replace(',', ' '))

    if cash_pea > 400:
        st.warning(f"⚠️ {cash_pea:,.2f}€ sur le PEA !".replace(',', ' '))

    st.divider()

    st.subheader("🛠️ Configuration")
    duree = st.select_slider(
        "Période d'analyse", 
        options=["1 Mois", "3 Mois", "6 Mois", "1 An", "3 Ans", "5 Ans", "Max"],
        value= "6 Mois"
    )
    vue_12m = st.toggle("12 mois roulants", value=False)

# --- 2. LOGIQUE TEMPORELLE ---

# 1. Traduction en jours
mapping_duree = {
    "1 Mois": 1, 
    "3 Mois": 3, 
    "6 Mois": 6, 
    "1 An": 12, 
    "3 Ans": 36, 
    "5 Ans": 60, 
    "Max": 600
}
nb_mois = mapping_duree[duree]

# 2. Définition de la date pivot
# date_debut = pd.Timestamp.now() - pd.Timedelta(days=jours)
date_debut = pd.Timestamp.now() - pd.DateOffset(months=nb_mois)

# 3. Création des DataFrames filtrés
# On convertit en datetime si ce n'est pas fait à l'import
df_histo['jour'] = pd.to_datetime(df_histo['jour'])

# DataFrame filtré sur la période
df_periode = df_histo[df_histo['jour'] >= date_debut]

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
df_etf_kpi = df.query("pdt_id in [1, 2]")
perf_etf_euro = df_etf_kpi['profit_euro'].sum()
investi_etf = df_etf_kpi['capital_investi'].sum()
perf_etf_pcent = (perf_etf_euro / investi_etf * 100) if investi_etf > 0 else 0

# Calcul des poids
etf_ids = [1, 2]
pee_ids = [3, 4]
livret_ids = [6]

if capital > 0:
    poids_etf = df.query("ptf_id in @etf_ids and pdt_est_actif == True")['capital_actuel'].sum() / capital * 100
    poids_pee = df.query("ptf_id in @pee_ids and pdt_est_actif == True")['capital_actuel'].sum() / capital * 100
    poids_livret = df.query("ptf_id in @livret_ids and pdt_est_actif == True")['capital_actuel'].sum() / capital * 100
else:
    poids_etf = poids_pee = poids_livret = 0

# Performance combinée (PEA + CTO)
df_etf_periode = (df_periode.query("ptf_id in [1, 2]")
               .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi']]
               .sum()
               .reset_index()
               .query("capital_investi > 1")
               .sort_values('jour'))

if not df_etf_periode.empty:
    snap_debut, snap_fin = df_etf_periode.iloc[0], df_etf_periode.iloc[-1]

    if duree == "Max":
        perf_etf_periode_euro = snap_fin['profit_euro']
    else:
        perf_etf_periode_euro = snap_fin['profit_euro'] - snap_debut['profit_euro']

    perf_etf_periode_pct = (perf_etf_periode_euro / snap_fin['capital_investi'] * 100) if snap_fin['capital_investi'] > 0 else 0
else:
    perf_etf_periode_euro, perf_etf_periode_pct = 0, 0

# Calcul par enveloppe
portefeuilles = {1: "PEA", 2: "CTO", 3: "STEF", 4: "CiC"}
perf = {}

for ptf_id, ptf_nom in portefeuilles.items():
    df_temp = (df_periode.query("ptf_id == @ptf_id")
               .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
               .sum()
               .reset_index()
               .query("capital_investi + abondement_recu > 1")
               .sort_values('jour'))

    if not df_temp.empty:
        snap_debut, snap_fin = df_temp.iloc[0], df_temp.iloc[-1]

        if duree == "Max":
            profit_local = snap_fin['profit_euro']
        else:
            profit_local = snap_fin['profit_euro'] - snap_debut['profit_euro']

        base_locale = snap_fin['capital_investi'] + snap_fin['abondement_recu']
        local_pcent = (profit_local / base_locale * 100) if base_locale > 0 else 0
    else:
        profit_local, local_pcent = 0, 0

    perf[ptf_nom] = {"prof": profit_local, "pct": local_pcent}

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

# st.markdown("<h2 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>🕰️ Historique</h2>", unsafe_allow_html=True)

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

# DONUTS

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
df_etf_donut  = df.query("ptf_id in [1, 2]").groupby('ptf_id')['capital_actuel'].sum().reset_index()
df_etf_donut ['nom_pour_legende'] = df_etf_donut ['ptf_id'].map({1: "S&P 500", 2: "Gold"})
fig_etf = px.pie(df_etf_donut , 
                 names='nom_pour_legende', 
                 values="capital_actuel", 
                 hole=0.68,
                 color="ptf_id",
                 color_discrete_map={1: "#822A2A", 2: "#D3AF37"})
apply_style(fig_etf)
fig_etf.update_traces(rotation=50)
fig_etf.update_layout(common_layout, hoverlabel=dict(font_size=15), annotations=[
    dict(text="Poids ETF", x=0.5, y=0.6, showarrow=False, font=dict(size=18)),
    dict(text=f"<b>{poids_etf:.0f}%</b>", x=0.51, y=0.4, showarrow=False, font=dict(size=35))
])

# PEE (ID 3 & 4)
df_pee_donuts = df.query("ptf_id in [3, 4]").groupby('ptf_id')['capital_actuel'].sum().reset_index()
df_pee_donuts['nom_pour_legende'] = df_pee_donuts['ptf_id'].map({3: "STEF", 4: "CiC"})
fig_pee = px.pie(df_pee_donuts, 
                 names='nom_pour_legende', 
                 values="capital_actuel", 
                 hole=0.68,
                 color="ptf_id",
                 color_discrete_map={3: "#00519e", 4: "#018289"})
apply_style(fig_pee)
fig_pee.update_traces(rotation=80)
fig_pee.update_layout(common_layout, hoverlabel=dict(font_size=15), annotations=[
    dict(text="Poids PEE", x=0.5, y=0.6, showarrow=False, font=dict(size=18)),
    dict(text=f"<b>{poids_pee:.0f}%</b>", x=0.517, y=0.4, showarrow=False, font=dict(size=35))
])

# Livrets (ID 6)
df_liv_donuts = df.query("pdt_id in [10, 11]").groupby('pdt_id')['capital_actuel'].sum().reset_index()
df_liv_donuts['nom_pour_legende'] = df_liv_donuts['pdt_id'].map({10: "Livret A", 11: "LEP"})
fig_liv = px.pie(df_liv_donuts, 
                 names='nom_pour_legende', 
                 values="capital_actuel", 
                 hole=0.68,
                 color="pdt_id",
                 color_discrete_map={10: "#FF8C00", 11: "#540A88"})
apply_style(fig_liv)
fig_liv.update_traces(rotation=0)
fig_liv.update_layout(common_layout, hoverlabel=dict(font_size=15), annotations=[
    dict(text="Poids Livrets", x=0.5, y=0.6, showarrow=False, font=dict(size=18)),
    dict(text=f"<b>{poids_livret:.0f}%</b>", x=0.51, y=0.4, showarrow=False, font=dict(size=35))
])

# Affichage
col4, col5, col6 = st.columns(3)
with col4: st.plotly_chart(fig_etf, use_container_width=True, config={'displayModeBar': False})
with col5: st.plotly_chart(fig_pee, use_container_width=True, config={'displayModeBar': False})
with col6: st.plotly_chart(fig_liv, use_container_width=True, config={'displayModeBar': False})

st.divider()

# --- 4. JOURNAL DE BORD --- (réactif au slider)

st.markdown(f"<h4 style='text-align: center; margin-top: -20px; margin-bottom: 15px;'>📅 Journal de bord : {duree}</h4>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Performance ETF", 
        value=f"{perf_etf_periode_euro:,.0f} €".replace(",", " "),
        delta=f"{perf_etf_periode_pct:.0f} %",
        help="Rendement des enveloppes ETF"
    )

with col2:
    st.metric(
        label="Performance PEA", 
        value=f"{perf['PEA']['prof']:,.0f} €".replace(",", " "),
        delta=f"{perf['PEA']['pct']:.0f} %",
        help="Rendement total par rapport au capital investi"
    )

with col3:
    st.metric(
        label="Performance CTO", 
        value=f"{perf['CTO']['prof']:,.0f} €".replace(",", " "),
        delta=f"{perf['CTO']['pct']:.0f} %",
        help="Rendement total par rapport au capital investi"
    )

with col4:
    st.metric(
        label="Performance STEF", 
        value=f"{perf['STEF']['prof']:,.0f} €".replace(",", " "),
        delta=f"{perf['STEF']['pct']:.0f} %",
        help="Rendement total par rapport au capital investi"
    )

with col5:
    st.metric(
        label="Performance CiC", 
        value=f"{perf['CiC']['prof']:,.0f} €".replace(",", " "),
        delta=f"{perf['CiC']['pct']:.0f} %",
        help="Rendement total par rapport au capital investi"
    )

# LE TABLEAU

# Mapping calendaire
debut_mois_actuel = pd.Timestamp.now().replace(day=1)
date_depart_tableau = debut_mois_actuel - pd.DateOffset(months=nb_mois)

# Mapping par PTF_ID
mapping_ptf = {
    1: "ETF", 
    2: "ETF", 
    3: "STEF", 
    4: "CiC",
    6: "Livrets",
}

# Création du DF
df_mensuel = df_histo.copy()
df_mensuel['Enveloppe'] = df_mensuel['ptf_id'].map(mapping_ptf)

df_journalier = (df_mensuel.groupby(['Enveloppe', 'jour'])
                 .agg({'capital_actuel': 'sum', 'capital_investi': 'sum'})
                 .reset_index())

df_pivot = (df_journalier.groupby(['Enveloppe', pd.Grouper(key='jour', freq='ME')])
            .agg({'capital_actuel': 'last', 'capital_investi': 'last'})
            .unstack(level=0))

df_final = df_pivot['capital_actuel'].copy()

# Calcul des colonnes
df_final['Total'] = df_final.sum(axis=1)

df_final['Evo Patrimoine'] = df_final['Total'].diff()
df_final['Evo (%)'] = (df_final['Evo Patrimoine'] / df_final['Total'].shift(1)) * 100

df_apports['mois'] = df_apports['mois'].apply(lambda x: pd.Timestamp(x).replace(tzinfo=None).normalize())
df_apports = df_apports.set_index('mois')
injecte_mois = df_apports['injecte'].reindex(df_final.index, fill_value=0)
df_final['Perf Marchés (€)'] = df_final['Evo Patrimoine'] - injecte_mois

df_final['Evo 12m (€)'] = df_final['Total'] - df_final['Total'].shift(12)
df_final['Evo 12m (%)'] = (df_final['Evo 12m (€)'] / df_final['Total'].shift(12)) * 100

# Nettoyage
df_final = df_final.query("jour >= @date_depart_tableau")

df_final_graph = df_final.copy()

colonnes_ordre = [
    'ETF', 'STEF', 'CiC', 'Livrets', 'Total', 
    'Evo Patrimoine', 'Evo (%)', 'Perf Marchés (€)'
]
if vue_12m:
    colonnes_ordre.extend(['Evo 12m (€)', 'Evo 12m (%)'])

colonnes_enveloppes = set(mapping_ptf.values())
tableau = []
for c in colonnes_ordre:
    if c in colonnes_enveloppes:
        if c in df_final.columns and df_final[c].notna().any() and df_final[c].sum() > 0:
            tableau.append(c)
    else:
        if c in df_final.columns and df_final[c].notna().any():
            tableau.append(c)

df_final = df_final[tableau]
df_final = df_final.iloc[1:].sort_index(ascending=False)

df_final.index.name = 'Mois'

mois_fr = {
    1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
    5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
    9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
}
df_final.index = df_final.index.map(lambda x: f"{mois_fr[x.month]} {x.year}")

format_complet = {
        'ETF': "{:,.2f} €", 'STEF': "{:,.2f} €", 'CiC': "{:,.2f} €", 
        'Livrets': "{:,.2f} €", 'Total': "{:,.2f} €", 'Evo Patrimoine': "{:,.2f} €",
        'Perf Marchés (€)': "{:,.2f} €", 'Evo 12m (€)': "{:,.0f} €",
        'Evo (%)': "{:.2f} %", 'Evo 12m (%)': "{:.1f} %"
    }
format_filtre = {k: v for k, v in format_complet.items() if k in df_final.columns}

st.dataframe(
    df_final.style.format(format_filtre, na_rep='-', thousands=" ")
    .applymap(lambda x: 'color: #ff4b4b' if x < 0 else 'color: #09ab3b', 
              subset=[c for c in ['Evo Patrimoine', 'Evo (%)', 'Perf Marchés (€)'] if c in df_final.columns]), 
    use_container_width=True, height=min(35 * len(df_final) + 38, 458)
)

st.divider()

# --- 5. GRAPHIQUE ---

# Création des DF
df_apports_graph = df_apports.copy()
df_apports_graph['cumsum'] = df_apports_graph['injecte'].cumsum()
index_complet = pd.date_range(
    start=df_apports_graph.index.min(), 
    end=pd.Timestamp.today() + pd.offsets.MonthEnd(), 
    freq='ME'
)
df_apports_graph = df_apports_graph.reindex(index_complet).ffill()
df_apports_graph_filtre = df_apports_graph[df_apports_graph.index >= date_depart_tableau]
df_apports_graph_filtre.index = df_apports_graph_filtre.index.to_period('M').to_timestamp()
df_apports_graph_filtre = df_apports_graph_filtre.iloc[1:]

df_capital_graph = df_final_graph.copy()
df_capital_graph['perf_graph'] = (df_capital_graph['Perf Marchés (€)'] / df_capital_graph['Total'].shift(1)) * 100
df_capital_graph.index = df_capital_graph.index.to_period('M').to_timestamp()
df_capital_graph = df_capital_graph.iloc[1:]

df_capital_graph['delta'] = df_capital_graph['Total'] - df_apports_graph_filtre['cumsum']

# Params
couleurs = df_capital_graph['perf_graph'].apply(lambda x: '#ff4b4b' if x < 0 else '#09ab3b')

# Dessin
graph = go.Figure()

graph.add_trace(go.Scatter(
    x=df_capital_graph.index,  
    y=df_capital_graph['Total'], 
    name="Capital",
    mode='lines+markers',
    marker=dict(size=4),
    yaxis="y2",
    line=dict(color='#FFD700'),
    customdata=df_capital_graph['delta'],
    hovertemplate="%{y:,.0f} €<br>Delta: %{customdata:,.0f} €"
))

graph.add_trace(go.Scatter(
    x=df_apports_graph_filtre.index,  
    y=df_apports_graph_filtre['cumsum'],  
    name="Injecté",
    mode='lines+markers',
    marker=dict(size=4),
    yaxis="y2",
    line=dict(color='#4DA6FF'),
    hovertemplate="%{y:,.0f} €",
))

graph.add_trace(go.Bar(
    x=df_capital_graph.index,
    y=df_capital_graph['perf_graph'],
    name="Perf Marchés",
    marker=dict(color=couleurs, opacity=0.8),
    width=1000*3600*24*3,
    hovertemplate="%{y:,.2f} %"
))

# Habillage
y_min = min(df_capital_graph['Total'].min(), df_apports_graph_filtre['cumsum'].min()) * 0.95
y_max = max(df_capital_graph['Total'].max(), df_apports_graph_filtre['cumsum'].max()) * 1.05

graph.update_layout(
    yaxis=dict(title="Perf %", showgrid=False),
    yaxis2=dict(
        side='right', 
        overlaying='y', 
        range=[y_min, y_max],
        title="Capital (€)"
        ), 
    legend=dict(orientation='h', y=1.1, x=0.5, xanchor='center'),
    height=600,
    hovermode='x unified',
    hoverlabel=dict(font_size=15),
    separators=". "
    )

if duree != "1 Mois":
    st.plotly_chart(graph, use_container_width=True)
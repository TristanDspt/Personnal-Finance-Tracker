import streamlit as st
import components.database as db
import components.st_logic as logic
import components.st_charts as charts


# --- 1. CONFIGURATION PAGE ---
st.set_page_config(page_title="Projections", page_icon="🚀", layout="wide")

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
        min-height: 2rem;
        display: flex;
        align-items: flex-end;
    }
    [data-testid="stMetricValue"] {
        width: 100%;
    }
    [data-testid="stMetricDelta"] {
    justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)


# --- 2. CONNEXION & CHARGEMENT DES VUES SQL ---

engine = db.get_engine()


# --- 3. SIDEBAR ---

with st.sidebar:
    st.title("⚙️ Menu")

    # Choix de l'enveloppe
    choix_global = st.sidebar.radio("Menu", ["", "PEA", "CTO", "STEF", "CiC"], label_visibility="collapsed")

    st.divider()

    # Slider de période — contrôle tous les blocs réactifs de la page
    st.subheader("🛠️ Configuration")
    duree = st.select_slider(
        "Période d'analyse",
        options=["Début Mois", "15 Jours", "1 Mois", "3 Mois", "6 Mois", "1 An", "3 Ans", "5 Ans", "Max"],
        value="6 Mois"
    )
    # Toggle pour afficher les graphs détaillés sur le desh CiC
    if choix_global == "CiC":
        vue_detail = st.toggle("Vue détaillée", value=False)
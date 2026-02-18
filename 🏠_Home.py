import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Configuration de la page
st.set_page_config(
    page_title="PFT - Global Dashboard",
    page_icon="🏠",
    layout="wide"
)

# BLOC TITRE
st.markdown("<h1 style='text-align: center;'>🏛️ Personnal Finance Tracker 🏛️</h1>", unsafe_allow_html=True)
st.write("")
st.write("#### 🏠 Home")
st.divider() # Un petit trait pour séparer proprement

# 2. Initialisation de la connexion (Engine SQLAlchemy)
# On utilise st.cache_resource pour ne pas recréer la connexion à chaque clic
@st.cache_resource
def get_engine():
    creds = st.secrets["postgres"]
    url = f"postgresql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    return create_engine(url)

engine = get_engine()

# --- BLOC DE TEST ---
try:
    # Test rapide : on compte juste tes lignes de transactions ou une table clé
    with engine.connect() as conn:
        st.success("✅ Connecté à la base PFT avec succès !")
except Exception as e:
    st.error(f"❌ Erreur de connexion : {e}")

# --- TES CHIFFRES CLÉS (METRICS) ---
st.subheader("Synthèse globale")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Valeur Totale", value="-- €", delta="-- %")

with col2:
    st.metric(label="Cash Dispo", value="-- €")

with col3:
    st.metric(label="Performance", value="-- €")


import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import scripts.database as db
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# 0. CONFIGURATION PAGE (Doit être en premier)
st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# BLOC TITRE
#st.markdown("<h1 style='text-align: center; margin-bottom: 40px;'>🏛️ Personnal Finance Tracker 🏛️</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>📊 Dashboards</h2>", unsafe_allow_html=True)
st.divider() # Un petit trait pour séparer proprement

choix_global = st.sidebar.radio("Enveloppe", ["PEA", "CTO", "STEF", "CIC"])
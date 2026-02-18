import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Configuration de la page
st.set_page_config(
    page_title="Home",
    page_icon="📊",
    layout="wide"
)

# BLOC TITRE
st.markdown("<h1 style='text-align: center;'>🏛️ Personnal Finance Tracker 🏛️</h1>", unsafe_allow_html=True)
st.write("")
st.write("#### 📊 Dashboards")
st.divider() # Un petit trait pour séparer proprement
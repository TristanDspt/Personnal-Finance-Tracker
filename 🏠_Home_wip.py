import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
import plotly.graph_objects as go
import scripts.database as db

# -----------------------------------------------------------------------------------------------------------------

# CONFIG TECHNIQUE

# 1. Configuration de la page
st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")

engine = db.get_engine()

#IMPORT DES VUE SQL
df = db.get_view("view_global_portefeuille", engine)
df_histo = db.get_view("view_historique_portefeuille", engine)
df_apports = db.get_view("view_apports_mensuels", engine)

# -----------------------------------------------------------------------------------------------------------------

# INTERFACE GRAPHIQUE


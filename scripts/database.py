import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

@st.cache_resource
def get_engine():
    creds = st.secrets["postgres"]
    url = f"postgresql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    return create_engine(url)

@st.cache_data
def get_view(view_name, engine):
    df = pd.read_sql(f"SELECT * FROM {view_name}", engine)
    return df
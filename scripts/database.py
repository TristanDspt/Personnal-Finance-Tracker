import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

@st.cache_resource
def get_engine():
    creds = st.secrets["postgres"]
    url = f"postgresql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    return create_engine(url)

@st.cache_data
def get_view(view_name, _engine):
    df = pd.read_sql(f"SELECT * FROM {view_name}", _engine)
    return df

def get_cotations_pdt(engine, pdt_id, date_debut):
    query = """
        WITH slider AS (
        SELECT 
            max(cot_prix) AS max,
            min(cot_prix) AS min
        FROM cotation_cot
        WHERE 
            pdt_id = %(pdt_id)s
            AND cot_date >= %(date_debut)s
        ),
        dernier AS (
            SELECT 
                cot_date,
                cot_prix,
                ROW_NUMBER() OVER (PARTITION BY pdt_id ORDER BY cot_date DESC) AS rn
            FROM cotation_cot
            WHERE 
                pdt_id = %(pdt_id)s
        )
        SELECT
            s.max,
            s.min,
            d.cot_date,
            d.cot_prix
        FROM dernier d
        CROSS JOIN slider s
        WHERE rn = 1
    """
    df_cotation = pd.read_sql(query, engine, params={"pdt_id": pdt_id, "date_debut": date_debut})

    return df_cotation
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

@st.cache_resource
def get_engine():
    """Crée et met en cache la connexion SQLAlchemy à PostgreSQL."""
    creds = st.secrets["postgres"]
    url = f"postgresql://{creds['user']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
    return create_engine(url)


@st.cache_data
def get_view(view_name, _engine):
    """
    Charge une vue SQL complète en DataFrame et la met en cache.
    
    Args:
        view_name (str): nom de la vue SQL (ex: "view_global_portefeuille")
        _engine: connexion SQLAlchemy (préfixe _ pour exclure du cache Streamlit)
    
    Returns:
        DataFrame: contenu complet de la vue
    """
    df = pd.read_sql(f"SELECT * FROM {view_name}", _engine)
    return df


def get_cotations_pdt(engine, pdt_id, date_debut):
    """
    Récupère le cours actuel et les extremes de prix sur la période sélectionnée.

    Args:
        engine: connexion SQLAlchemy
        pdt_id (int): id du produit financier
        date_debut (pd.Timestamp): date de début de la période (depuis get_date_debut())

    Returns:
        DataFrame: une ligne avec [max, min, cot_date, cot_prix]
    """
    query = """
        WITH slider AS (
            -- High et Low sur la période filtrée
            SELECT 
                max(cot_prix) AS max,
                min(cot_prix) AS min
            FROM cotation_cot
            WHERE 
                pdt_id = %(pdt_id)s
                AND cot_date >= %(date_debut)s
        ),
        dernier AS (
            -- Dernière cotation connue (pas de filtre période)
            SELECT 
                cot_date,
                cot_prix,
                ROW_NUMBER() OVER (PARTITION BY pdt_id ORDER BY cot_date DESC) AS rn
            FROM cotation_cot
            WHERE 
                pdt_id = %(pdt_id)s
        )
        -- Jointure sans clé : une seule ligne dans chaque CTE
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
    df_cotation['min'] = df_cotation['min'].fillna(df_cotation['cot_prix'])
    df_cotation['max'] = df_cotation['max'].fillna(df_cotation['cot_prix'])

    return df_cotation
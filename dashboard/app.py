import streamlit as st

pages = [
    st.Page("pages/1_📊_KPIs.py", title="KPIs", icon="📊"),
    st.Page("pages/2_📈_Dashboards.py", title="Evolution CA", icon="📈"),
    st.Page("pages/3_✍️_Saisie.py", title="Corrélations", icon="✍️"),
]

pg = st.navigation(pages)
pg.run()
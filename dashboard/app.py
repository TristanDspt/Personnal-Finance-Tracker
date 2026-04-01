import streamlit as st

pages = [
    st.Page("pages/1_📊_KPIs.py", title="KPIs", icon="📊"),
    st.Page("pages/2_📈_Dashboards.py", title="Dashboards", icon="📈"),
    st.Page("pages/3_🚀_Projection.py", title="Projections", icon="🚀"),
    st.Page("pages/4_✍️_Saisie.py", title="Saisie", icon="✍️"),
]

pg = st.navigation(pages)
pg.run()
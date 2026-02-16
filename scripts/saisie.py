import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import config
import time

# --------------------------------------------------------------------------------------------------------------

# SQL
# 1 Connection à la DB
url = f"postgresql://{config.db_params['user']}:{config.db_params['password']}@{config.db_params['host']}:{config.db_params['port']}/{config.db_params['database']}"
engine = create_engine(url)

# 2. Fonction pour charger les données (mise en cache pour la rapidité)
@st.cache_data
def load_data():
    query_ptf = """
        SELECT ptf_id, ptf_nom_banque, ptf_type_enveloppe
        FROM public.portefeuille_ptf
        WHERE ptf_est_actif is TRUE
    """
    df_ptf = pd.read_sql(query_ptf, engine)
    query_pdt = """
        SELECT pdt_id, pdt_nom_produit, pdt_ticker, pdt_cash, ptf_id
        FROM public.produit_financier_pdt
        WHERE pdt_est_actif is TRUE
    """
    df_pdt = pd.read_sql(query_pdt, engine)
    return df_ptf, df_pdt

# 3 Appel de la fonction
df_liste_ptf, df_liste_pdt = load_data()

# --------------------------------------------------------------------------------------------------------------

# CREATION DES LISTE DEROULANTES
# Création de df
df_liste_ptf['affichage'] = df_liste_ptf['ptf_nom_banque'] + " - " + df_liste_ptf['ptf_type_enveloppe']
df_titres = df_liste_ptf[df_liste_ptf['ptf_type_enveloppe'] != 'Livrets'].copy()

# Listes dynamiques
liste_livrets_cash = df_liste_ptf['affichage'].tolist()
liste_livrets_titres = df_titres['affichage'].tolist()

# Listes fixes
liste_types_cash = ["Dépôt", "Retrait", "Ajustement", "Intérêts"]
liste_types_titres = ["Achat", "Vente", "Ajustement", "Abondement", "Dividende"]

# --------------------------------------------------------------------------------------------------------------

# CONFIGURATION STREAMLIT
st.set_page_config(layout="wide")

# BLOC TITRE
st.markdown("<h1 style='text-align: center;'>🏛️ Personnal Finance Tracker 🏛️</h1>", unsafe_allow_html=True)
st.write("")
st.write("#### ✍️ Saisie manuelle")
st.divider() # Un petit trait pour séparer proprement

# CHOIX DU TYPE
choix_global = st.sidebar.radio("Catégorie", ["💸 Flux Cash", "📈 Titres"])

# CASH
if choix_global == "💸 Flux Cash":

    # Ligne 1
    col1, col2, col3 = st.columns([0.5, 2, 0.5])
    with col2:
        choix_livret = st.selectbox("Livret", liste_livrets_cash)
        # --- LOGIQUE BACKGROUND ---
        # 1. On trouve l'ID du portefeuille
        id_ptf_sel = df_liste_ptf[df_liste_ptf['affichage'] == choix_livret]['ptf_id'].values[0]
        
        # 2. On trouve le produit Cash associé
        mask_cash = (df_liste_pdt['ptf_id'] == id_ptf_sel) & (df_liste_pdt['pdt_cash'] == True)
        df_temp = df_liste_pdt[mask_cash]

        if not df_temp.empty:
            id_pdt_final = df_temp['pdt_id'].values[0]
        else:
            # SI PAS DE CASH (PEE, etc.), on prend le premier produit trouvé pour ce livret
            # On s'en fiche, c'est juste pour stocker le montant de l'ajustement/frais
            id_pdt_final = df_liste_pdt[df_liste_pdt['ptf_id'] == id_ptf_sel]['pdt_id'].values[0]

    # Ligne 2
    col4, col5, col6 = st.columns(3)
    with col4:
        date_cash = st.date_input("Date de l'opération")
    with col5:
        montant = st.number_input("Montant")
    with col6:
        choix_cash = st.selectbox("Type", liste_types_cash)

# ACTIONS        
elif choix_global == "📈 Titres":

    # Ligne 1
    col1, col2, col3 = st.columns(3)
    with col1:
        choix_placement = st.selectbox("Livret", liste_livrets_titres)
        id_ptf_sel = df_titres[df_titres['affichage'] == choix_placement]['ptf_id'].values[0]
        
    with col2:
        mask = (df_liste_pdt['ptf_id'] == id_ptf_sel) & (df_liste_pdt['pdt_cash'] == False)
        titres_dispo = df_liste_pdt[mask]
        choix_action = st.selectbox("Placement", titres_dispo['pdt_nom_produit'].tolist())
        
        # On récupère l'id 
        id_pdt_final = titres_dispo[titres_dispo['pdt_nom_produit'] == choix_action]['pdt_id'].values[0]
        
    with col3:
        choix_titre = st.selectbox("Type", liste_types_titres)

    # Ligne 2
    col4, col5, col6 = st.columns(3)
    with col4:
        date_titre = st.date_input("Date de l'opération")
    with col5:
        quantite = st.number_input("Nombre de parts", step=0.000001, format="%.6f")
    with col6:
        prix = st.number_input("Prix de la part", step=0.0001, format="%.4f")

# --------------------------------------------------------------------------------------------------------------

# AJOUT EN BASE

# POP UP DE CONFIRMATION
@st.dialog("Confirmer l'opération")
def confirmer_operation(p_id, p_date, p_qte, p_frais, p_type, p_prix, p_categorie):
    # Gestion de la syntaxe "réelle vs DB"
    if p_type == "Dépôt":
        type_propre = "APPORT"
    elif p_type == "Intérêts":
        type_propre = "INTERET"
    else:
        type_propre = str(p_type).upper()
    # Gestion des ventes / retrait à passer en négatif
    if p_type in ["Vente", "Retrait"]:
        p_qte = -abs(p_qte)
    else:
        p_qte = abs(p_qte)

    # On adapte l'affichage selon si c'est du Cash ou des Actions
    if p_categorie == "💸 Flux Cash":
        # Affichage pour le CASH
        st.write(f"## 💸 Enregistrer un **{p_type}**")
        st.info(f"Montant : **{p_qte}€**")
        st.write(f"### 🏛️ {choix_livret}")
    else:
        # Affichage pour les ACTIONS
        st.write(f"## 📈 Enregistrer un **{p_type}**")
        col1, col2 = st.columns(2)
        col1.metric("Parts", f"{p_qte:.6f}")
        col2.metric("Prix", f"{p_prix:.4f}€")
        col3, col4 = st.columns(2)
        col3.metric("Montant Total", f"{p_qte * p_prix:.2f}€")
        col4.metric("Frais de courtage", f"{p_frais:.2f}€")
        st.write(f"### 🏛️ {choix_action}")

    st.write(f"📅 *Date : {p_date}*")
    st.divider()

    if st.button("Valider ✅", use_container_width=True, type='primary'):
        # On crée la requête SQL
        requete = f"""
            INSERT INTO public.mouvement_mvt 
                (pdt_id, mvt_date, mvt_nb_parts, mvt_frais, mvt_type_mouvement, mvt_prix)
            VALUES 
                ({p_id}, '{p_date}', {p_qte}, {p_frais}, '{type_propre}', {p_prix})
        """
        # On l'exécute direct
        with engine.begin() as conn:
            conn.execute(text(requete))

        st.cache_data.clear()  
        st.success("🚀 Données envoyées !")
        time.sleep(1)
        
        st.rerun()

st.divider()

_, col_btn, _ = st.columns(3)
with col_btn:
    if st.button("Enregistrer l'opération 💾", use_container_width=True):
        # ETAPE A : On prépare les données à afficher dans le popup
        if choix_global == "💸 Flux Cash":
            # Rappel : Pour le cash, on dit que Prix = 1 et Parts = Montant
            confirmer_operation(id_pdt_final, date_cash, montant, 0, choix_cash, 1, choix_global)
        
        elif choix_global == "📈 Titres":
            # Calcul des frais rapide
            banque = df_liste_ptf[df_liste_ptf['ptf_id'] == id_ptf_sel]['ptf_nom_banque'].values[0]
            frais = min((prix * quantite) * 0.005, 1.99) if banque == 'BoursoBank' else 0

            # ETAPE B : On appelle la fonction
            confirmer_operation(id_pdt_final, date_titre, quantite, frais, choix_titre, prix, choix_global)

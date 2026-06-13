import streamlit as st
import pandas as pd
from sqlalchemy import text
import subprocess
import components.database as db
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# --------------------------------------------------------------------------------------------------------------

# 0. CONFIGURATION PAGE
st.set_page_config(page_title="Saisie", page_icon="✍️", layout="wide")

# SQL
# 1 Connection à la DB
engine = db.get_engine()

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
df_pdt_cash = df_liste_pdt[df_liste_pdt['pdt_cash'] == True].copy()
df_pdt_cash = df_pdt_cash.merge(df_liste_ptf[['ptf_id', 'ptf_nom_banque']], on='ptf_id')
df_pdt_cash['affichage_cash'] = df_pdt_cash['ptf_nom_banque'] + " - " + df_pdt_cash['pdt_nom_produit']

df_actions = df_liste_ptf[df_liste_ptf['ptf_type_enveloppe'] != 'Livrets'].copy()
df_actions['affichage_actions'] = df_actions['ptf_nom_banque'] + " - " + df_actions['ptf_type_enveloppe']

# Listes dynamiques
liste_livrets_cash = df_pdt_cash['affichage_cash'].tolist()
liste_livrets_titres = df_actions['affichage_actions'].tolist()

# Listes fixes
liste_types_cash = ["Dépôt", "Retrait", "Ajustement", "Intérêts"]
liste_types_titres = ["Achat", "Vente", "Ajustement", "Abondement", "Dividende"]

# --------------------------------------------------------------------------------------------------------------

# BLOC TITRE
#st.markdown("<h1 style='text-align: center; margin-bottom: 40px;'>🏛️ Personnal Finance Tracker 🏛️</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>✍️ Saisie</h2>", unsafe_allow_html=True)
st.divider() # Un petit trait pour séparer proprement

# MENU
with st.sidebar:
    st.title("⚙️ Menu")

    choix_global = st.sidebar.radio("Choix", ["💸 Flux Cash", "📈 Titres"], label_visibility="collapsed")

    st.divider()

    # Bouton de mise à jour manuelle des fonds PEE (lance update_pee.py en subprocess)
    if st.button("🔄 MAJ PEE"):
        result = subprocess.run(
            [st.secrets["venv_python"], r"scripts\update_pee.py"],
            capture_output=True, text=True
        )
        st.cache_data.clear()
        if result.stderr:
            st.error("⚠️ Erreur !")
            st.text(result.stderr)
        elif "non trouvé" in result.stdout:
            st.warning("⚠️ Fichiers absents...")
            st.text(result.stdout)
        else:
            st.success("🚀 Données envoyées !")
            st.text(result.stdout)
        time.sleep(8)
        st.rerun()
    st.caption("⚠️ Télécharger CSV avant MAJ")

# CASH
if choix_global == "💸 Flux Cash":

    # Ligne 1
    col1, col2, col3 = st.columns([0.5, 2, 0.5])
    with col2:
        choix_livret = st.selectbox("Livret", liste_livrets_cash)
        # On récupère tout d'un coup
        selection = df_pdt_cash[df_pdt_cash['affichage_cash'] == choix_livret].iloc[0]
        pdt_id = selection['pdt_id'] 
        ptf_id = selection['ptf_id'] # Utile pour les frais/banque plus tard
        pdt_nom_produit = selection['pdt_nom_produit'] # Pour l'affichage popup

    # Ligne 2
    col4, col5, col6 = st.columns(3)
    with col4:
        mvt_date = st.date_input("Date de l'opération")
    with col5:
        saisie_parts = st.text_input("Montant", value="0", help="Saisir un montant positif, le signe est géré automatiquement")
        try:
            mvt_nb_parts = float(saisie_parts.replace(',', '.'))
        except ValueError:
            st.error("⚠️ Montant invalide")
            mvt_nb_parts = None
    with col6:
        mvt_type_mouvement = st.selectbox("Type", liste_types_cash)

    # Valeurs fixes pour le cash
    mvt_prix = 1
    mvt_frais = 0

# ACTIONS        
elif choix_global == "📈 Titres":

    # Ligne 1
    col1, col2, col3 = st.columns(3)
    col1, col2, col3 = st.columns(3)
    with col1:
        choix_enveloppe = st.selectbox("Livret", liste_livrets_titres)
        ptf_id = df_actions[df_actions['affichage_actions'] == choix_enveloppe]['ptf_id'].values[0]
        
    with col2:
        df_pdt_du_ptf = df_liste_pdt[(df_liste_pdt['ptf_id'] == ptf_id) & (df_liste_pdt['pdt_cash'] == False)]
        pdt_nom_produit = st.selectbox("Placement", df_pdt_du_ptf['pdt_nom_produit'].tolist())
        # On récupère l'id 
        pdt_id = df_pdt_du_ptf[df_pdt_du_ptf['pdt_nom_produit'] == pdt_nom_produit]['pdt_id'].values[0]
        
    with col3:
        mvt_type_mouvement = st.selectbox("Type", liste_types_titres)

    # Ligne 2
    col4, col5, col6 , col7 = st.columns(4)
    with col4:
        mvt_date = st.date_input("Date de l'opération")
    with col5:
        saisie_parts = st.text_input("Nombre de parts", value="0", help="Saisir une valeur positive — le signe est appliqué automatiquement")
        try:
            mvt_nb_parts = float(saisie_parts.replace(',', '.'))
        except ValueError:
            st.error("⚠️ Nombre de parts invalide")
            mvt_nb_parts = None
    with col6:
        saisie_prix = st.text_input("Prix de la part", value="0")
        try:
            mvt_prix = float(saisie_prix.replace(',', '.'))
        except ValueError:
            st.error("⚠️ Prix invalide")
            mvt_prix = None
    with col7:
        saisie_frais = st.text_input("Frais", value="0")
        try:
            mvt_frais = float(saisie_frais.replace(',', '.'))
        except ValueError:
            st.error("⚠️ Frais invalide")
            mvt_frais = None

# --------------------------------------------------------------------------------------------------------------

# AJOUT EN BASE

# POP UP DE CONFIRMATION
@st.dialog("Confirmer l'opération") # crée la popup
def confirmer_operation(p_id, p_date, p_qte, p_frais, p_type, p_prix, p_cat, p_nom_pdt, p_id_cash=None):
    # Gestion de la syntaxe "réelle vs DB"
    if p_type == "Dépôt":
        type_txt = "APPORT"
    elif p_type == "Intérêts":
        type_txt = "INTERET"
    else:
        type_txt = str(p_type).upper()
    # Gestion des ventes / retrait à passer en négatif
    if p_type in ["Vente", "Retrait"]:
        # On force le négatif quoi qu'il arrive
        type_pos = -abs(p_qte)
    elif p_type in ["Ajustement"]:
        # On garde le signe saisi par l'utilisateur (permet de corriger + ou -)
        type_pos = p_qte
    else:
        # Pour les achats/dépôts, on force le positif
        type_pos = abs(p_qte)

    # On adapte l'affichage selon si c'est du Cash ou des Actions
    if p_cat == "💸 Flux Cash":
        # Affichage pour le CASH
        st.write(f"## 💸 Enregistrer un **{p_type}**")
        st.info(f"Montant : **{p_qte}€**")
        st.write(f"### 🏛️ {p_nom_pdt}")
    else:
        # Affichage pour les ACTIONS
        st.write(f"## 📈 Enregistrer un **{p_type}**")
        col1, col2 = st.columns(2)
        col1.metric("Parts", f"{p_qte:.6f}")
        col2.metric("Prix", f"{p_prix:.4f}€")
        col3, col4 = st.columns(2)
        col3.metric("Montant Total", f"{p_qte * p_prix:.2f}€")
        col4.metric("Frais de courtage", f"{p_frais:.2f}€")
        st.write(f"### 🏛️ {p_nom_pdt}")

    st.write(f"📅 *Date : {p_date}*")
    st.divider()

    if st.button("Valider ✅", width='stretch', type='primary'):
        # Connection à la DB
        with engine.begin() as conn:
        
            # On crée la requête SQL
            requete_titre = f"""
                INSERT INTO public.mouvement_mvt 
                    (pdt_id, mvt_date, mvt_nb_parts, mvt_frais, mvt_type_mouvement, mvt_prix)
                VALUES 
                    ({p_id}, '{p_date}', {type_pos}, {p_frais}, '{type_txt}', {p_prix})
            """
            conn.execute(text(requete_titre))

            # Cas spécifique pour les achat vente passage de l'argent de ou vers la poche cash
            if p_id_cash:
                # 1. Calcul du montant net (le cash qui bouge réellement)
                montant_mouvement_titre = (p_qte * p_prix)
                
                if p_type == "Achat":
                    montant_cash = -(montant_mouvement_titre + p_frais)
                    type_cash = "RETRAIT_MIROIR"
                elif p_type == "Vente":
                    montant_cash = (montant_mouvement_titre - p_frais)
                    type_cash = "APPORT"
                else:
                    # Pour Ajustement ou Dividende, à toi de voir la logique
                    montant_cash = montant_mouvement_titre 
                    type_cash = "AJUSTEMENT"

                # 2. Requête miroir
                requete_cash = f"""
                    INSERT INTO public.mouvement_mvt 
                        (pdt_id, mvt_date, mvt_nb_parts, mvt_frais, mvt_type_mouvement, mvt_prix)
                    VALUES 
                        ({p_id_cash}, '{p_date}', {montant_cash}, 0, '{type_cash}', 1)
                """
                conn.execute(text(requete_cash)) 

        st.cache_data.clear()
        st.success("🚀 Données envoyées !")
        time.sleep(1)
        st.rerun()

st.divider()

# BOUTON ET ACTIVATION

_, col_btn, _ = st.columns(3)
with col_btn:
    if st.button("Enregistrer l'opération 💾", width='stretch'):
        # 1. Initialisation par défaut (pour le Cash)
        id_cash_miroir = None
        
        # 2. Logique spécifique aux Actions (Miroir + Frais)
        if choix_global == "📈 Titres":
            # On trouve l'ID de la poche cash
            id_cash_miroir = df_liste_pdt[(df_liste_pdt['ptf_id'] == ptf_id) & (df_liste_pdt['pdt_cash'] == True)]['pdt_id'].values[0]
            
            # On récupère le nom de la banque pour calculer les frais
            banque = df_liste_ptf[df_liste_ptf['ptf_id'] == ptf_id]['ptf_nom_banque'].values[0]

        # 3. Appel de la fonction (mvt_frais sera soit 0 (Cash), soit le calcul ci-dessus)
        confirmer_operation(
            pdt_id, 
            mvt_date, 
            mvt_nb_parts, 
            mvt_frais, 
            mvt_type_mouvement, 
            mvt_prix, 
            choix_global, 
            pdt_nom_produit, 
            id_cash_miroir
        )

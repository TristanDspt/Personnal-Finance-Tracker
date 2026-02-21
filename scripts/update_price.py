import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
import config
import logging
from datetime import datetime
import sys

# Configure le journal (va créer un fichier bourse_log.txt)
logging.basicConfig(
    filename=config.chemin_log,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

logging.debug("Démarrage de la mise à jour automatique.")  # info sur le lancement du script

# 1. Connection à la DB
url = f"postgresql://{config.db_params['user']}:{config.db_params['password']}@{config.db_params['host']}:{config.db_params['port']}/{config.db_params['database']}"
engine = create_engine(url)

logging.debug("Connexion établie !")  # pour savoir s'il se connecte bien à la base

# 2. Récupérer uniquement les produits "boursiers"
query = """
    SELECT pdt_id, pdt_ticker
    FROM public.produit_financier_pdt
    WHERE pdt_ticker is not null
"""
df_liste_ticker = pd.read_sql(query, engine)

# 3. On demande à la base la date la plus récente qu'on possède
query_last_date = "SELECT MAX(cot_date_prix) FROM public.cotation_cot"  # SELECT MAX envoi NONE si la table est vide
last_date_in_db = pd.read_sql(query_last_date, engine).iloc[0, 0]

# 4. On définit la date de début pour Yahoo Finance
if last_date_in_db is None:
    date_debut = "2024-01-01"
    logging.debug("Base vide, on récupère tout depuis 2024.")  # debug 1er import
else:
    # On ajoute +1 jour pour ne pas re-télécharger le dernier jour déjà présent
    date_debut = last_date_in_db + pd.Timedelta(days=1)
    if date_debut > datetime.now().date():
        logging.info(f"Déjà à jour (Dernière date : {last_date_in_db}).")  # si le script a déjà été lancé ce jour
        logging.info("-" * 50)  # pour améliorer la lisibilité des logs
        engine.dispose()
        sys.exit()
    logging.info(f"Dernière donnée en base : {last_date_in_db}. Ajout à partir du {date_debut}")  # info sur l'action du script

# 5. LA BOUCLE
for index, row in df_liste_ticker.iterrows():
    ticker = row["pdt_ticker"]
    pdt_id = row["pdt_id"]

    try:
        df_temp = yf.download(ticker, start=date_debut, multi_level_index=False)

        if not df_temp.empty:
            df_temp = df_temp["Close"].reset_index()
            df_temp.columns = ["cot_date_prix", "cot_prix_unitaire"]
            df_temp["pdt_id"] = pdt_id
            df_temp["cot_date_prix"] = pd.to_datetime(df_temp["cot_date_prix"]).dt.date

            # On injecte uniquement les nouvelles lignes
            df_temp.to_sql("cotation_cot", engine, if_exists="append", index=False)
            logging.info(f"Ajout de {len(df_temp)} nouvelles lignes pour {ticker}")  # info sur le bon déroulement de l'import
        else:
            logging.info(f"Déjà à jour pour {ticker}.")  # info sur le bon déroulement de l'import
    except Exception as e:
        logging.error(f"Erreur sur {ticker} : {e}")  # info sur le type d'erreur rencontrée
engine.dispose()  # ferme la connection SQL pour liberer de la place en memoire
logging.debug("Connexion fermée. Traitement terminé !")  # info sur la fermeture du script
logging.info("-" * 50)  # pour améliorer la lisibilité des logs

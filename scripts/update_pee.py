import pandas as pd
from sqlalchemy import create_engine
import config
from datetime import datetime
import os

# 1. Connection à la DB
url = f"postgresql://{config.db_params['user']}:{config.db_params['password']}@{config.db_params['host']}:{config.db_params['port']}/{config.db_params['database']}"
engine = create_engine(url)

# 2. Parametres de nettoyage des fichiers
# On définit les modèles (templates)
params_stef = {
    "sep": ";",
    "header": 0,
    "names": ["cot_date", "cot_prix"],
    "usecols": [0, 1],
    "parse_dates": ["cot_date"],
    "dayfirst": True,
}

params_cic = {
    "skiprows": 2,
    "names": ["cot_date", "cot_prix"],
    "usecols": [0, 1],
    "parse_dates": ["cot_date"],
    "date_format": "%d/%m/%Y",
    "decimal": ",",
}

# On les utilise dans la config
config_auto = {
    3: {
        "nom": "STEF",
        "keyword": "HistoriqueValeurPart",
        "type": "csv",
        "params": params_stef,
    },
    4: {
        "nom": "CiC Obligation",
        "keyword": "FCPE 1525",
        "type": "excel",
        "params": params_cic,
    },
    5: {
        "nom": "CiC Equilibre",
        "keyword": "FCPE 1630",
        "type": "excel",
        "params": params_cic,
    },
    6: {
        "nom": "CiC Stratégie",
        "keyword": "FCPE 4604",
        "type": "excel",
        "params": params_cic,
    },
}

dossier = config.dossier_dl
tout_les_fichiers = os.listdir(
    dossier
)  # Crée une liste de textes avec les noms des fichiers

# 3 LA BOUCLE
for pdt_id, param in config_auto.items():
    chemin = None

    # --- ETAPE A : RECHERCHE ---
    for nom_fichier in tout_les_fichiers:
        if param["keyword"] in nom_fichier:
            chemin = os.path.join(dossier, nom_fichier)
            break

    # --- ETAPE B : LECTURE ---
    if chemin:
        if param["type"] == "csv":
            df = pd.read_csv(chemin, **param["params"])
        else:
            df = pd.read_excel(chemin, **param["params"])

        df["pdt_id"] = pdt_id  # On ajoute l'ID pour que la base sache de quel livret on parle
    else:
        print(f"Fichier {param['nom']} non trouvé dans le dossier.")
        continue  # On passe au produit suivant si pas de fichier

    # --- ETAPE C : COMPARAISON ET ENVOI ---
    # 1. On récupère la date max en SQL pour ce pdt_id spécifique
    date_fichier = df["cot_date"].max()
    query = f"SELECT MAX(cot_date) FROM cotation_cot WHERE pdt_id = {pdt_id}"
    with engine.connect() as conn:
        res = pd.read_sql(query, conn).iloc[0, 0] # On stocke le résultat brut (Pandas n'aime pas le type datetime de SQL)
        date_db = pd.to_datetime(res) if res is not None else None # On convertit pour que Pandas soit content

        # 2. On traite le fichier uniquement si on trouve des dates plus récentes
        if date_db is None or date_fichier > date_db:
            if date_db is None:
                df_neuf = df
            else:
                df_neuf = df[df["cot_date"] > date_db]

            # On n'envoie que si le filtre n'est pas vide
            if not df_neuf.empty:
                df_neuf.to_sql("cotation_cot", engine, if_exists="append", index=False)
                print(f"Mis à jour : {len(df_neuf)} lignes ajoutées pour {param['nom']}")
        else:
            print(f"{param['nom']} est déjà à jour.")
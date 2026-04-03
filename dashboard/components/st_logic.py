import pandas as pd
from pyxirr import xirr

# =============================================================================
# st_logic.py
# Contient toute la logique métier de l'application (calculs, transformations).
# Aucun code Streamlit ici — uniquement des fonctions Python pures.
# =============================================================================


# --- RÉFÉRENCE : IDs Portefeuilles & Produits ---
# PTF: 1 : PEA | 2 : CTO | 3 : STEF | 4 CiC | 6 : Livrets
# PDT: 1 : S&P500 | 2 : Gold | 3 : Action STEF | 4 : Oblig CiC | 5 : Equi CiC | 6 : Strat CiC | 7 : Cash Bourso | 8 : Cash TR | 10 : Livret A | 11 : LEP


PTF_TO_PDT = {
    1: [1, 7],
    2: [2, 8],
    3: [3],
    4: [4, 5, 6, 9],
    6: [10, 11],
}


def get_patrimoine_total(df):
    """
    Calcule la valeur totale du patrimoine (cash + titres).

    Args:
        df (DataFrame): view_global_portefeuille (ou sous-ensemble filtré)

    Returns:
        float: somme de capital_actuel sur tous les produits
    """
    capital = df['capital_actuel'].sum()
    return capital


def get_perf_marches(df):
    """
    Calcule la performance globale des marchés (hors produits cash).
    Inclut l'abondement dans la base de calcul du pourcentage.

    Args:
        df (DataFrame): view_global_portefeuille (ou sous-ensemble filtré)

    Returns:
        dict: {"euro": float, "pct": float}
    """
    # On exclut le cash (livrets, poches broker) — ils ne font pas de perf boursière
    df_bourse = df.query("pdt_cash == False")
    profit_euro = df_bourse['profit_euro'].sum()

    # Base de calcul : effort perso + abondement employeur
    investi_bourse = df_bourse['capital_investi'].sum()
    abondement = df_bourse['abondement_recu'].sum()
    total_investi = investi_bourse + abondement

    # Garde-fou pour éviter une division par zéro
    profit_pct = (profit_euro / total_investi * 100) if total_investi > 0 else 0

    return {"euro": profit_euro, "pct": profit_pct}


def get_poids_enveloppes(df):
    """
    Calcule le poids de chaque enveloppe dans le patrimoine total (en %).

    Args:
        df (DataFrame): view_global_portefeuille

    Returns:
        dict: {"etf": float, "pee": float, "livret": float}
    """
    # IDs des portefeuilles par catégorie
    etf_ids = [1, 2]
    pee_ids = [3, 4]
    livret_ids = [6]

    # Appel de la fonction dédiée pour éviter de recalculer le capital
    capital = get_patrimoine_total(df)

    if capital > 0:
        # Poids = capital de l'enveloppe / capital total * 100
        poids_etf = df.query("ptf_id in @etf_ids and pdt_est_actif == True")['capital_actuel'].sum() / capital * 100
        poids_pee = df.query("ptf_id in @pee_ids and pdt_est_actif == True")['capital_actuel'].sum() / capital * 100
        poids_livret = df.query("ptf_id in @livret_ids and pdt_est_actif == True")['capital_actuel'].sum() / capital * 100
    else:
        # Sécurité si le patrimoine est vide (DB vide, premier lancement)
        poids_etf = poids_pee = poids_livret = 0

    return {"etf": poids_etf, "pee": poids_pee, "livret": poids_livret}


def get_nb_mois(duree):
    """
    Convertit le label du slider en nombre de mois.
    Retourne 0 pour le cas "Début Mois" (non présent dans le mapping).

    Args:
        duree (str): valeur du slider (ex: "6 Mois", "1 An", "Max", "Début Mois")

    Returns:
        int: nombre de mois correspondant, 0 si cas spécial
    """
    mapping_duree = {
        "1 Mois": 1,
        "3 Mois": 3,
        "6 Mois": 6,
        "1 An": 12,
        "3 Ans": 36,
        "5 Ans": 60,
        "Max": 600
    }

    # "Début Mois" n'est pas dans le mapping → retourne 0
    if duree in mapping_duree:
        nb_mois = mapping_duree[duree]
    else:
        nb_mois = 0

    return nb_mois


def get_date_debut(duree):
    """
    Calcule la date de début de la période sélectionnée via le slider.
    Cas "Début Mois" : retourne le 1er du mois en cours.
    Autres cas : retourne aujourd'hui - nb_mois, normalisé à minuit.

    ⚠️ Le normalize() est essentiel pour éviter les décalages d'un jour
    liés à l'heure exacte d'exécution lors des comparaisons avec df_histo.

    Args:
        duree (str): valeur du slider

    Returns:
        pd.Timestamp: date de début de la période (minuit)
    """
    nb_mois = get_nb_mois(duree)
    debut_mois_actuel = pd.Timestamp.now().replace(day=1)

    if nb_mois > 0:
        # Cas normal : on recule de nb_mois à partir d'aujourd'hui
        date_debut = pd.Timestamp.now() - pd.DateOffset(months=nb_mois)
        # Cas "15 jours" : on recule de 15j à partir d'aujourd'hui
    elif duree == "15 Jours":
        date_debut = pd.Timestamp.now() - pd.DateOffset(days=15)
    else:
        # Cas "Début Mois" : on repart du 1er du mois en cours
        date_debut = debut_mois_actuel

    # Normalisation à minuit — évite les décalages lors des comparaisons avec les dates SQL
    date_debut = pd.Timestamp(date_debut).normalize()

    return date_debut


def get_df_periode(df_histo, date_debut):
    """
    Filtre df_histo sur la période sélectionnée.

    Args:
        df_histo (DataFrame): view_historique_portefeuille
        date_debut (pd.Timestamp): date de début calculée par get_date_debut()

    Returns:
        DataFrame: df_histo filtré >= date_debut
    """
    # Conversion sécurisée en datetime (au cas où l'import SQL ne l'a pas fait)
    df_histo['jour'] = pd.to_datetime(df_histo['jour'])
    df_periode = df_histo[df_histo['jour'] >= date_debut]
    return df_periode


def get_perf_etf_periode(df_histo, df_periode, date_debut, duree):
    """
    Calcule la performance des ETF (PEA + CTO) sur la période sélectionnée.
    Gère les cas spéciaux "Début Mois" et "Max".

    ⚠️ Si snap_debut['jour'] > date_debut, cela signifie que la période demandée
    remonte avant le premier mouvement — on traite alors comme "Max" (profit total).

    Args:
        df_histo (DataFrame): view_historique_portefeuille (complet, non filtré)
        df_periode (DataFrame): df_histo filtré sur la période
        date_debut (pd.Timestamp): date de début calculée par get_date_debut()
        duree (str): valeur du slider

    Returns:
        dict: {"euro": float, "pct": float}
    """
    # Utilisé pour le cas "Début Mois" : on cherche le snapshot avant le 1er du mois
    debut_mois_actuel = pd.Timestamp.now().replace(day=1)

    # Agrégation journalière des deux ETF sur la période
    df_etf_periode = (df_periode.query("ptf_id in [1, 2]")
                        .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi']]
                        .sum()
                        .reset_index()
                        .query("capital_investi > 1")  # filtre les jours sans position réelle
                        .sort_values('jour'))

    if not df_etf_periode.empty:
        snap_fin = df_etf_periode.iloc[-1]  # dernier jour de la période

        if duree == "Début Mois":
            # On cherche le dernier snapshot AVANT le 1er du mois dans l'historique complet
            snap_debut = (df_histo.query("ptf_id in [1, 2] and jour < @debut_mois_actuel")
                            .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi']]
                            .sum()
                            .reset_index()
                            .query("capital_investi > 1")
                            .sort_values('jour')
                            .iloc[-1])
        else:
            snap_debut = df_etf_periode.iloc[0]  # premier jour de la période filtrée

        # Si snap_debut est postérieur à date_debut → la période remonte avant le 1er mouvement
        # On traite comme "Max" : profit total depuis le début
        if duree == "Max" or snap_debut['jour'] > date_debut:
            perf_etf_periode_euro = snap_fin['profit_euro']
        else:
            # Variation de profit entre début et fin de période
            perf_etf_periode_euro = snap_fin['profit_euro'] - snap_debut['profit_euro']

        perf_etf_periode_pct = (perf_etf_periode_euro / snap_fin['capital_investi'] * 100) if snap_fin['capital_investi'] > 0 else 0
    else:
        # Pas de données sur la période
        perf_etf_periode_euro, perf_etf_periode_pct = 0, 0

    return {"euro": perf_etf_periode_euro, "pct": perf_etf_periode_pct}


def get_perf_ptf_periode(df_histo, df_periode, duree, date_debut, mapping):
    """
    Calcule la performance de chaque portefeuille sur la période sélectionnée.
    Gère les cas spéciaux "Début Mois" et "Max".

    ⚠️ Si snap_debut['jour'] > date_debut, cela signifie que la période demandée
    remonte avant le premier mouvement — on traite alors comme "Max" (profit total).

    Args:
        df_histo (DataFrame): view_historique_portefeuille (complet, non filtré)
        df_periode (DataFrame): df_histo filtré sur la période
        duree (str): valeur du slider
        date_debut (pd.Timestamp): date de début calculée par get_date_debut()
        mapping (dict): {ptf_id: nom_affiche} — ex: {1: "PEA", 2: "CTO"}

    Returns:
        dict: {"PEA": {"euro": float, "pct": float}, "CTO": {...}, ...}
    """
    debut_mois_actuel = pd.Timestamp.now().replace(day=1)

    portefeuilles = mapping
    perf = {}

    for ptf_id, ptf_nom in portefeuilles.items():
        # Agrégation journalière pour ce portefeuille sur la période
        df_temp = (df_periode.query("ptf_id == @ptf_id")
                    .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                    .sum()
                    .reset_index()
                    .query("capital_investi + abondement_recu > 1")
                    .sort_values('jour'))

        if not df_temp.empty:
            snap_fin = df_temp.iloc[-1]

            if duree == "Début Mois":
                # Snapshot avant le 1er du mois dans l'historique complet
                snap_debut = (df_histo.query("ptf_id == @ptf_id and jour < @debut_mois_actuel")
                                .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                                .sum()
                                .reset_index()
                                .query("capital_investi + abondement_recu > 1")
                                .sort_values('jour')
                                .iloc[-1])
            else:
                snap_debut = df_temp.iloc[0]

            # Si snap_debut est postérieur à date_debut → la période remonte avant le 1er mouvement
            # On traite comme "Max" : profit total depuis le début
            if duree == "Max" or snap_debut['jour'] > date_debut:
                euro = snap_fin['profit_euro']
            else:
                euro = snap_fin['profit_euro'] - snap_debut['profit_euro']

            # Base = effort perso + abondement pour un calcul de ROI correct
            base = snap_fin['capital_investi'] + snap_fin['abondement_recu']
            pct = (euro / base * 100) if base > 0 else 0
        else:
            euro, pct = 0, 0

        perf[ptf_nom] = {"euro": euro, "pct": pct}

    return perf


def get_tableau_mensuel_ptf(df_histo, df_apports, duree, mapping_ptf):
    """
    Construit le tableau mensuel du journal de bord.
    Retourne deux DataFrames :
    - df_tableau : version nettoyée pour l'affichage (tri décroissant, 1er mois viré)
    - df_tableau_buffer : version avec le mois de buffer nécessaire au calcul du graph
                            (trié croissant, 1er mois conservé pour le shift(1) de perf_graph)

    Args:
        df_histo (DataFrame): view_historique_portefeuille
        df_apports (DataFrame): view_apports_mensuels
        duree (str): valeur du slider
        mapping_ptf (dict): {ptf_id: nom_enveloppe} — ex: {1: "ETF", 2: "ETF", 3: "STEF"}
                        Les valeurs identiques permettent de regrouper plusieurs ptf sous une même colonne

    Returns:
        tuple: (df_tableau, df_tableau_buffer)
    """
    nb_mois = get_nb_mois(duree)
    debut_mois_actuel = pd.Timestamp.now().replace(day=1)
    # Date de départ du tableau — inclut 1 mois de buffer pour permettre le calcul des évolutions m-1
    date_debut_tableau = debut_mois_actuel - pd.DateOffset(months=nb_mois)

    # Copies pour ne pas modifier les DataFrames originaux
    df_mensuel = df_histo.copy()
    df_apports = df_apports.copy()

    # Ajout de la colonne enveloppe pour le regroupement
    df_mensuel['Enveloppe'] = df_mensuel['ptf_id'].map(mapping_ptf)

    # Agrégation journalière par enveloppe
    df_journalier = (df_mensuel.groupby(['Enveloppe', 'jour'])
                    .agg({'capital_actuel': 'sum', 'capital_investi': 'sum'})
                    .reset_index())

    # Pivot mensuel : dernière valeur du mois par enveloppe
    df_pivot = (df_journalier.groupby(['Enveloppe', pd.Grouper(key='jour', freq='ME')])
                .agg({'capital_actuel': 'last', 'capital_investi': 'last'})
                .unstack(level=0))

    df_tableau = df_pivot['capital_actuel'].copy()

    # --- Calcul des colonnes de performance ---
    df_tableau['Total'] = df_tableau.sum(axis=1)
    df_tableau['Evo Patrimoine'] = df_tableau['Total'].diff()
    df_tableau['Evo (%)'] = (df_tableau['Evo Patrimoine'] / df_tableau['Total'].shift(1)) * 100

    # Alignement des apports sur l'index mensuel du tableau
    # La vue SQL retourne des dates avec timezone → on la vire proprement avant le reindex
    df_apports['mois'] = df_apports['mois'].apply(lambda x: pd.Timestamp(x).replace(tzinfo=None).normalize())
    df_apports = df_apports.set_index('mois')
    injecte_mois = df_apports['injecte'].reindex(df_tableau.index, fill_value=0)

    # Perf marchés = variation patrimoine - argent injecté ce mois
    df_tableau['Perf Marchés (€)'] = df_tableau['Evo Patrimoine'] - injecte_mois

    # Colonnes glissantes sur 12 mois (activées via toggle dans Home.py)
    df_tableau['Evo 12m (€)'] = df_tableau['Total'] - df_tableau['Total'].shift(12)
    df_tableau['Evo 12m (%)'] = (df_tableau['Evo 12m (€)'] / df_tableau['Total'].shift(12)) * 100

    # --- Nettoyage ---
    # Filtre sur la période sélectionnée
    df_tableau = df_tableau.query("index >= @date_debut_tableau")

    # Ordre d'affichage : enveloppes dynamiques (dédupliquées) + colonnes fixes
    colonnes_ordre = list(dict.fromkeys(mapping_ptf.values())) + [
        'Total', 'Evo Patrimoine', 'Evo (%)', 'Perf Marchés (€)', 'Evo 12m (€)', 'Evo 12m (%)'
        ]

    # On n'affiche une enveloppe que si elle a des données non nulles
    colonnes_enveloppes = set(mapping_ptf.values())
    tableau = []
    for c in colonnes_ordre:
        if c in colonnes_enveloppes:
            if c in df_tableau.columns and df_tableau[c].notna().any() and df_tableau[c].sum() > 0:
                tableau.append(c)
        else:
            if c in df_tableau.columns and df_tableau[c].notna().any():
                tableau.append(c)

    df_tableau = df_tableau[tableau]

    # Buffer pour le graph : trié croissant, conserve le 1er mois
    # (nécessaire pour que get_donnees_graph puisse calculer perf_graph via shift(1))
    df_tableau_buffer = df_tableau.sort_index(ascending=True)

    # Tableau d'affichage : tri décroissant + suppression du 1er mois (artefact du diff())
    if nb_mois > 0:
        df_tableau = df_tableau.iloc[1:].sort_index(ascending=False)
    else:
        df_tableau = df_tableau.sort_index(ascending=False)

    df_tableau.index.name = 'Mois'

    return df_tableau, df_tableau_buffer


def get_donnees_graph(df_tableau_buffer, df_apports, duree):
    """
    Prépare les deux DataFrames nécessaires au graphique principal.
    - df_apports_graph : cumul des apports mensuels, filtré et réindexé sur la période
    - df_capital_graph : capital mensuel + perf, avec le 1er mois viré après calculs

    ⚠️ Reçoit df_tableau_buffer (avec mois de buffer) et non df_tableau (version affichage).
    Le buffer est indispensable pour calculer perf_graph via shift(1) sans perdre le 1er mois affiché.

    Args:
        df_tableau_buffer (DataFrame): résultat de get_tableau_mensuel_ptf()[1] — trié croissant avec buffer
        df_apports (DataFrame): view_apports_mensuels brut (avec colonne 'mois')
        duree (str): valeur du slider

    Returns:
        tuple: (df_apports_graph, df_capital_graph)
    """
    nb_mois = get_nb_mois(duree)
    debut_mois_actuel = pd.Timestamp.now().replace(day=1)
    date_debut_tableau = debut_mois_actuel - pd.DateOffset(months=nb_mois)

    # --- Préparation df_apports_graph ---

    # Tri croissant pour les calculs cumulatifs
    df_tableau_buffer = df_tableau_buffer.sort_index(ascending=True)

    df_apports = df_apports.copy()
    df_apports = df_apports.set_index('mois')

    # La vue SQL retourne des dates propres (::date) — conversion simple sans timezone
    df_apports.index = pd.to_datetime(df_apports.index)

    # Cumul des apports depuis le début (toute l'histoire, pas juste la période)
    df_apports['cumsum'] = df_apports['injecte'].cumsum()

    # Remplissage des mois manquants (mois sans mouvement) par forward fill
    # Nécessaire pour avoir une courbe continue même les mois sans apport
    index_complet = pd.date_range(
        start=pd.Timestamp(df_apports.index.min()).tz_localize(None),
        end=pd.Timestamp.today() + pd.offsets.MonthEnd(0),
        freq='ME'
    )
    df_apports = df_apports.reindex(index_complet).ffill()

    # Filtre sur la période + réindexation en début de mois pour aligner avec df_capital_graph
    df_apports_graph = df_apports[df_apports.index >= date_debut_tableau]
    df_apports_graph.index = df_apports_graph.index.to_period('M').to_timestamp()

    # Suppression du 1er mois : il sert de référence pour le diff() mais ne doit pas s'afficher
    df_apports_graph = df_apports_graph.iloc[1:]

    # --- Préparation df_capital_graph ---

    df_capital_graph = df_tableau_buffer

    # Perf marchés en % : variation mensuelle du patrimoine / total du mois précédent
    # Le shift(1) utilise le mois de buffer — c'est pour ça qu'on a besoin de df_tableau_buffer
    df_capital_graph['perf_graph'] = (df_capital_graph['Perf Marchés (€)'] / df_capital_graph['Total'].shift(1)) * 100

    # Réindexation en début de mois pour aligner avec df_apports_graph
    df_capital_graph.index = df_capital_graph.index.to_period('M').to_timestamp()

    # Delta = écart entre capital réel et apports cumulés = performance pure des marchés en €
    df_capital_graph['delta'] = df_capital_graph['Total'] - df_apports_graph['cumsum']

    # Suppression du 1er mois (buffer) — il a servi pour le shift(1), on ne l'affiche pas
    df_capital_graph = df_capital_graph.iloc[1:]

    return df_apports_graph, df_capital_graph


def get_injecte_periode(df_histo, df_periode, duree, date_debut, liste_pdt):
    """
    Calcule le capital total injecté sur une liste de produits sur la période sélectionnée.
    Gère les cas spéciaux "Début Mois" et "Max".

    ⚠️ Basé sur capital_investi (cumulatif) — calcule la variation entre snap_debut et snap_fin.
    Si snap_debut['jour'] > date_debut, la période remonte avant le 1er mouvement :
    on traite alors comme "Max" et retourne le capital_investi total.

    Args:
        df_histo (DataFrame): view_historique_portefeuille (complet, non filtré)
        df_periode (DataFrame): df_histo filtré sur la période
        duree (str): valeur du slider
        date_debut (pd.Timestamp): date de début calculée par get_date_debut()
        liste_pdt (list): liste des pdt_id à inclure — ex: [1, 7] pour PEA (ETF + cash)

    Returns:
        float: somme du capital injecté sur les produits listés sur la période
    """
    debut_mois_actuel = pd.Timestamp.now().replace(day=1)

    injecte = 0

    for pdt_id in liste_pdt:
        # Agrégation journalière pour ce produit sur la période
        df_temp = (df_periode.query("pdt_id == @pdt_id")
                    .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                    .sum()
                    .reset_index()
                    .query("capital_investi + abondement_recu > 1")
                    .sort_values('jour'))

        if not df_temp.empty:
            snap_fin = df_temp.iloc[-1]

            if duree == "Début Mois":
                # Snapshot avant le 1er du mois dans l'historique complet
                snap_debut = (df_histo.query("pdt_id == @pdt_id and jour < @debut_mois_actuel")
                                .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                                .sum()
                                .reset_index()
                                .query("capital_investi + abondement_recu > 1")
                                .sort_values('jour')
                                .iloc[-1])
            else:
                snap_debut = df_temp.iloc[0]

            # Si snap_debut est postérieur à date_debut → la période remonte avant le 1er mouvement
            # On traite comme "Max" : capital investi total depuis le début
            if duree == "Max" or snap_debut['jour'] > date_debut:
                injecte += snap_fin['capital_investi']
            else:
                injecte += snap_fin['capital_investi'] - snap_debut['capital_investi']

        else:
            injecte += 0

    return injecte


def get_capital_net(df, liste_pdt):
    """
    Calcule le capital net et la performance après fiscalité sur les plus-values.
    PEA/PEE : 18.6% | CTO : 31.4%
    Si pas de plus-value, retourne le capital actuel brut.

    Args:
        df (DataFrame): view_global_portefeuille
        ptf_id (int): id du portefeuille

    Returns:
        dict: {"net": float, "euro": float, "pct": float}
    """
    taux = {1: 18.6, 2: 31.4, 3: 18.6, 4: 18.6, 5: 18.6, 6: 18.6}
    capital_net = {}
    df = df.copy()

    for pdt_id in liste_pdt:
        df_temp = df.query("pdt_id == @pdt_id and pdt_cash == False and pdt_est_actif == True")
        plus_value = df_temp['profit_euro'].sum()

        # Fiscalité uniquement si plus-value positive
        if plus_value > 0:
            impot = plus_value * taux[pdt_id] / 100
            capital_net[pdt_id] = df_temp['capital_actuel'].sum() - impot
        else:
            capital_net[pdt_id] = df_temp['capital_actuel'].sum()

    return capital_net


def get_tri_ptf(df, engine, liste_ptf):
    """
    Calcule le Taux de Rendement Interne (TRI / XIRR) pour une ou plusieurs enveloppes.

    Reproduit la logique de TRI.PAIEMENTS d'Excel :
    - Flux négatifs : les apports historiques (argent sorti de la poche)
    - Flux positif final : le capital actuel à la date d'aujourd'hui

    Args:
        df (DataFrame)      : view_global_portefeuille (snapshot instantané)
        engine              : connexion SQLAlchemy
        liste_ptf (list)    : liste des ptf_id à inclure — ex: [1, 2] pour PEA+CTO

    Returns:
        float: TRI annualisé en %
    """

    # --- 1. RÉCUPÉRATION DES FLUX HISTORIQUES ---
    # On prend uniquement les APPORT (dépôts cash réels sur la poche broker)
    # Les ACHAT sont exclus — ce serait un double comptage avec les APPORT
    query = """
        SELECT
            pdt.ptf_id,
            mvt_date,
            -(mvt_nb_parts * mvt_prix + mvt_frais) AS calcul
        FROM mouvement_mvt mvt
        JOIN produit_financier_pdt pdt ON mvt.pdt_id = pdt.pdt_id
        WHERE mvt_type_mouvement IN ('APPORT', 'ABONDEMENT')
        AND pdt.ptf_id IN %(liste_ptf)s
    """

    df_tri = pd.read_sql(query, engine, params={"liste_ptf": tuple(liste_ptf)})
    df_tri = df_tri.sort_values('mvt_date')

    # --- 2. CONSTRUCTION DES LISTES XIRR ---
    flux  = df_tri["calcul"].tolist()
    dates = df_tri["mvt_date"].tolist()

    # --- 3. AJOUT DU FLUX FINAL POSITIF ---
    # Capital actuel = ce qu'on récupèrerait si on vendait tout aujourd'hui
    capital = df.query("ptf_id == @liste_ptf")['capital_actuel'].sum()
    flux.append(capital)
    dates.append(pd.Timestamp.today())

    # --- 4. CALCUL DU TRI ---
    tri = xirr(dates, flux)

    return tri * 100  # Converti en %


def get_perf_pdt_periode(df_histo_pdt, df_periode_pdt, duree, date_debut, liste_pdt, aggregate=False):
    """
    Calcule la performance de chaque produit sur la période sélectionnée.
    Gère les cas spéciaux "Début Mois" et "Max".

    ⚠️ Si snap_debut['jour'] > date_debut, cela signifie que la période demandée
    remonte avant le premier mouvement — on traite alors comme "Max" (profit total).

    Args:
        df_histo_pdt (DataFrame): view_historique_portefeuille_pdt (complet, non filtré)
        df_periode_pdt (DataFrame): df_histo_pdt filtré sur la période
        duree (str): valeur du slider
        date_debut (pd.Timestamp): date de début calculée par get_date_debut()
        liste_pdt (list): liste des pdt_id à inclure — ex: [4, 5, 6] pour CiC
        aggregate (bool): si True, retourne un dict agrégé {euro, pct} au lieu du détail par pdt_id
                            ⚠️ le % est recalculé sur la base totale, pas une moyenne des % individuels

    Returns:
        dict: si aggregate=False → {pdt_id: {"euro": float, "pct": float}}
            si aggregate=True  → {"euro": float, "pct": float}
    """
    debut_mois_actuel = pd.Timestamp.now().replace(day=1).normalize()

    perf = {}
    total_base = 0

    for pdt_id in liste_pdt:
        # Agrégation journalière pour ce produit sur la période
        df_temp = (df_periode_pdt.query("pdt_id == @pdt_id")
                    .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                    .sum()
                    .reset_index()
                    .query("capital_investi + abondement_recu > 1")
                    .sort_values('jour'))

        if not df_temp.empty:
            snap_fin = df_temp.iloc[-1]

            if duree == "Début Mois":
                # Snapshot avant le 1er du mois dans l'historique complet
                snap_debut = (df_histo_pdt.query("pdt_id == @pdt_id and jour < @debut_mois_actuel")
                                .groupby('jour')[['capital_actuel', 'profit_euro', 'capital_investi', 'abondement_recu']]
                                .sum()
                                .reset_index()
                                .query("capital_investi + abondement_recu > 1")
                                .sort_values('jour')
                                .iloc[-1])
            else:
                snap_debut = df_temp.iloc[0]

            # Si snap_debut est postérieur à date_debut → la période remonte avant le 1er mouvement
            # On traite comme "Max" : profit total depuis le début
            if duree == "Max" or snap_debut['jour'] > date_debut:
                euro = snap_fin['profit_euro']
            else:
                euro = snap_fin['profit_euro'] - snap_debut['profit_euro']

            # Base = effort perso + abondement pour un calcul de ROI correct
            base = snap_fin['capital_investi'] + snap_fin['abondement_recu']
            total_base += base
            pct = (euro / base * 100) if base > 0 else 0
        else:
            euro, pct = 0, 0

        perf[pdt_id] = {"euro": euro, "pct": pct}

    if aggregate:
        # somme euros + recalcul pct sur base totale
        total_euro = sum(v['euro'] for v in perf.values())
        pct = (total_euro / total_base * 100) if total_base > 0 else 0
        return {"euro": total_euro, "pct": pct}
    
    return perf


def get_tri_pdt(df, engine, liste_pdt):
    """
    Calcule le Taux de Rendement Interne (TRI / XIRR) pour chaque produit d'une liste.

    Reproduit la logique de TRI.PAIEMENTS d'Excel :
    - Flux négatifs : les apports et abondements historiques par produit
    - Flux positif final : le capital actuel à la date d'aujourd'hui

    Args:
        df (DataFrame)      : view_global_portefeuille (snapshot instantané)
        engine              : connexion SQLAlchemy
        liste_pdt (list)    : liste des pdt_id à inclure — ex: [4, 5, 6] pour CiC

    Returns:
        dict: {pdt_id: tri_annualisé} — ex: {4: 3.2, 5: 5.1, 6: 7.4}
    """
    tri = {}

    for pdt_id in liste_pdt:
        # --- 1. RÉCUPÉRATION DES FLUX HISTORIQUES ---
        # On prend uniquement les APPORT (dépôts cash réels sur la poche broker)
        # Les ACHAT sont exclus — ce serait un double comptage avec les APPORT
        query = """
            SELECT
                pdt_id,
                mvt_date,
                -(mvt_nb_parts * mvt_prix + mvt_frais) AS calcul
            FROM mouvement_mvt mvt
            WHERE mvt_type_mouvement IN ('APPORT', 'ABONDEMENT', 'TRANSFERT')
            AND pdt_id = %(pdt_id)s
        """

        df_tri = pd.read_sql(query, engine, params={"pdt_id": pdt_id})
        df_tri = df_tri.sort_values('mvt_date')

        # --- 2. CONSTRUCTION DES LISTES XIRR ---
        flux  = df_tri["calcul"].tolist()
        dates = df_tri["mvt_date"].tolist()

        # --- 3. AJOUT DU FLUX FINAL POSITIF ---
        # Capital actuel = ce qu'on récupèrerait si on vendait tout aujourd'hui
        capital = df.query("pdt_id == @pdt_id")['capital_actuel'].sum()
        flux.append(capital)
        dates.append(pd.Timestamp.today())

        # --- 4. CALCUL DU TRI ---
        tri[pdt_id] = xirr(dates, flux) * 100

    return tri


def get_tableau_mensuel_pdt(df_histo, df_apports, duree, mapping_pdt):
    """
    Construit le tableau mensuel du journal de bord.
    Retourne deux DataFrames :
    - df_tableau : version nettoyée pour l'affichage (tri décroissant, 1er mois viré)
    - df_tableau_buffer : version avec le mois de buffer nécessaire au calcul du graph
                            (trié croissant, 1er mois conservé pour le shift(1) de perf_graph)

    Args:
        df_histo (DataFrame): view_historique_portefeuille
        df_apports (DataFrame): view_apports_mensuels
        duree (str): valeur du slider
        mapping_pdt (dict): {pdt_id: nom_enveloppe} — ex: {1: "PEA", 2: "CTO", 3: "STEF"}
                        Les valeurs identiques permettent de regrouper plusieurs ptf sous une même colonne

    Returns:
        tuple: (df_tableau, df_tableau_buffer)
    """
    nb_mois = get_nb_mois(duree)
    debut_mois_actuel = pd.Timestamp.now().replace(day=1)
    # Date de départ du tableau — inclut 1 mois de buffer pour permettre le calcul des évolutions m-1
    date_debut_tableau = debut_mois_actuel - pd.DateOffset(months=nb_mois)

    # Copies pour ne pas modifier les DataFrames originaux
    df_mensuel = df_histo.copy()
    df_apports = df_apports.copy()

    # Ajout de la colonne enveloppe pour le regroupement
    df_mensuel['Enveloppe'] = df_mensuel['pdt_id'].map(mapping_pdt)

    # Agrégation journalière par enveloppe
    df_journalier = (df_mensuel.groupby(['Enveloppe', 'jour'])
                        .agg({'capital_actuel': 'sum', 'capital_investi': 'sum'})
                        .reset_index())

    # Pivot mensuel : dernière valeur du mois par enveloppe
    df_pivot = (df_journalier.groupby(['Enveloppe', pd.Grouper(key='jour', freq='ME')])
                .agg({'capital_actuel': 'last', 'capital_investi': 'last'})
                .unstack(level=0))

    df_tableau = df_pivot['capital_actuel'].copy()

    # --- Calcul des colonnes de performance ---
    df_tableau['Total'] = df_tableau.sum(axis=1)
    df_tableau['Evo Patrimoine'] = df_tableau['Total'].diff()
    df_tableau['Evo (%)'] = (df_tableau['Evo Patrimoine'] / df_tableau['Total'].shift(1)) * 100

    # Alignement des apports sur l'index mensuel du tableau
    # La vue SQL retourne des dates avec timezone → on la vire proprement avant le reindex
    df_apports['mois'] = df_apports['mois'].apply(lambda x: pd.Timestamp(x).replace(tzinfo=None).normalize())
    df_apports = df_apports.set_index('mois')
    injecte_mois = df_apports['injecte'].reindex(df_tableau.index, fill_value=0)

    # Perf marchés = variation patrimoine - argent injecté ce mois
    df_tableau['Perf Marchés (€)'] = df_tableau['Evo Patrimoine'] - injecte_mois

    # Colonnes glissantes sur 12 mois (activées via toggle dans Home.py)
    df_tableau['Evo 12m (€)'] = df_tableau['Total'] - df_tableau['Total'].shift(12)
    df_tableau['Evo 12m (%)'] = (df_tableau['Evo 12m (€)'] / df_tableau['Total'].shift(12)) * 100

    # --- Nettoyage ---
    # Filtre sur la période sélectionnée
    df_tableau = df_tableau.query("index >= @date_debut_tableau")

    # Ordre d'affichage : enveloppes dynamiques (dédupliquées) + colonnes fixes
    colonnes_ordre = list(dict.fromkeys(mapping_pdt.values())) + [
        'Total', 'Evo Patrimoine', 'Evo (%)', 'Perf Marchés (€)', 'Evo 12m (€)', 'Evo 12m (%)'
        ]

    # On n'affiche une enveloppe que si elle a des données non nulles
    colonnes_enveloppes = set(mapping_pdt.values())
    tableau = []
    for c in colonnes_ordre:
        if c in colonnes_enveloppes:
            if c in df_tableau.columns and df_tableau[c].notna().any() and df_tableau[c].sum() > 0:
                tableau.append(c)
        else:
            if c in df_tableau.columns and df_tableau[c].notna().any():
                tableau.append(c)

    df_tableau = df_tableau[tableau]

    # Buffer pour le graph : trié croissant, conserve le 1er mois
    # (nécessaire pour que get_donnees_graph puisse calculer perf_graph via shift(1))
    df_tableau_buffer = df_tableau.sort_index(ascending=True)

    # Tableau d'affichage : tri décroissant + suppression du 1er mois (artefact du diff())
    if nb_mois > 0:
        df_tableau = df_tableau.iloc[1:].sort_index(ascending=False)
    else:
        df_tableau = df_tableau.sort_index(ascending=False)

    df_tableau.index.name = 'Mois'

    return df_tableau, df_tableau_buffer


# def get_projection(capital, taux, injection_mensuelle, nb_annees):
-- ==========================================================
-- VUE : view_global_portefeuille
-- OBJECTIF : État des lieux en temps réel (Valeur actuelle, PRU, Perf)
-- ==========================================================

CREATE OR REPLACE VIEW view_global_portefeuille AS
WITH flux_net AS (
    -- Premier bloc : Analyse de tous les mouvements historiques par produit
    SELECT 
        pdt_id, 
        -- 1. TON EFFORT : Argent réellement sorti de ta poche (achats titres - hors abondement)
        SUM(CASE WHEN mvt_nb_parts > 0 AND (mvt_type_mouvement != 'ABONDEMENT' OR mvt_type_mouvement IS NULL) 
                 THEN (mvt_nb_parts * mvt_prix) + mvt_frais ELSE 0 END) AS effort_epargne_perso,
        
        -- 2. L'ABONDEMENT : Argent "cadeau" versé par l'entreprise
        SUM(CASE WHEN mvt_type_mouvement = 'ABONDEMENT' 
                 THEN (mvt_nb_parts * mvt_prix) ELSE 0 END) AS total_abondement,

        -- 3. FLUX NET CASH : Calcul du solde pour les livrets (Dépôts - Retraits)
        SUM(mvt_nb_parts * mvt_prix + mvt_frais) AS cash_net_dans_le_produit,
        
        -- 4. BASES DE CALCUL POUR PROFIT : Total des entrées et sorties historiques
        SUM(CASE WHEN mvt_nb_parts > 0 THEN (mvt_nb_parts * mvt_prix) + mvt_frais ELSE 0 END) AS total_investi_historique,
        SUM(CASE WHEN mvt_nb_parts < 0 THEN ABS(mvt_nb_parts * mvt_prix) ELSE 0 END) AS total_encaisse_historique
    FROM public.mouvement_mvt
    GROUP BY pdt_id
),
derniere_cotation AS (
    -- Deuxième bloc : Récupération du prix le plus récent pour chaque produit
    SELECT pdt_id, cot_prix, cot_date
    FROM (
        SELECT pdt_id, cot_prix, cot_date,
               ROW_NUMBER() OVER (PARTITION BY pdt_id ORDER BY cot_date DESC) as rn
        FROM public.cotation_cot
    ) t WHERE t.rn = 1
)
-- ==========================================================
-- SELECTION FINALE : Jointure des positions avec les flux et prix
-- ==========================================================
SELECT 
    vpa.pdt_id,
    vpa.ptf_id,
    vpa.pdt_cash,
    vpa.pdt_est_actif,
    vpa.quantite_detenue,
    
    -- CAPITAL INVESTI : 
    -- Si c'est du cash, l'investi c'est ce qu'il reste (solde). 
    -- Si c'est un titre, c'est la somme de tes achats passés.
    CASE 
        WHEN vpa.pdt_cash = True THEN vpa.quantite_detenue
        ELSE COALESCE(fn.effort_epargne_perso, 0) 
    END AS capital_investi,
    
    -- CAPITAL ACTUEL : Ce que ça vaut aujourd'hui
    vpa.quantite_detenue * COALESCE(dc.cot_prix, 1) AS capital_actuel,

    -- ABONDEMENT : Visualisation de l'argent gratuit cumulé
    COALESCE(fn.total_abondement, 0) AS abondement_recu,

    -- PRU : Prix de revient calculé par ta vue dédiée
    CAST(COALESCE(pru.pru, 0) AS NUMERIC) AS prix_achat_moyen,
    
    -- PROFIT EURO : (Valeur actuelle + Ventes passées) - Achats passés
    -- Forcé à 0 pour le cash (le cash ne fait pas de profit boursier)
    CASE 
        WHEN vpa.pdt_cash = True THEN 0
        ELSE (
            (vpa.quantite_detenue * COALESCE(dc.cot_prix, 1)) 
            + COALESCE(fn.total_encaisse_historique, 0) 
            - COALESCE(fn.total_investi_historique, 0)
        )
    END AS profit_euro,

    -- PROFIT % : Performance réelle alignée sur tes autres vues
    CASE 
        WHEN vpa.pdt_cash = True THEN 0
        -- Formule : Profit / (Ton Argent + Abondement)
        WHEN (COALESCE(fn.effort_epargne_perso, 0) + COALESCE(fn.total_abondement, 0)) > 0 
        THEN 
            ((
                (vpa.quantite_detenue * COALESCE(dc.cot_prix, 1) + COALESCE(fn.total_encaisse_historique, 0)) 
                / (fn.effort_epargne_perso + fn.total_abondement)
            ) - 1) * 100
        ELSE 0 
    END AS profit_pourcent,
    
    dc.cot_date AS derniere_maj_cours

FROM view_positions_actuelles vpa
LEFT JOIN flux_net fn ON vpa.pdt_id = fn.pdt_id
LEFT JOIN derniere_cotation dc ON vpa.pdt_id = dc.pdt_id
LEFT JOIN view_pru pru ON vpa.pdt_id = pru.pdt_id
ORDER BY pdt_id;
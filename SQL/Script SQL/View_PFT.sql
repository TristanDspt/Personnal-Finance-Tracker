-- VUE BRIQUE

-- Vue instantannée
CREATE OR REPLACE VIEW view_positions_actuelles as
SELECT 
    mvt.pdt_id, 
    pdt.pdt_nom_produit,
    -- La somme de toutes les parts (Achats + Ventes en négatif)
    SUM(mvt.mvt_nb_parts) as quantite_detenue,
    pdt.ptf_id,
    pdt.pdt_cash,
    pdt.pdt_est_actif
FROM public.mouvement_mvt mvt
INNER JOIN public.produit_financier_pdt pdt ON pdt.pdt_id = mvt.pdt_id
GROUP BY mvt.pdt_id, pdt.pdt_nom_produit, pdt.pdt_cash, pdt.ptf_id, pdt.pdt_est_actif;

-- Vue PRU
CREATE OR REPLACE VIEW view_pru AS
SELECT 
    pdt_id,
    -- On garde ta logique de calcul avec les frais (c'est très bien !)
    CASE 
        WHEN SUM(CASE WHEN mvt_nb_parts > 0 THEN mvt_nb_parts ELSE 0 END) > 0 
        THEN SUM(CASE WHEN mvt_nb_parts > 0 THEN (mvt_nb_parts * mvt_prix) + mvt_frais ELSE 0 END) 
             / SUM(CASE WHEN mvt_nb_parts > 0 THEN mvt_nb_parts ELSE 0 END)
        ELSE 0 
    END as pru
FROM public.mouvement_mvt
GROUP BY pdt_id;



-- SUPER VUE

CREATE OR REPLACE VIEW view_global_portefeuille AS
WITH flux_net AS (
    SELECT 
        pdt_id, 
        -- 1. TON ARGENT : Somme des achats réels (on exclut l'abondement pour ton effort perso)
        SUM(CASE WHEN mvt_nb_parts > 0 AND (mvt_type_mouvement != 'ABONDEMENT' OR mvt_type_mouvement IS NULL) 
                 THEN (mvt_nb_parts * mvt_prix) + mvt_frais ELSE 0 END) AS effort_epargne_perso,
        
        -- 2. L'ABONDEMENT : L'argent gratuit identifié par le type de mouvement
        SUM(CASE WHEN mvt_type_mouvement = 'ABONDEMENT' 
                 THEN (mvt_nb_parts * mvt_prix) ELSE 0 END) AS total_abondement,

        -- 3. FLUX NET : Pour gérer les livrets (Dépôts - Retraits)
        SUM(mvt_nb_parts * mvt_prix + mvt_frais) AS cash_net_dans_le_produit,
        
        -- 4. HISTO COMPLET : Utile pour le calcul du profit total (valeur + ce qui est déjà sorti)
        SUM(CASE WHEN mvt_nb_parts > 0 THEN (mvt_nb_parts * mvt_prix) + mvt_frais ELSE 0 END) AS total_investi_historique,
        SUM(CASE WHEN mvt_nb_parts < 0 THEN ABS(mvt_nb_parts * mvt_prix) ELSE 0 END) AS total_encaisse_historique
    FROM public.mouvement_mvt
    GROUP BY pdt_id
),
derniere_cotation AS (
    SELECT pdt_id, cot_prix_unitaire, cot_date_prix
    FROM (
        SELECT pdt_id, cot_prix_unitaire, cot_date_prix,
               ROW_NUMBER() OVER (PARTITION BY pdt_id ORDER BY cot_date_prix DESC) as rn
        FROM public.cotation_cot
    ) t WHERE t.rn = 1
)
SELECT 
    vpa.pdt_id,
    vpa.ptf_id,
    vpa.pdt_nom_produit,
    vpa.quantite_detenue,
    vpa.pdt_cash,
    vpa.pdt_est_actif,
    
    -- CAPITAL INVESTI :
    CASE 
        WHEN vpa.pdt_cash = True THEN ROUND(vpa.quantite_detenue::numeric, 2)
        ELSE ROUND(COALESCE(fn.effort_epargne_perso, 0)::numeric, 2) 
    END AS capital_investi,
    
    -- CAPITAL ACTUEL : Valeur marché aujourd'hui (Quantité * Dernier cours)
    ROUND((vpa.quantite_detenue * COALESCE(dc.cot_prix_unitaire, 1))::numeric, 2) AS capital_actuel,

    -- ABONDEMENT : Argent gratuit cumulé sur ce produit
    ROUND(COALESCE(fn.total_abondement, 0)::numeric, 2) AS abondement_recu,

    -- PRU (Prix de Revient Unitaire) : Ton prix moyen d'achat
    ROUND(CAST(COALESCE(pru.pru, 0) AS NUMERIC), 4) AS prix_achat_moyen,
    
    -- PROFIT EURO : Argent gagné (Valeur + Ventes - Achats totaux). 0 pour le cash.
    CASE 
        WHEN vpa.pdt_cash = True THEN 0
        ELSE ROUND((
            (vpa.quantite_detenue * COALESCE(dc.cot_prix_unitaire, 1)) 
            + COALESCE(fn.total_encaisse_historique, 0) 
            - COALESCE(fn.total_investi_historique, 0)
        )::numeric, 2)
    END AS profit_euro,

    -- PROFIT % : Performance basée sur la réalité de l'actif (abondement + capital investi)
    CASE 
        WHEN vpa.pdt_cash = True THEN 0
        -- On divise par (Ton Argent + Abondement) pour avoir la base réelle du placement
        WHEN (COALESCE(fn.effort_epargne_perso, 0) + COALESCE(fn.total_abondement, 0)) > 0 
        THEN ROUND(
            ((
                (vpa.quantite_detenue * COALESCE(dc.cot_prix_unitaire, 1) + COALESCE(fn.total_encaisse_historique, 0)) 
                / (fn.effort_epargne_perso + fn.total_abondement)
            ) - 1)::numeric * 100, 2)
        ELSE 0 
    END AS profit_pourcent,
    
    dc.cot_date_prix AS derniere_maj_cours

FROM view_positions_actuelles vpa
LEFT JOIN flux_net fn ON vpa.pdt_id = fn.pdt_id
LEFT JOIN derniere_cotation dc ON vpa.pdt_id = dc.pdt_id
LEFT JOIN view_pru pru ON vpa.pdt_id = pru.pdt_id;


				
	
		

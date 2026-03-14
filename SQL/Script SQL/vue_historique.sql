-- ==========================================================
-- VUE : view_historique_portefeuille
-- OBJECTIF : Reconstitution quotidienne de la valeur et de la performance
-- ==========================================================

CREATE OR REPLACE VIEW view_historique_portefeuille AS
WITH date_range AS (
    -- 1. Génère un calendrier complet du premier mouvement à aujourd'hui
    -- Cela permet de ne pas avoir de "trous" dans les graphiques
    SELECT generate_series(MIN(mvt_date), CURRENT_DATE, '1 day')::date AS jour 
    FROM public.mouvement_mvt
),
produits AS (
    -- 2. Récupère la liste des produits et leur nature (Cash vs Titre)
    SELECT pdt_id, ptf_id, pdt_cash FROM public.produit_financier_pdt
),
grille_vide AS (
    -- 3. Crée une matrice (Jour x Produit) pour calculer les soldes chaque jour
    SELECT d.jour, p.pdt_id, p.ptf_id, p.pdt_cash FROM date_range d CROSS JOIN produits p
),
mouvements_cumules AS (
    -- 4. Agrégation des flux quotidiens par produit
    SELECT 
        gv.jour, gv.pdt_id, gv.ptf_id, gv.pdt_cash,
        
        -- Variation du nombre de parts (ou montant si cash) le jour J
        COALESCE(SUM(mvt.mvt_nb_parts), 0) as mvt_parts_jour,
        
        -- CALCUL DE L'EFFORT PERSO (Capital Investi)
		COALESCE(SUM(CASE 
		    -- 1. Sur la ligne CASH : 
		    -- On compte les dépôts (+) ET on retire les achats de titres (-) 
		    -- (mvt_nb_parts sur le cash est le montant en €)
		    WHEN gv.pdt_cash = True THEN mvt.mvt_nb_parts
		    
		    -- 2. Sur la ligne TITRE : 
		    -- On compte l'achat comme un effort (+)
		    WHEN gv.pdt_cash = False AND mvt.mvt_nb_parts > 0 AND mvt.mvt_type_mouvement NOT IN ('ABONDEMENT', 'TRANSFERT') 
		         THEN (mvt.mvt_nb_parts * mvt.mvt_prix) + mvt.mvt_frais
		    
		    ELSE 0 
		END), 0) as effort_perso_jour,

        -- Abondements (Argent offert par l'entreprise, n'est pas un effort perso)
        COALESCE(SUM(CASE WHEN mvt.mvt_type_mouvement = 'ABONDEMENT' 
                          THEN (mvt.mvt_nb_parts * mvt.mvt_prix) ELSE 0 END), 0) as abondement_jour,

        -- Variables pour le calcul du profit historique (flux entrants vs sortants)
        COALESCE(SUM(CASE WHEN mvt.mvt_nb_parts > 0 AND mvt.mvt_type_mouvement NOT IN ('TRANSFERT') THEN (mvt.mvt_nb_parts * mvt.mvt_prix) + mvt.mvt_frais ELSE 0 END), 0) as investi_brut_jour,
        COALESCE(SUM(CASE WHEN mvt.mvt_nb_parts < 0 THEN ABS(mvt.mvt_nb_parts * mvt.mvt_prix) ELSE 0 END), 0) as encaisse_jour
    FROM grille_vide gv
    LEFT JOIN public.mouvement_mvt mvt ON gv.jour = mvt.mvt_date AND gv.pdt_id = mvt.pdt_id
    GROUP BY gv.jour, gv.pdt_id, gv.ptf_id, gv.pdt_cash
),
historique_cumule AS (
    -- 5. Transformation des flux quotidiens en soldes cumulés (Sommes glissantes)
    SELECT 
        jour, pdt_id, ptf_id, pdt_cash,
        SUM(mvt_parts_jour) OVER (PARTITION BY pdt_id ORDER BY jour) as quantite_detenue,
        SUM(effort_perso_jour) OVER (PARTITION BY pdt_id ORDER BY jour) as capital_investi,
        SUM(abondement_jour) OVER (PARTITION BY pdt_id ORDER BY jour) as abondement_recu,
        SUM(investi_brut_jour) OVER (PARTITION BY pdt_id ORDER BY jour) as total_investi_histo,
        SUM(encaisse_jour) OVER (PARTITION BY pdt_id ORDER BY jour) as total_encaisse_histo
    FROM mouvements_cumules
),
historique_prix_groupes AS (
    -- 6. Gestion des prix : on associe les cotations et on prépare le remplissage des jours vides (week-ends)
    SELECT 
        hc.*, cot.cot_prix,
        COUNT(cot.cot_prix) OVER (PARTITION BY hc.pdt_id ORDER BY hc.jour) as grp_prix
    FROM historique_cumule hc
    LEFT JOIN public.cotation_cot cot ON hc.jour = cot.cot_date AND hc.pdt_id = cot.pdt_id
),
historique_final AS (
    -- 7. "Forward Fill" : on récupère le dernier prix connu si pas de cotation ce jour-là
    SELECT 
        *,
        FIRST_VALUE(cot_prix) OVER (PARTITION BY pdt_id, grp_prix ORDER BY jour) as prix_a_jour
    FROM historique_prix_groupes
)
-- ==========================================================
-- SELECTION FINALE : Calculs des indicateurs de performance
-- ==========================================================
SELECT  
    hc.pdt_id, 
    hc.ptf_id,
    pdt.pdt_cash,
    pdt.pdt_est_actif,
    quantite_detenue,
    
    -- Capital Investi : L'argent réel sorti de ta poche à date
    capital_investi,
    
    -- Abondements : Cumul des primes employeurs
    abondement_recu,

    -- Capital Actuel : Valeur de revente estimée au prix du jour
    CASE 
        WHEN hc.pdt_cash = True THEN quantite_detenue
        ELSE quantite_detenue * COALESCE(prix_a_jour, 0) 
    END as capital_actuel,

    -- Profit Euro : (Valeur Actuelle + Cash déjà retiré) - (Cash total injecté historiquement)
    CASE 
        WHEN hc.pdt_cash = True THEN 0
        ELSE (
            (quantite_detenue * COALESCE(prix_a_jour, 0)) 
            + total_encaisse_histo 
            - total_investi_histo
        )
    END as profit_euro,
    jour

FROM historique_final hc
JOIN public.produit_financier_pdt pdt ON hc.pdt_id = pdt.pdt_id
-- On masque les lignes inutiles (produits pas encore achetés ou totalement vendus sans historique)
WHERE quantite_detenue != 0 OR capital_investi != 0
ORDER BY jour DESC, pdt_id;
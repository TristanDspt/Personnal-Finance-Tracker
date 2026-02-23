-- ==========================================================
-- VUE : view_historique_portefeuille
-- OBJECTIF : Reconstitution quotidienne de la valeur et de la performance
-- ==========================================================

CREATE OR REPLACE VIEW view_historique_portefeuille AS
WITH date_range AS (
    -- Génère un calendrier complet du premier mouvement à aujourd'hui
    SELECT generate_series(MIN(mvt_date), CURRENT_DATE, '1 day')::date AS jour 
    FROM public.mouvement_mvt
),
produits AS (
    -- Récupère la liste des produits pour savoir s'il s'agit de CASH ou de TITRES
    SELECT pdt_id, ptf_id, pdt_cash FROM public.produit_financier_pdt
),
grille_vide AS (
    -- Crée une ligne par jour et par produit (matrice vide pour remplir les trous)
    SELECT d.jour, p.pdt_id, p.ptf_id, p.pdt_cash FROM date_range d CROSS JOIN produits p
),
mouvements_cumules AS (
    -- Agrégation des flux quotidiens par produit
    SELECT 
        gv.jour, gv.pdt_id, gv.ptf_id, gv.pdt_cash,
        -- Somme des parts du jour
        COALESCE(SUM(mvt.mvt_nb_parts), 0) as mvt_parts_jour,
        
        -- EFFORT PERSO (Le dénominateur de TA performance)
        COALESCE(SUM(CASE 
            -- Pour le CASH : On prend le solde net (Dépôts - Retraits). 
            -- C'est la clé pour éviter de compter 2x le capital lors d'un achat d'action.
            WHEN gv.pdt_cash = True THEN mvt.mvt_nb_parts 
            -- Pour les TITRES : On ne somme que les ACHATS (flux entrants) hors abondement.
            WHEN mvt.mvt_nb_parts > 0 AND (mvt.mvt_type_mouvement != 'ABONDEMENT' OR mvt.mvt_type_mouvement IS NULL) 
            THEN (mvt.mvt_nb_parts * mvt.mvt_prix) + mvt.mvt_frais 
            ELSE 0 
        END), 0) as effort_perso_jour,

        -- Somme des abondements reçus ce jour
        COALESCE(SUM(CASE WHEN mvt.mvt_type_mouvement = 'ABONDEMENT' 
                          THEN (mvt.mvt_nb_parts * mvt.mvt_prix) ELSE 0 END), 0) as abondement_jour,

        -- Variables de calcul du Profit (entrées totales vs sorties totales)
        COALESCE(SUM(CASE WHEN mvt.mvt_nb_parts > 0 THEN (mvt.mvt_nb_parts * mvt.mvt_prix) + mvt.mvt_frais ELSE 0 END), 0) as investi_brut_jour,
        COALESCE(SUM(CASE WHEN mvt.mvt_nb_parts < 0 THEN ABS(mvt.mvt_nb_parts * mvt.mvt_prix) ELSE 0 END), 0) as encaisse_jour
    FROM grille_vide gv
    LEFT JOIN public.mouvement_mvt mvt ON gv.jour = mvt.mvt_date AND gv.pdt_id = mvt.pdt_id
    GROUP BY gv.jour, gv.pdt_id, gv.ptf_id, gv.pdt_cash
),
historique_cumule AS (
    -- Transformation des flux quotidiens en soldes cumulés (Sommes glissantes)
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
    -- Jointure avec les cotations et création de groupes pour le "Forward Fill" (combler les jours sans prix)
    SELECT 
        hc.*, cot.cot_prix,
        COUNT(cot.cot_prix) OVER (PARTITION BY hc.pdt_id ORDER BY hc.jour) as grp_prix
    FROM historique_cumule hc
    LEFT JOIN public.cotation_cot cot ON hc.jour = cot.cot_date AND hc.pdt_id = cot.pdt_id
),
historique_final AS (
    -- On récupère le dernier prix connu pour chaque jour
    SELECT 
        *,
        FIRST_VALUE(cot_prix) OVER (PARTITION BY pdt_id, grp_prix ORDER BY jour) as prix_a_jour
    FROM historique_prix_groupes
)
-- ==========================================================
-- SELECTION FINALE : Calculs des indicateurs métiers
-- ==========================================================
SELECT  
    hc.pdt_id, 
    hc.ptf_id,
    pdt.pdt_cash,
    pdt.pdt_est_actif,
    quantite_detenue,
    
    -- 1. Effort financier de l'utilisateur (Argent sorti de sa poche)
    capital_investi as capital_investi,
    
    -- 2. Argent "offert" par l'entreprise
    abondement_recu,

    -- 3. Valeur actuelle (Prix du marché * Quantité / ou Solde si cash)
    CASE 
        WHEN hc.pdt_cash = True THEN quantite_detenue
        ELSE quantite_detenue * COALESCE(prix_a_jour, 0) 
    END as capital_actuel,

    -- 4. Profit en Euros : (Valeur Actuelle + Sorties Cash) - Entrées Cash
    -- On force à 0 pour le cash car il ne génère pas de profit en soi
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
-- On filtre pour ne pas afficher les produits avant leur achat ou après leur clôture totale
WHERE quantite_detenue > 0 OR capital_investi > 0
ORDER BY jour DESC, pdt_id;
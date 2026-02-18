-- VUE PRINCIPALES

-- Vue instantannée des placements
CREATE OR REPLACE VIEW view_positions_actuelles as
SELECT 
    mvt.pdt_id, 
    pdt.pdt_nom_produit,
    -- La somme de toutes les parts (Achats + Ventes en négatif)
    SUM(mvt.mvt_nb_parts) as quantite_detenue
FROM public.mouvement_mvt mvt
INNER JOIN public.produit_financier_pdt pdt ON pdt.pdt_id = mvt.pdt_id
WHERE pdt.pdt_est_actif = true
GROUP BY mvt.pdt_id, pdt.pdt_nom_produit
HAVING SUM(mvt.mvt_nb_parts) > 0; -- Pour ne pas afficher les lignes soldées à zéro

-- Vue PRU
CREATE OR REPLACE VIEW view_pru as
SELECT 
    mvt.pdt_id, 
    pdt.pdt_nom_produit,
    -- 1. Coût total d'achat (Parts * Prix + Frais) pour les flux positifs
    SUM(
        CASE WHEN mvt_nb_parts > 0 
        THEN (mvt_nb_parts * mvt_prix) + mvt_frais 
        ELSE 0
    END) as cout_total_achat,
    -- 2. Total des parts achetées historiquement
    SUM(
        CASE WHEN mvt_nb_parts > 0 
        THEN mvt_nb_parts 
        ELSE 0
    END) as total_parts_achetees,
    -- 3. Calcul du PRU avec sécurité division par zéro
    CASE 
        WHEN SUM(CASE WHEN mvt_nb_parts > 0 THEN mvt_nb_parts ELSE 0 END) > 0 
        THEN SUM(CASE WHEN mvt_nb_parts > 0 THEN (mvt_nb_parts * mvt_prix) + mvt_frais ELSE 0 END) 
             / SUM(CASE WHEN mvt_nb_parts > 0 THEN mvt_nb_parts ELSE 0 END)
        ELSE 0 
    END as pru
FROM public.mouvement_mvt mvt
INNER JOIN public.produit_financier_pdt pdt ON pdt.pdt_id = mvt.pdt_id
WHERE 
    pdt.pdt_cash != true
    AND pdt.pdt_est_actif = true
GROUP BY mvt.pdt_id, pdt.pdt_nom_produit;
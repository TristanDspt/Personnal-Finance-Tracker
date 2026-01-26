CREATE OR REPLACE VIEW view_pru_par_produit AS
SELECT 
    p.pdt_nom,
    p.pdt_ticker,
    SUM(m.mvt_nb_parts) as total_parts,
    SUM(m.mvt_nb_parts * m.mvt_prix_unitaire + m.mvt_frais) as cout_total_achat,
    -- Calcul du PRU (Coût total / Nombre de parts)
    CASE 
        WHEN SUM(m.mvt_nb_parts) > 0 
        THEN SUM(m.mvt_nb_parts * m.mvt_prix_unitaire + m.mvt_frais) / SUM(m.mvt_nb_parts)
        ELSE 0 
    END as pru
FROM public.produit_financier_pdt p
JOIN public.mouvement_mvt m ON p.pdt_id = m.pdt_id
GROUP BY p.pdt_nom, p.pdt_ticker;

SELECT 
    p.pdt_nom_produit,
    ptf.ptf_nom_banque,
    -- 1. Calcul du stock total actuel
    SUM(m.mvt_nb_parts) as stock_actuel,
    -- 2. Récupération du dernier prix unitaire connu
    (SELECT c.cot_prix_unitaire 
     FROM public.cotation_cot c 
     WHERE c.pdt_id = p.pdt_id 
     ORDER BY c.cot_date_prix DESC LIMIT 1) as dernier_prix,
    -- 3. Valorisation (Stock * Prix)
    SUM(m.mvt_nb_parts) * (SELECT c.cot_prix_unitaire 
                           FROM public.cotation_cot c 
                           WHERE c.pdt_id = p.pdt_id 
                           ORDER BY c.cot_date_prix DESC LIMIT 1) as valorisation_totale
FROM public.produit_financier_pdt p
JOIN public.portefeuille_ptf ptf ON p.ptf_id = ptf.ptf_id
LEFT JOIN public.mouvement_mvt m ON p.pdt_id = m.pdt_id
WHERE p.pdt_est_actif = TRUE
GROUP BY p.pdt_id, p.pdt_nom_produit, ptf.ptf_nom_banque;

WITH Recap_Mensuel AS (
    SELECT 
        date_trunc('month', mvt_date)::date as mois,
        pdt_id,
        SUM(SUM(mvt_nb_parts)) OVER (PARTITION BY pdt_id ORDER BY date_trunc('month', mvt_date)) as stock_parts
    FROM public.mouvement_mvt
    GROUP BY 1, 2
)
SELECT 
    r.mois,
    p.pdt_nom_produit,
    r.stock_parts,
    (SELECT cot_prix_unitaire 
     FROM public.cotation_cot c 
     WHERE c.pdt_id = r.pdt_id 
       AND c.cot_date_prix <= (r.mois + interval '1 month' - interval '1 day')::date
     ORDER BY c.cot_date_prix DESC LIMIT 1) as dernier_prix
FROM Recap_Mensuel r
JOIN public.produit_financier_pdt p ON r.pdt_id = p.pdt_id;
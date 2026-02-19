-- VUE PRINCIPALES

-- Vue instantannée
CREATE OR REPLACE VIEW view_positions_actuelles as
SELECT 
    mvt.pdt_id, 
    pdt.pdt_nom_produit,
    -- La somme de toutes les parts (Achats + Ventes en négatif)
    SUM(mvt.mvt_nb_parts) as quantite_detenue,
    pdt.ptf_id,
    pdt.pdt_cash
FROM public.mouvement_mvt mvt
INNER JOIN public.produit_financier_pdt pdt ON pdt.pdt_id = mvt.pdt_id
WHERE pdt.pdt_est_actif = true
GROUP BY mvt.pdt_id, pdt.pdt_nom_produit, pdt.pdt_cash,pdt.ptf_id
HAVING SUM(mvt.mvt_nb_parts) > 0; -- Pour ne pas afficher les lignes soldées à zéro

-- Vue Historique
CREATE OR REPLACE VIEW view_performance_historique as
WITH flux AS (
    SELECT pdt_id, SUM(mvt_nb_parts * mvt_prix) as total_investi
    FROM public.mouvement_mvt
    GROUP BY pdt_id
),
valeur AS (
    -- On prend la dernière cotation multipliée par le nombre de parts actuel
    SELECT 
        vpa.pdt_id, 
        vpa.quantite_detenue * COALESCE(
            (SELECT cot_prix_unitaire FROM public.cotation_cot c 
             WHERE c.pdt_id = vpa.pdt_id ORDER BY cot_date_prix DESC LIMIT 1), 
            1
        ) as valeur_marche
    FROM view_positions_actuelles vpa
)
SELECT 
    pdt.pdt_id,
    pdt.ptf_id,
    pdt.pdt_nom_produit,
    pdt.pdt_cash,
    COALESCE(v.valeur_marche, 0) as valeur_actuelle,
    COALESCE(v.valeur_marche, 0) - COALESCE(f.total_investi, 0) as profit_euro
FROM public.produit_financier_pdt pdt
LEFT JOIN flux f ON pdt.pdt_id = f.pdt_id
LEFT JOIN valeur v ON pdt.pdt_id = v.pdt_id;

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

-- VUE SECONDAIRES

-- Vue Valeur PFT
CREATE OR REPLACE VIEW view_valeur_portefeuille as
with derniere_date as (
	select
		pdt_id,
		max(cot_date_prix) as max_date
	from public.cotation_cot
	group by pdt_id
),
	dernier_prix as (
	select 
		cot.pdt_id,
		cot.cot_prix_unitaire
	from public.cotation_cot cot
	inner join derniere_date dd
		on cot.pdt_id = dd.pdt_id
		and cot.cot_date_prix = dd.max_date
)
select
	vpa.pdt_id,
	vpa.ptf_id,
	vpa.pdt_nom_produit,
	vpa.quantite_detenue,
	vpa.quantite_detenue * COALESCE(dp.cot_prix_unitaire, 1) AS valeur_actuelle,
	pru.pru,
	vpa.quantite_detenue * COALESCE(pru.pru, 1) as valeur_pru_totale,
	vpa.pdt_cash
from view_positions_actuelles vpa
left join dernier_prix dp
	on dp.pdt_id = vpa.pdt_id
left join view_pru pru 
	on vpa.pdt_id = pru.pdt_id


				
	
		

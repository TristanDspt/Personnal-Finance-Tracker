-- ==========================================================
-- VUE : view_apports_mensuels
-- OBJECTIF : Calcul des flux d'argent réels entrant/sortant par mois
--            Sert à calculer la "Perf Marchés" dans le dashboard
--            (Variation patrimoine - Argent injecté/retiré = perf pure des marchés)
-- ==========================================================

CREATE OR REPLACE VIEW view_apports_mensuels AS
SELECT
    -- Ramène toutes les dates au dernier jour du mois pour aligner avec Pandas
    (DATE_TRUNC('month', mvt_date) + INTERVAL '1 month' - INTERVAL '1 day')::date as mois,
    
    SUM(CASE
        -- CASH (livrets, poches broker) : mvt_nb_parts est déjà en €
        -- APPORT (+) et RETRAIT (-) sont déjà signés correctement en DB
        WHEN pdt_cash = TRUE THEN mvt_nb_parts
        
        -- TITRES PEE : mvt_nb_parts est en parts, on multiplie par le prix pour avoir les €
        -- Inclut les versements volontaires (APPORT) et l'abondement employeur (ABONDEMENT)
        WHEN pdt_cash = FALSE THEN mvt_nb_parts * mvt_prix
    END) as injecte

FROM mouvement_mvt mvt
JOIN produit_financier_pdt pdt ON mvt.pdt_id = pdt.pdt_id

WHERE 
    -- Flux cash réels : APPORT (entrée) et RETRAIT (sortie)
    -- Les RETRAIT_MIROIR (débit automatique lors d'un achat ETF) sont exclus
    (pdt_cash = TRUE AND mvt_type_mouvement IN ('APPORT', 'RETRAIT'))
    OR
    -- Versements PEE : APPORT volontaire + ABONDEMENT employeur
    -- ⚠️ Les mouvements PEE doivent être saisis en APPORT (pas ACHAT)
    (pdt_cash = FALSE AND mvt_type_mouvement IN ('APPORT', 'ABONDEMENT'))
    -- Type Vente : L'argent sort de la bourse pour aller dans ma poche
   	-- La perf marché ne doit pas etre impacté par un vente
    OR (pdt_cash = FALSE AND mvt_type_mouvement IN ('VENTE'))

GROUP BY DATE_TRUNC('month', mvt_date)
ORDER BY mois;


-- ==========================================================
-- VUE : view_apports_mensuels_pdt
-- OBJECTIF : Même logique que view_apports_mensuels mais granularité produit (pdt_id)
--            Sert à filtrer les apports par produit dans les dashboards individuels
--            (PEA, CTO, STEF, CiC) pour construire la courbe "Injecté" par enveloppe
-- ==========================================================

CREATE OR REPLACE VIEW view_apports_mensuels_pdt AS
SELECT
	pdt.pdt_id,
    -- Ramène toutes les dates au dernier jour du mois pour aligner avec Pandas
    (DATE_TRUNC('month', mvt_date) + INTERVAL '1 month' - INTERVAL '1 day')::date as mois,
    
    SUM(CASE
        -- CASH (livrets, poches broker) : mvt_nb_parts est déjà en €
        -- APPORT (+) et RETRAIT (-) sont déjà signés correctement en DB
        WHEN pdt_cash = TRUE THEN mvt_nb_parts
        
        -- TITRES PEE : mvt_nb_parts est en parts, on multiplie par le prix pour avoir les €
        -- Inclut les versements volontaires (APPORT) et l'abondement employeur (ABONDEMENT)
        WHEN pdt_cash = FALSE THEN mvt_nb_parts * mvt_prix
    END) as injecte

FROM mouvement_mvt mvt
JOIN produit_financier_pdt pdt ON mvt.pdt_id = pdt.pdt_id

WHERE 
    -- Flux cash réels : APPORT (entrée) et RETRAIT (sortie)
    -- Les RETRAIT_MIROIR (débit automatique lors d'un achat ETF) sont exclus
    (pdt_cash = TRUE AND mvt_type_mouvement IN ('APPORT', 'RETRAIT'))
    -- Versements PEE : APPORT volontaire + ABONDEMENT employeur
    -- ⚠️ Les mouvements PEE doivent être saisis en APPORT (pas ACHAT)
    -- ⚠️ TRANSFERT inclus ici (contrairement à view_apports_mensuels) car à la granularité
	-- pdt_id y'a pas de double comptage — chaque produit est regardé individuellement
    OR (pdt_cash = FALSE AND mvt_type_mouvement IN ('APPORT', 'ABONDEMENT', 'TRANSFERT'))
    -- Type Vente : L'argent sort de la bourse pour aller dans ma poche
   	-- La perf marché ne doit pas etre impacté par un vente
    OR (pdt_cash = FALSE AND mvt_type_mouvement IN ('VENTE'))

GROUP BY DATE_TRUNC('month', mvt_date), pdt.pdt_id
ORDER BY mois;
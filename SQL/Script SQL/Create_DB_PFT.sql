-- ==========================================================
--          SCHEMA SQL : GESTION DE PATRIMOINE
-- ==========================================================

------------------------------------------------------------
-- 1. TABLE : PORTEFEUILLE (Contenants : PEA, Livret A...)
------------------------------------------------------------
CREATE SEQUENCE public.portefeuille_ptf_ptf_id_seq;

CREATE TABLE public.portefeuille_PTF (
    PTF_id INTEGER NOT NULL DEFAULT nextval('public.portefeuille_ptf_ptf_id_seq'),
    PTF_nom_banque VARCHAR(50) NOT NULL,
    PTF_type_enveloppe VARCHAR(20) NOT NULL,
    PTF_est_actif BOOLEAN NOT NULL,
    CONSTRAINT ptf_id PRIMARY KEY (PTF_id)
);

-- Lie la séquence à la colonne pour qu'elle soit supprimée si la table l'est
ALTER SEQUENCE public.portefeuille_ptf_ptf_id_seq OWNED BY public.portefeuille_PTF.PTF_id;

------------------------------------------------------------
-- 2. TABLE : PRODUIT FINANCIER (Actifs : Actions, ETF...)
------------------------------------------------------------
CREATE SEQUENCE public.produit_financier_pdt_pdt_id_seq;

CREATE TABLE public.produit_financier_PDT (
    PDT_id INTEGER NOT NULL DEFAULT nextval('public.produit_financier_pdt_pdt_id_seq'),
    PDT_nom_produit VARCHAR(100) NOT NULL,
    PDT_ticker VARCHAR(20),
    PDT_cash BOOLEAN NOT NULL,
    PDT_est_actif BOOLEAN NOT NULL,
    PTF_id INTEGER NOT NULL,
    CONSTRAINT pdt_id PRIMARY KEY (PDT_id)
);

ALTER SEQUENCE public.produit_financier_pdt_pdt_id_seq OWNED BY public.produit_financier_PDT.PDT_id;

------------------------------------------------------------
-- 3. TABLE : COTATION (Historique des prix / Valeurs)
------------------------------------------------------------
CREATE SEQUENCE public.cotation_cot_cot_id_seq;

CREATE TABLE public.cotation_COT (
    COT_id INTEGER NOT NULL DEFAULT nextval('public.cotation_cot_cot_id_seq'),
    COT_date DATE NOT NULL,
    COT_prix NUMERIC(10,6) NOT NULL,
    PDT_id INTEGER NOT NULL,
    CONSTRAINT cot_id PRIMARY KEY (COT_id)
);

ALTER SEQUENCE public.cotation_cot_cot_id_seq OWNED BY public.cotation_COT.COT_id;

------------------------------------------------------------
-- 4. TABLE : MOUVEMENT (Flux : Achats, Ventes, Frais)
------------------------------------------------------------
CREATE SEQUENCE public.mouvement_mvt_mvt_id_seq;

CREATE TABLE public.mouvement_MVT (
    MVT_id INTEGER NOT NULL DEFAULT nextval('public.mouvement_mvt_mvt_id_seq'),
    PDT_id INTEGER NOT NULL,
    MVT_date DATE NOT NULL,
    mvt_prix DECIMAL(8, 4) NOT NULL,
    MVT_nb_parts NUMERIC(15,6) NOT NULL,
    MVT_frais NUMERIC(5,2) DEFAULT 0 NOT NULL,
    MVT_type_mouvement VARCHAR(20) NOT NULL,
    CONSTRAINT mvt_id PRIMARY KEY (MVT_id)
);

ALTER SEQUENCE public.mouvement_mvt_mvt_id_seq OWNED BY public.mouvement_MVT.MVT_id;

------------------------------------------------------------
-- 5. CONTRAINTES DE CLÉS ÉTRANGÈRES (Relations)
------------------------------------------------------------

-- Relie le Produit à son Portefeuille
ALTER TABLE public.produit_financier_PDT ADD CONSTRAINT portefeuille_pdt_financier_fk
FOREIGN KEY (PTF_id) REFERENCES public.portefeuille_PTF (PTF_id)
ON DELETE RESTRICT ON UPDATE NO ACTION;

-- Relie le Mouvement au Produit
ALTER TABLE public.mouvement_MVT ADD CONSTRAINT pdt_financier_mouvements_fk
FOREIGN KEY (PDT_id) REFERENCES public.produit_financier_PDT (PDT_id)
ON DELETE NO ACTION ON UPDATE NO ACTION;

-- Relie la Cotation au Produit
ALTER TABLE public.cotation_COT ADD CONSTRAINT pdt_financier_cotation_fk
FOREIGN KEY (PDT_id) REFERENCES public.produit_financier_PDT (PDT_id)
ON DELETE RESTRICT ON UPDATE NO ACTION;

------------------------------------------------------------
-- 6. INDEX DE PERFORMANCE (Optimisation requêtes & Power BI)
------------------------------------------------------------

-- Index sur les Clés Étrangères (Accélère les jointures JOIN)
CREATE INDEX idx_pdt_ptf_id ON public.produit_financier_PDT(PTF_id);
CREATE INDEX idx_mvt_pdt_id ON public.mouvement_MVT(PDT_id);
CREATE INDEX idx_cot_pdt_id ON public.cotation_COT(PDT_id);

-- Index sur les Dates (Accélère les filtres temporels et graphiques)
CREATE INDEX idx_mvt_date ON public.mouvement_MVT(MVT_date);
CREATE INDEX idx_cot_date ON public.cotation_COT(COT_date);

------------------------------------------------------------
-- 7. CONTRAINTES D'UNICITE SPECIFIQUES
------------------------------------------------------------

-- Empêche d'avoir deux fois le même livret dans la même banque
ALTER TABLE public.portefeuille_PTF 
ADD CONSTRAINT unique_banque_enveloppe UNIQUE (PTF_nom_banque, PTF_type_enveloppe);

-- Empêche d'avoir deux fois le même ticker dans le même portefeuille
ALTER TABLE public.produit_financier_PDT 
ADD CONSTRAINT unique_ticker_par_ptf UNIQUE (PTF_id, PDT_ticker);

-- Une seule ligne de prix par produit pour une date donnée
ALTER TABLE public.cotation_COT 
ADD CONSTRAINT unique_cotation_par_jour UNIQUE (PDT_id, COT_date);

-- Empêche d'avoir des prix ou des quantités négatives
ALTER TABLE public.cotation_COT ADD CONSTRAINT check_prix_positif CHECK (COT_prix > 0);

ALTER TABLE public.mouvement_MVT ADD CONSTRAINT check_parts_non_null CHECK (MVT_nb_parts <> 0);

-- Sécurité sur les types de mouvements autorisés
ALTER TABLE mouvement_mvt 
ADD CONSTRAINT check_type_mvt 
CHECK (mvt_type_mouvement IN ('ACHAT', 'VENTE', 'DIVIDENDE', 'APPORT', 'RETRAIT', 'ABONDEMENT', 'INTERET', 'AJUSTEMENT'));

-- Empêche d'avoir deux fois la même cotation d'un produit pour un même jour
ALTER TABLE public.cotation_cot 
ADD CONSTRAINT unique_cotation UNIQUE (pdt_id, cot_date);






-- Creation des portefeuilles

insert into public.portefeuille_ptf (ptf_nom_banque, ptf_type_enveloppe, ptf_est_actif)
values
	('BoursoBank', 'PEA', true),
	('Trade Republic', 'CTO', true),
	('STEF', 'PEE', true),
	('CiC', 'PEE', true);

-- Création des porduits financiers

insert into public.produit_financier_pdt (pdt_nom_produit, pdt_ticker, pdt_cash, pdt_est_actif, ptf_id)
values
	('S&P 500', 'ESE.PA', false, true,
	(select ptf_id
	from public.portefeuille_ptf
	where ptf_nom_banque = 'BoursoBank')),
	
	('ETF GOLD', 'SGLD.DE', false, true,
	(select ptf_id
	from public.portefeuille_ptf
	where ptf_nom_banque = 'Trade Republic')),
	
	('Action STEF', 'STEF_PEE', false, true,
	(select ptf_id
	from public.portefeuille_ptf
	where ptf_nom_banque = 'STEF')),
	
	('Obligation CiC', 'CiC_OBGL', false, true,
	(select ptf_id
	from public.portefeuille_ptf
	where ptf_nom_banque = 'CiC')),
	
	('Equilibre CiC', 'CiC_EQUI', false, true,
	(select ptf_id
	from public.portefeuille_ptf
	where ptf_nom_banque = 'CiC')),
	
	('Stratégie CiC', 'CiC_STRAT', false, true,
	(select ptf_id
	from public.portefeuille_ptf
	where ptf_nom_banque = 'CiC')),
	
	('Cash Bourso', 'CASH_BOURSO', true, true,
	(select ptf_id
	from public.portefeuille_ptf
	where ptf_nom_banque = 'BoursoBank')),
	
	('Cash Trade Rep', 'CASH_TR', true, true,
	(select ptf_id
	from public.portefeuille_ptf
	where ptf_nom_banque = 'Trade Republic')),
	
insert into public.portefeuille_ptf (ptf_nom_banque, ptf_type_enveloppe, ptf_est_actif)
values
	('Caisse d''Epargne', 'Livrets', true);
	

insert into public.produit_financier_pdt (pdt_nom_produit, pdt_ticker, pdt_cash, pdt_est_actif, ptf_id)
values
	('Livret A', null, true, true,
	(select ptf_id
	from public.portefeuille_ptf
	where ptf_nom_banque = 'Caisse d''Epargne')),
	('LEP', null, true, true,
	(select ptf_id
	from public.portefeuille_ptf
	where ptf_nom_banque = 'Caisse d''Epargne'));
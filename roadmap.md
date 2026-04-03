# 🚀 ROADMAP : Personal Finance Tracker

### 🧰 0. Socle
- [x] **ETL** : scripts `update_price.py` et `update_pee.py` opérationnels
- [x] **Vues SQL** : toutes les vues métier créées (view_global_portefeuille, view_historique_*, view_apports_*, etc.)
- [x] **Page Saisie** : formulaire de saisie manuelle mensuel

### 🏠 1. Homepage
- [x] **KPI Globaux**
- [x] **Intégration du tableau**
- [x] **Slider** : sélection de période actif
- [x] **Refacto complète de Home.py** : diviser la partie logique (calculs) et la partie graphique (affichage)
- [x] **Graphiques** : progression globale + Match "Perf Réelle" vs "Injections"

### 📊 2. Page Dashboards
- [x] **Dash ETF** (regroupe PEA + CTO)
- [x] **Dash PEA**
- [x] **Dash CTO**
- [x] **Dash STEF**
- [x] **Dash CiC** (vue globale + vue détaillée 3 fonds)

### 🔧 3. Modifications
- [x] **Déplacer le bouton MAJ PEE** vers la page Saisie
- [x] **KPI Perf Globale** ajouté sur la page KPIs

### 🔐 4. Sécurité & Cloud
- [x] **Gestion des Secrets** : `st.secrets` & `config.py` non publics
- [ ] **API** : FastAPI ⏳
- [ ] **Migration Cloud** : PostgreSQL local → Supabase ⏳
- [ ] **Authentification** : login pour sécuriser l'accès en ligne ⏳
- [ ] **BDD Fake** : fake data à des fins de présentation ⏳

### 💡 5. Autres idées
- [ ] **Projection à 10 ans** (intérêts composés basés sur la perf réelle) ⏳

### 🤖 6. Vision Futur (ML - 2027+)
- [ ] **Prédiction de trajectoire** : Forecasting via Prophet ou ARIMA ⏳
- [ ] **Optimisation d'allocation** : Modèle de Markowitz (Risk/Reward) ⏳

### 🚨 7. Bugs Mineurs
- [ ] **Graph dashboards** : premier mois sans data `NaN sur diff` ⏳
# 🚀 ROADMAP : Personal Finance Tracker

### 🏠 1. Homepage
- [x] Intégration du tableau
- [x] Rendre le slider de sélection de période actif
- [x] **Refacto complète de Home.py** : diviser la partie logique (calculs) et la partie graphique (affichage)
- [x] **Graphiques** : progression globale + Match "Perf Réelle" vs "Injections"

### 📊 2. Page Dashboards
- [x] **Dash ETF** (regroupe PEA + CTO)
- [x] **Dash PEA**
- [x] **Dash CTO**
- [x] **Dash STEF**
- [x] **Dash CiC** (vue globale + vue détaillée 3 fonds)
- [ ] **Graph dashboards** : premier mois sans data (NaN sur diff) ⏳
- [ ] **Refacto** `st_logic.py` : remplacer toutes les fonctions `ptf` par des fonctions `pdt` plus souples ⏳

### 🔧 3. Modifications
- [x] **Déplacer le bouton MAJ PEE** vers la page Saisie
- [x] **KPI Perf Globale** ajouté sur la page KPIs

### 🔐 4. Sécurité & Cloud
- [x] Choix de la techno BDD (PostgreSQL)
- [x] Gestion des Secrets (`st.secrets` & `config.py` non publics)
- [ ] **Migration Cloud** : PostgreSQL local → Supabase ⏳
- [ ] **Authentification** : login pour sécuriser l'accès en ligne ⏳
- [ ] **BDD Fake** : fake data à des fins de présentation ⏳

### 💡 5. Autres idées
- [ ] **Projection à 10 ans** (intérêts composés basés sur la perf réelle) ⏳
- [ ] **Virements Automatiques** : création d'une ligne le 2 du mois pour PEA et CTO ⏳

### 🤖 6. Vision Futur (ML - 2027+)
- [ ] **Prédiction de trajectoire** : Forecasting via Prophet ou ARIMA ⏳
- [ ] **Optimisation d'allocation** : Modèle de Markowitz (Risk/Reward) ⏳
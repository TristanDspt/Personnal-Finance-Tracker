# 🚀 ROADMAP : Personnal Finance Tracker

### 🏠 1. Homepage
- ~~integration du tableau~~ ✅
- ~~rendre le slider de selection de période actif~~ ✅
- **Refacto complète de Home.py** : diviser la partie logique (calculs) et la partie graphique (affichage) 🚨 **URGENT**
- ~~**Graphiques** : progression globale (comparé à l'attendu : similaire à celui d'excel) + le Match "Perf Réelle" vs "Injections" ?~~ ✅
- **DCA Automatique** : création d'une ligne le 16 du mois (hors week-end -et JF ?) dans la DB ⏳

### 📊 2. Page Dashboards
- **dash ETF** (qui regroupe les deux ETF) ?? ⏳
- **dash PEA** ⏳
- **dash CTO** ⏳
- **dash Stef** ⏳
- **dash CiC** (quid du détails des 3 enveloppes ?) ⏳

### 📈 3. Page Historique
- **Historique des cours** : Pour chaque placements actif. ⏳

### 🔐 4. Sécurité & Cloud
- ~~Choix de la techno BDD (PostgreSQL)~~ ✅
- ~~Gestion des Secrets (st.secrets & config.py non publics)~~ ✅
- **Migration Cloud** : Passer de l'instance PostgreSQL locale à une instance hébergée (Supabase/Neon). ⏳
- **Authentification** : Ajouter un login pour sécuriser l'accès en ligne. ⏳
- **Login et MDP** : Ajouter une page de connection ⏳

### 💡 5. Autres idées à venir
- **Projection à 10 ans** (intérêts composés basés sur la perf réelle). ⏳
- **Export PDF/CSV** pour backup. ⏳

### 🤖 6. Vision Futur (ML - 2027+)
- **Prédiction de trajectoire** : Forecasting via Prophet ou ARIMA. ⏳
- **Optimisation d'allocation** : Modèle de Markowitz (Risk/Reward). ⏳

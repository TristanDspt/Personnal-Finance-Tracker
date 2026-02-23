# 🚀 ROADMAP : Portfolio Finance Tracker

### 🏠 1. Homepage
- ~~integration du tableau~~ ✅
- ~~rendre le slider de selection de période actif~~ ✅
- **Refacto complète de Home.py** : diviser la partie logique (calculs) et la partie graphique (affichage) 🚨 **URGENT**
- **graphiques** : progression globale (comparé à l'attendu : similaire à celui d'excel) + idée à trouver ou non ? ⏳

### 📊 2. Page Dashboards
*Utiliser st.radio pour selectionner les differents dashboards ? ou plusieurs pages ?*
- **dash ETF** (qui regroupe les deux ETF) ?? ⏳
- **dash PEA** ⏳
- **dash CTO** ⏳
- **dash Stef** ⏳
- **dash CiC** (quid du détails des 3 enveloppes ?) ⏳

### 🔐 3. Sécurité & Cloud
- ~~Choix de la techno BDD (PostgreSQL)~~ ✅
- ~~Gestion des Secrets (st.secrets & config.py non publics)~~ ✅
- **Migration Cloud** : Passer de l'instance PostgreSQL locale à une instance hébergée (Supabase/Neon). ⏳
- **Authentification** : Ajouter un login pour sécuriser l'accès en ligne. ⏳

### 💡 4. Autres idées à venir
- **Projection à 10 ans** (intérêts composés basés sur la perf réelle).
- **Export PDF/CSV** pour backup.

### 🤖 5. Vision Futur (ML - 2027+)
- **Prédiction de trajectoire** : Forecasting via Prophet ou ARIMA. ⏳
- **Optimisation d'allocation** : Modèle de Markowitz (Risk/Reward). ⏳

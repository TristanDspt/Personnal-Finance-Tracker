# 🚀 ROADMAP : Personnal Finance Tracker

### 🏠 1. Homepage
- ~~integration du tableau~~ ✅
- ~~rendre le slider de selection de période actif~~ ✅
- ~~**Refacto complète de Home.py** : diviser la partie logique (calculs) et la partie graphique (affichage)~~ ✅ 
- ~~**Graphiques** : progression globale (comparé à l'attendu : similaire à celui d'excel) + le Match "Perf Réelle" vs "Injections" ?~~ ✅

### 📊 2. Page Dashboards
- **Idées graphiques** : Waterfall (perf / perf totale) / (capital / captital total). Hors livrets ? ⏳
- **dash ETF** (qui regroupe les deux ETF) ? ⏳
- **dash PEA** ⏳
- **dash CTO** ⏳
- **dash Stef** ⏳
- **dash CiC** (quid du détails des 3 enveloppes ?) ⏳

### 🔐 3. Sécurité & Cloud
- ~~Choix de la techno BDD (PostgreSQL)~~ ✅
- ~~Gestion des Secrets (st.secrets & config.py non publics)~~ ✅
- **API** : Dev API pour les appels en base. ⏳
- **Migration Cloud** : Passer de l'instance PostgreSQL locale à une instance hébergée (Supabase). ⏳
- **Authentification** : Ajouter un login pour sécuriser l'accès en ligne. ⏳
- **Login et MDP** : Ajouter une page de connection. ⏳
- **BDD Fake** : Ajoute de fake data à des fins de présentation. ⏳

### 💡 4. Autres idées à venir
- **Compartif des placements** : Pour mettre dos à dos les perfs ? ⏳
- **Page Bourse** : Page dédiée uniquement aux perf des produits boursier, nécéssite refonte graphique complete de la home page. (evolution de la perf marchés ?) ⏳
- **Historique des cours** : 📈 Pour chaque placements actif. (full groupé ou radio ?) ⏳
- **Projection à 10 ans** (intérêts composés basés sur la perf réelle). ⏳
- **Virements Automatiques** : création d'une ligne le 2 du mois pour le PEA et le CTO dans la DB. ⏳

### 🤖 5. Vision Futur (ML - 2027+)
- **Prédiction de trajectoire** : Forecasting via Prophet ou ARIMA. ⏳
- **Optimisation d'allocation** : Modèle de Markowitz (Risk/Reward). ⏳

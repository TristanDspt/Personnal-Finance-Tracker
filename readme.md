# 🏛️ Personal Finance Tracker

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-local-green)

Migration d'une gestion financière complexe (anciennement sous Excel) vers une architecture **Python / PostgreSQL / Streamlit**.  
L'outil centralise des actifs variés (ETF, Actions, PEE, Livrets) et automatise le suivi de performance avec calcul du TRI.

---

## 🚀 Vue d'ensemble

L'objectif est de transformer un suivi manuel fastidieux en une application autonome capable de :
- Centraliser des sources de données hétérogènes
- Automatiser la récupération des cours boursiers
- Offrir une interface de saisie comptable rigoureuse
- Visualiser la performance globale et l'allocation d'actifs en temps réel

---

## 🛠 Stack Technique

| Composant | Technologie | Usage |
| :--- | :--- | :--- |
| **Langage** | Python 3.x | ETL, logique métier |
| **Base de données** | PostgreSQL | Stockage relationnel + Vues calculées |
| **Interface** | Streamlit | Dashboard + formulaires de saisie |
| **DataViz** | Plotly | Graphiques dynamiques |
| **Gestion DB** | DBeaver | Administration et requêtage SQL |
| **Data Sources** | yfinance / CSV / Excel | Cours boursiers + historiques fonds |
| **Performance** | pyxirr (XIRR) | Calcul du TRI annualisé |

---

## 💡 Fonctionnalités

### 1. Ingestion & Automatisation (ETL)
- **Automatique :** Script Python via `yfinance` pour les actifs boursiers
- **Semi-automatique :** Parsing Excel/CSV pour les fonds PEE (STEF, CiC)
- **Incrémentation logique :** Comparaison des dates en base pour n'importer que les nouvelles cotations
- **MAJ manuelle PEE :** Bouton dans la sidebar déclenche `update_pee.py` via subprocess

### 2. Intelligence SQL (Business Logic)
La logique financière est déportée au maximum dans des **Vues SQL** :
- **Calcul du PRU :** Prix de revient unitaire intégrant les frais de courtage
- **Gestion de l'abondement :** Distinction effort perso / abondement employeur pour un ROI précis
- **Vue globale :** Synthèse instantanée capital, profit €/%, dernière cotation par produit
- **Vue historique :** Reconstitution quotidienne du patrimoine (base de tous les graphiques)

### 3. Dashboard Home
- KPIs globaux : Patrimoine total, Performance Marchés, TRI annualisé (hors livrets)
- 3 Donuts : répartition ETF / PEE / Livrets avec poids %
- Journal de bord réactif au slider : perf par enveloppe sur la période
- Tableau mensuel avec coloration conditionnelle + toggle 12 mois roulants
- Graphique capital vs apports (masqué sur les courtes périodes)

### 4. Dashboards par Enveloppe
Chaque enveloppe dispose d'un dashboard dédié avec KPIs, TRI, capital net fiscal, journal de bord période :

| Dashboard | Enveloppe | Contenu |
| :--- | :--- | :--- |
| ETF | PEA + CTO agrégés | Perf S&P500 + Gold, TRI |
| PEA | BoursoBank PEA | Capital net (18.6%), TRI, cours High/Low |
| CTO | BoursoBank CTO | Capital net (31.4%), TRI, cours High/Low |
| STEF | PEE STEF | Abondement, capital net (18.6%), cours action |
| CiC | PEE CiC | 3 fonds (Oblig/Equi/Strat), TRI par fonds |

### 5. Application de Saisie
- Formulaire de saisie des mouvements (Achat, Vente, Apport, Retrait, Abondement)
- **Opérations miroir :** un achat ETF déduit automatiquement le montant de la poche cash broker

---

## 🏗 Architecture du Code

```
PostgreSQL (Vues SQL)
        ↓
scripts/database.py   ← connexion + chargement des vues
        ↓
   st_logic.py        ← calculs, transformations pandas (zéro Streamlit)
   st_charts.py       ← figures Plotly (zéro Streamlit)
        ↓
     Home.py          ← interface principale
   pages/Dashboards   ← dashboards par enveloppe
   pages/Saisie       ← formulaire de saisie
```

Voir `ARCHITECTURE.md` pour le détail complet des fonctions et des ordres d'appel.

---

## 🏗 Schéma SQL

| Table | Contenu |
| :--- | :--- |
| `portefeuille_PTF` | Enveloppes (PEA, CTO, STEF, CiC, Livrets) |
| `produit_financier_PDT` | Actifs individuels (ETF, actions, fonds, cash) |
| `mouvement_MVT` | Flux (Achats, Ventes, Apports, Abondements) |
| `cotation_COT` | Historique des prix |

Contraintes : clés étrangères, unicité Ticker/Date, checks Prix > 0.

---

## 📝 Conventions de Saisie

### Types de mouvements (`mvt_type_mouvement`)

| Type | Usage |
| :--- | :--- |
| `APPORT` | Dépôt cash sur poche broker OU versement PEE |
| `RETRAIT` | Retrait cash réel |
| `RETRAIT_MIROIR` | Débit automatique poche cash lors d'un achat ETF |
| `ABONDEMENT` | Prime employeur PEE (hors effort perso) |
| `ACHAT` | Achat ETF/Action sur PEA ou CTO uniquement |
| `VENTE` | Vente ETF/Action |

> ⚠️ Les versements PEE doivent être saisis en `APPORT` (pas `ACHAT`) pour être correctement comptabilisés dans le calcul de la Performance Marchés.

---

## ⚙️ Installation & Setup

1. Cloner le repo
2. Créer et activer un venv : `python -m venv pft_env`
3. Installer les dépendances : `pip install -r requirements.txt`
4. Initialiser la DB : `psql -f SQL/schema/Create_DB_PFT.sql`
5. Créer le fichier `config.py` à la racine (voir section Sécurité)
6. Créer `.streamlit/secrets.toml` (voir section Sécurité)
7. Lancer l'application : `streamlit run Home.py`

---

## 🔒 Sécurité & Configuration

Deux fichiers à créer manuellement (exclus du repo via `.gitignore`) :

**`config.py`** (utilisé par les scripts ETL) :
```python
DB_HOST     = "localhost"
DB_PORT     = "5432"
DB_NAME     = "nom_de_la_db"
DB_USER     = "votre_user"
DB_PASSWORD = "votre_password"
```

**`.streamlit/secrets.toml`** (utilisé par l'app Streamlit) :
```toml
[postgres]
host     = "localhost"
port     = "5432"
database = "nom_de_la_db"
user     = "votre_user"
password = "votre_password"

venv_python = "C:/path/to/venv/Scripts/python.exe"
```

---

## 📁 Structure du Projet

```
├── Home.py                    ← Page principale Streamlit
├── pages/
│   ├── 1_📊_Dashboards.py    ← Dashboards par enveloppe
│   └── 2_✍️_Saisie.py        ← Formulaire de saisie
├── scripts/
│   ├── database.py            ← Connexion PostgreSQL + chargement vues
│   ├── st_logic.py            ← Logique métier (calculs pandas)
│   ├── st_charts.py           ← Figures Plotly
│   └── update_pee.py          ← ETL mise à jour fonds PEE
├── SQL/
│   └── schema/                ← Scripts de création DB
├── ARCHITECTURE.md            ← Documentation technique détaillée
├── roadmap.md                 ← Roadmap et backlog
└── requirements.txt
```

---

*Projet personnel développé dans le cadre d'une reconversion Data Analyst / Dev IA.*
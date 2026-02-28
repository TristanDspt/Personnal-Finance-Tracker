# 🏛️ Personal Finance Tracker

Projet de migration d'une gestion financière complexe (anciennement sous Excel) vers une architecture robuste **Python / PostgreSQL / Streamlit**. 
L'outil centralise des actifs variés (Actions, ETF, PEE, Livrets) et automatise le suivi de performance.

## 🚀 Vision du Projet
L'objectif est de transformer un suivi manuel fastidieux en une application autonome capable de :
* Centraliser des sources de données hétérogènes.
* Automatiser la récupération des cours boursiers.
* Offrir une interface de saisie comptable rigoureuse.
* Visualiser la performance globale et l'allocation d'actifs en temps réel.

## 🛠 Stack Technique
| Composant | Technologie | Usage |
| :--- | :--- | :--- |
| **Langage** | Python 3.x | ETL, logique métier et backend |
| **Base de données** | PostgreSQL | Stockage relationnel et Vues calculées |
| **Interface (UI)** | Streamlit | Dashboard interactif et formulaires de saisie |
| **DataViz** | Plotly | Graphiques dynamiques et indicateurs de performance |
| **Gestion DB** | DBeaver | Administration et requêtage SQL |
| **Data Sources** | yfinance / CSV / Excel | Extraction des cours et historiques fonds (CIC, STEF) |

## 💡 Fonctionnalités Clés

### 1. Ingestion & Automatisation (ETL)
* **Automatique :** Script Python utilisant l'API `yfinance` pour les actifs boursiers.
* **Semi-Automatique :** Parsing intelligent de fichiers Excel/CSV pour les fonds d'entreprise (STEF, CIC).
* **Incrémentation Logique :** Le script compare les dates en base de données pour n'importer que les nouvelles cotations (évite les doublons).
* **Orchestration :** Automatisation via fichiers `.bat` et le **Planificateur de tâches Windows** pour une mise à jour quotidienne sans intervention.

### 2. Intelligence SQL (Business Logic)
La logique financière est déportée au maximum dans des **Vues SQL complexes** pour garantir la performance :
* **Calcul du PRU :** Intégration des frais de courtage et calcul du prix de revient moyen pondéré.
* **Gestion de l'Abondement :** Distinction entre l'effort d'épargne réel et les abondements employeurs pour un calcul de ROI précis.
* **Super Vue Global :** Synthèse instantanée du capital, du profit (euro/%) et de la dernière mise à jour des cours.

### 3. Interface Utilisateur (Streamlit)
* **Dashboard Home :** Visualisation de l'allocation d'actifs (Donut Charts) et des KPIs principaux (Patrimoine total, Performance par enveloppe).
* **Application de Saisie :** Interface dédiée avec **gestion des opérations miroirs** (l'achat d'un titre déduit automatiquement le montant net de la poche cash correspondante).
* **Calculateur de Frais :** Moteur dynamique calculant les frais de courtage selon la banque (ex: paliers BoursoBank).

## 🏗 Architecture du Schéma SQL
La base est normalisée pour garantir l'intégrité des données financières :
* `portefeuille_PTF` : Contenants (PEA, Livret A, CTO...).
* `produit_financier_PDT` : Actifs individuels.
* `mouvement_MVT` : Flux (Achats, Ventes, Dividendes, Apports).
* `cotation_COT` : Historique des prix.
* **Contraintes :** Utilisation stricte de clés étrangères, de contraintes d'unicité (Ticker/Date) et de checks de validité (Prix > 0).

## 📝 Conventions de saisie

### Types de mouvements (`mvt_type_mouvement`)
| Type | Usage |
| :--- | :--- |
| `APPORT` | Dépôt cash sur livret/poche broker OU versement sur PEE |
| `RETRAIT` | Retrait cash réel (livret, sortie d'argent) |
| `RETRAIT_MIROIR` | Débit automatique poche cash lors d'un achat ETF (généré automatiquement) |
| `ABONDEMENT` | Prime employeur sur PEE (ne compte pas comme effort perso) |
| `ACHAT` | Achat ETF/Action sur PEA ou CTO uniquement |
| `VENTE` | Vente ETF/Action |

### ⚠️ Ajout d'un nouveau PEE
Les versements PEE doivent être saisis en `APPORT` (pas `ACHAT`) pour être correctement comptabilisés dans le calcul de la Perf Marchés.

## ⚙️ Installation & Setup
1. Cloner le repo.
2. initialiser la DB : `psql -f sql/schema/Create_DB_PFT.sql`.
3. Installer les dépendances : `pip install -r requirements.txt`.
4. Configurer le fichier `.streamlit/secrets.toml` avec les accès PostgreSQL.
5. Configurer le fichier `config.py` avec les accès PostgreSQL.
6. Lancer l'application : `streamlit run home.py`.

## 🔒 Sécurité & Configuration
Le projet utilise un fichier `.gitignore` pour protéger les données sensibles. 
Pour faire fonctionner l'application, vous devez créer :
1. Un fichier `config.py` à la racine pour les paramètres locaux.
2. Un dossier `.streamlit/` contenant un fichier `secrets.toml` avec vos identifiants PostgreSQL :
   ```toml
   [postgres]
   host = "localhost"
   port = "5432"
   database = "nom_de_la_db"
   user = "votre_user"
   password = "votre_password"

## 📈 État d'avancement
- [x] Backend Python & Fetching API
- [x] Modélisation de la base de données (PostgreSQL)
- [x] Application Streamlit : Formulaires de saisie manuelle
- [ ] Application Streamlit : Dashboard de DataViz (En cours)
- [ ] Pages dédiées PEA / CTO / PEE(s)

## ⚙️ Configuration
- **OS :** Windows 10/11
- **IDE :** VS Code
- **Gestion DB :** DBeaver

---
*Projet développé par Tristan dans le cadre d'une reconversion Data Analyst / Dev IA.*

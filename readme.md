# 🏛️ Personal Finance Tracker

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-local-green)

Migration d'une gestion financière complexe (anciennement sous Excel) vers une architecture **Python / PostgreSQL / Streamlit**.  
L'outil centralise des actifs variés (ETF, Actions, PEE, Livrets) et automatise le suivi de performance avec calcul du TRI.

---

## 🛠 Stack Technique

| Composant | Technologie |
| :--- | :--- |
| **Langage** | Python 3.x |
| **Base de données** | PostgreSQL |
| **Interface** | Streamlit |
| **DataViz** | Plotly |
| **Performance** | pyxirr (XIRR) |
| **Data Sources** | yfinance / CSV / Excel |

---

## ⚙️ Installation & Setup

1. Cloner le repo
2. Créer et activer un venv : `python -m venv pft_env`
3. Installer les dépendances : `pip install -r requirements.txt`
4. Initialiser la DB : `psql -f sql/schema/Create_DB_PFT.sql`
5. Créer `scripts/config.py` et `.streamlit/secrets.toml` (voir `ARCHITECTURE.md`)
6. Lancer l'application : `streamlit run dashboard/app.py`

---

## 📚 Documentation

Voir [`ARCHITECTURE.md`](ARCHITECTURE.md) pour le détail complet : structure des fichiers, fonctions, vues SQL, conventions.

---

*Projet personnel développé dans le cadre d'une reconversion Data Analyst / Dev IA.*

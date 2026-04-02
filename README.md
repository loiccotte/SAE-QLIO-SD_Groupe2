# T'ELEFAN MES 4.0

Tableau de bord industriel pour le pilotage d'une ligne de production semi-automatisee FESTO CP Factory.

Projet SAE BUT3 QLIO Science des Donnees.

## Prerequis

- [Python 3.10+](https://www.python.org/downloads/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (pour MariaDB)

## Lancement rapide

```bash
# Option 1 : Docker (MariaDB + app)
docker compose up --build

# Option 2 : Local (SQLite)
pip install -r requirements.txt
flask run
```

L'application est accessible sur http://localhost:5000.

## Comptes

| Identifiant | Mot de passe | Role | Droits |
|-------------|-------------|------|--------|
| admin | admin123 | admin | Dashboard, export, config BDD |
| responsable | resp123 | responsable | Dashboard, export |
| operateur | oper123 | employe | Dashboard uniquement |

Les mots de passe sont haches avec scrypt (werkzeug.security).

## Architecture

```
SAE-QLIO-SD/
├── app/
│   ├── __init__.py              # Factory Flask, init BDD, gestion erreurs
│   ├── auth.py                  # Login/logout, RBAC, hachage mots de passe
│   ├── config.py                # Seuils, IDs machines, constantes
│   ├── models.py                # 10 modeles ORM (tables MES4)
│   ├── export.py                # Export PDF et Excel
│   ├── routes/
│   │   ├── dashboard.py         # Dashboard, API JSON, acces donnees CSV
│   │   ├── kpi_pages.py         # Pages detail (perf, qualite, delai, ...)
│   │   └── admin.py             # Config BDD, import SQL, conversion MySQL->SQLite
│   └── services/
│       ├── _helpers.py          # Decorateur safe_kpi, filtre temporel, durees machines
│       ├── performance.py       # OEE, utilisation, cadence, temps de cycle
│       ├── quality.py           # Non-conformite, temps de detection
│       ├── delay.py             # Lead time, temps d'attente buffer
│       ├── energy.py            # Consommation electrique et air comprime
│       └── stock.py             # Occupation buffers, variation stock
├── templates/
│   ├── base.html                # Layout : header, sidebar, auto-refresh 5min
│   ├── components/
│   │   ├── sidebar.html         # Navigation KPI + filtre temporel + user
│   │   └── time_filter.html     # Filtres annee/mois (sidebar)
│   ├── login.html, 404.html     # Pages standalone
│   ├── dashboard.html           # 5 cartes KPI cliquables
│   ├── performance.html         # OEE gauge, utilisation par machine/mois
│   ├── qualite.html             # Non-conformite, detection defauts
│   ├── delai.html               # Lead time, attente buffer
│   ├── energie.html             # Timeline conso, jauges air comprime
│   ├── stock.html               # Jauges buffers, variation stock
│   ├── carte.html               # Plan interactif ligne FESTO (Leaflet)
│   └── config_bdd.html          # Config BDD, drag & drop import SQL
├── scripts/
│   └── sanitize-sql.sh          # Nettoyage octets nuls avant import MariaDB
├── tests/                       # 61 tests (pytest)
├── data/mes4.db                 # Base SQLite locale (convertie depuis le dump)
├── docker-compose.yml           # MariaDB + Adminer + Flask
└── FestoMES-2026-03-31.sql      # Dump HeidiSQL de la ligne FESTO
```

## Conformite Cahier des Charges

| Exigence CDC | Status | Implementation |
|---|---|---|
| 1. Login avec mot de passe hache | OK | `auth.py` : scrypt via werkzeug |
| 2. Deconnexion + bouton logout | OK | Sidebar + bouton mobile |
| 3. Page 404 personnalisee | OK | `templates/404.html` |
| 4. Acces donnees sources via URL | OK | `/api/donnees` (liste) + `/api/donnees/<table>` (CSV) |
| 5. Minimum 5 pages web | OK | 8 pages : dashboard, performance, qualite, delai, energie, stock, carte, config |
| 6. Carte geographique avec indicateurs | OK | `carte.html` : plan Leaflet de la ligne FESTO |
| 7. Filtre plage de temps sur chaque page | OK | Sidebar : annee/mois, filtre toutes les pages KPI |
| Bandeau gauche (sidebar) | OK | Navigation KPI, filtres, infos utilisateur |
| Bandeau haut (header) | OK | Logo, refresh, export, config BDD, logout |
| Tableau de bord central | OK | Cartes KPI cliquables + graphiques Plotly |

## KPIs (12 indicateurs)

| # | Indicateur | Formule | Source BDD |
|---|---|---|---|
| 1 | OEE | Dispo x Perf x Qualite (NF E60-182) | tblmachinereport, tblfinstep, tblfinorderpos, tblfinorder |
| 2 | Utilisation machine | AutomaticMode / temps session | tblmachinereport |
| 3 | Cadence | Pieces / heures Busy | tblfinorderpos, tblmachinereport |
| 4 | Temps de cycle | AVG(End-Start) etapes prod | tblfinstep (OpNo < 200) |
| 5 | Non-conformite | Erreurs / total | tblfinorderpos, tblpartsreport |
| 6 | Detection defaut | Delta erreur -> arret | tblmachinereport (fronts ErrorL0/L2) |
| 7 | Lead Time | AVG(End-Start) par OF | tblfinorder |
| 8 | Attente buffer | AVG(End-Start) OpNo 210-215 | tblfinstep |
| 9 | Energie electrique | ElectricEnergyCalc / piece | tblfinstep (mWs -> Wh) |
| 10 | Air comprime | CompressedAirCalc / piece | tblfinstep (mNl -> L) |
| 11 | Occupation buffers | Positions PNo>0 / capacite | tblbuffer, tblbufferpos |
| 12 | Variation stock | Delta quantites par buffer | tblbufferpos |

## Stack technique

- **Backend :** Flask 3.x, SQLAlchemy, Jinja2
- **Frontend :** Tailwind CSS (CDN), Plotly.js, Leaflet.js, police Outfit
- **BDD :** MariaDB 10.6 (Docker) / SQLite (local, import drag & drop)
- **Tests :** pytest (61 tests, SQLite in-memory)
- **Export :** openpyxl (Excel), weasyprint (PDF)

## API

| Endpoint | Description |
|---|---|
| `/api/kpis` | KPIs calcules (JSON) |
| `/api/donnees` | Liste des tables avec lien CSV |
| `/api/donnees/<table>` | Export CSV d'une table brute |
| `/export/excel` | Rapport KPI Excel |
| `/export/pdf` | Rapport KPI PDF |

## Tests

```bash
python -m pytest tests/ -v
```

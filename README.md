# T'ELEFAN MES 4.0

Tableau de bord industriel pour le pilotage d'une ligne de production semi-automatisee FESTO (12 machines, fabrication de smartphones).

Projet SAE BUT3 Science des Donnees - Groupe 2.

## Prerequis

- Docker & Docker Compose
- Navigateur Chrome / Edge (recommande)

## Installation et lancement

```bash
git clone <url-du-repo>
cd SAE-QLIO-SD
cp .env.example .env
docker-compose up --build
```

## Acces

| Service | URL | Identifiants |
|---------|-----|-------------|
| Application Flask | http://localhost:5000 | Voir comptes ci-dessous |
| phpMyAdmin | http://localhost:8080 | example_user / example_password |

### Comptes de test

| Identifiant | Mot de passe | Role | Acces export |
|-------------|-------------|------|-------------|
| admin | admin123 | admin | Oui |
| responsable | resp123 | responsable | Oui |
| operateur | oper123 | employe | Non |

## Architecture technique

```
SAE-QLIO-SD/
├── app/
│   ├── __init__.py          # Flask factory, config, retry BDD, handler 404
│   ├── models.py            # 10 modeles SQLAlchemy (tables MES4)
│   ├── services.py          # 11 fonctions de calcul KPI + helpers
│   ├── routes.py            # 8 routes (dashboard, 5 detail, API, index)
│   ├── auth.py              # Auth hardcodee, login_required, role_required
│   └── export.py            # Export PDF et Excel des KPIs
├── templates/
│   ├── base.html            # Layout commun (header, timer, export, breadcrumbs)
│   ├── login.html           # Page de connexion (standalone)
│   ├── dashboard.html       # Dashboard global (5 cards KPI cliquables)
│   ├── performance.html     # Detail Performance (OEE, utilisation, cadence, cycle)
│   ├── qualite.html         # Detail Qualite (non-conformite, detection)
│   ├── delai.html           # Detail Delai (lead time scatter, buffer wait)
│   ├── energie.html         # Detail Energie (consommation timeline, air gauge)
│   ├── stock.html           # Detail Stock (occupation buffers, variation)
│   └── 404.html             # Page d'erreur personnalisee (standalone)
├── static/css/custom.css    # Couleurs KPI, animations, responsive Plotly
├── tests/
│   ├── conftest.py          # Fixtures (app test SQLite, seed data, clients)
│   ├── test_services.py     # Tests unitaires des 11 fonctions KPI
│   ├── test_routes.py       # Tests fonctionnels (protection, rendu, RBAC export)
│   └── test_auth.py         # Tests auth (login, logout, roles)
├── ressources/              # SQL init, maquettes, CDC, schema BDD
├── instructions/            # Prompts sprint, design system
├── docker-compose.yml       # 3 services : MariaDB + phpMyAdmin + Flask
├── Dockerfile               # Python 3.10-slim
├── requirements.txt         # Dependances Python
└── .env.example             # Variables d'environnement
```

## KPIs implementes (12)

| # | KPI | Methode de calcul | Source |
|---|-----|-------------------|--------|
| 1 | OEE (Taux de Rendement Global) | Disponibilite x Performance x Qualite | tblmachinereport, tblfinstep, tblfinorderpos |
| 2 | Taux d'utilisation machine | Busy / Total par machine | tblmachinereport |
| 3 | Cadence reelle | Pieces finies / duree production | tblfinorderpos |
| 4 | Temps moyen de cycle | AVG(End - Start) etapes productives | tblfinstep |
| 5 | Taux de non-conformite | Pieces erreur / total | tblfinorderpos, tblpartsreport |
| 6 | Temps de detection defaut | Delta erreur -> arret machine | tblmachinereport |
| 7 | Lead Time | End - Start par ordre | tblfinorder |
| 8 | Temps d'attente en buffer | AVG(End - Start) OpNo 210-215 | tblfinstep |
| 9-10 | Consommation energetique | Valeurs theoriques (ElectricEnergy, CompressedAir) | tblresourceoperation |
| 11 | Taux d'occupation buffers | Positions occupees / capacite | tblbuffer, tblbufferpos |
| 12 | Variation niveau de stock | Delta Quantity par buffer | tblbufferpos |

## Stack technique

- **Backend :** Flask 3.x + SQLAlchemy + Jinja2
- **Frontend :** Tailwind CSS (CDN) + Plotly.js (CDN) + police Geist
- **Base de donnees :** MariaDB 10.6 (schema MES4, 64 tables, lecture seule)
- **Infrastructure :** Docker Compose (3 services)
- **Export :** openpyxl (Excel), weasyprint (PDF)
- **Tests :** pytest + pytest-flask

## Lancement des tests

```bash
pip install pytest pytest-flask
pytest tests/ -v
```

## Problemes connus et limitations

1. Les donnees energetiques reelles sont a 0 dans la BDD (ElectricEnergyReal, CompressedAirReal) - valeurs theoriques utilisees en fallback
2. Les codes erreur 5050 et 99 dans tblpartsreport ne sont pas references dans tblerrorcodes
3. Les donnees couvrent 2016-2025 (sessions de test) - toutes les periodes sont agregees
4. L'export PDF utilise weasyprint ; en cas d'erreur d'installation, un fallback HTML est genere
5. Les comptes utilisateurs sont hardcodes (pas de table BDD)

# Architecture technique — T'ELEFAN MES 4.0

## Vue d'ensemble

L'application est un dashboard web Flask qui lit les donnees de production
d'une ligne FESTO MES 4.0 et affiche 12 indicateurs de performance (KPIs).

```
Navigateur  →  Flask (routes/)  →  services/ (calcul KPIs)  →  SQLAlchemy  →  MariaDB ou SQLite
                    ↓
             templates Jinja2 + Tailwind CSS + Plotly.js + Leaflet.js
```

## Design Patterns utilises

### 1. Service Layer Pattern
Les calculs KPI sont separes dans `app/services/` en 6 modules :

| Module | Responsabilite | Fonctions |
|--------|---------------|-----------|
| `performance.py` | OEE, utilisation, cadence, cycle | `calculate_oee()`, `calculate_utilization()`, ... |
| `quality.py` | Non-conformite, detection defauts | `calculate_non_conformity()`, `calculate_detection_time()` |
| `delay.py` | Lead time, attente buffer | `calculate_lead_time()`, `calculate_buffer_wait_time()` |
| `energy.py` | Consommation electrique/air | `calculate_energy_summary()` |
| `stock.py` | Occupation buffers, variation | `calculate_buffer_occupancy()`, `calculate_stock_variation()` |
| `_helpers.py` | Utilitaires partages | `safe_kpi()`, `build_time_filter()`, `get_machine_durations()` |

Chaque fonction accepte `year` et `month` optionnels pour le filtre temporel.
Le decorateur `@safe_kpi` capture les exceptions pour ne pas planter toute la page.

### 2. Blueprint modulaire
Les routes sont organisees en 3 modules partageant le meme Blueprint `main` :

| Module | Routes | Role |
|--------|--------|------|
| `dashboard.py` | `/`, `/dashboard`, `/api/kpis`, `/api/donnees` | Page principale + API |
| `kpi_pages.py` | `/performance`, `/qualite`, `/delai`, `/energie`, `/stock`, `/carte` | Pages detail KPI |
| `admin.py` | `/config-bdd`, `/import-bdd` | Administration BDD |

### 3. Template Composition
Le layout utilise l'heritage Jinja2 :
```
base.html (header + sidebar + footer)
├── components/sidebar.html (navigation + filtre temporel)
├── components/time_filter.html (selects annee/mois)
└── [page].html (contenu specifique)
```

## Flux de donnees

```
1. Utilisateur selectionne une plage (annee/mois) dans la sidebar
2. Le formulaire soumet en GET : /performance?year=2024&month=10
3. La route recupere year/month via _get_time_filter()
4. Les services filtrent les requetes SQL avec build_time_filter()
5. Les resultats sont passes au template Jinja2
6. Plotly.js genere les graphiques cote client
```

## Base de donnees

### Connexion
L'app supporte deux modes :
- **MariaDB** (Docker) : `DATABASE_URL=mysql+pymysql://user:pass@db:3306/mes4`
- **SQLite** (local) : `DATABASE_URL=sqlite:///data/mes4.db`

Le switch est dynamique (pas besoin de redemarrer) grace a `_apply_db_connection()`
qui dispose l'ancien engine SQLAlchemy et en cree un nouveau.

### Import drag & drop
L'import de fichiers SQL (HeidiSQL / mysqldump) passe par :
1. `_sanitize_sql_file()` : supprime les octets nuls
2. `_convert_mysql_to_sqlite()` : filtre les commandes MySQL incompatibles,
   adapte les types, gere les INSERT multi-lignes

### Tables utilisees (10 sur 64)

| Modele ORM | Table BDD | Utilise par |
|-----------|-----------|-------------|
| `Order` | `tblfinorder` | Lead time, OEE |
| `OrderPosition` | `tblfinorderpos` | Qualite, cadence, OEE |
| `Step` | `tblfinstep` | Cycle time, buffer wait, energie, OEE |
| `MachineReport` | `tblmachinereport` | Disponibilite, utilisation, detection |
| `PartsReport` | `tblpartsreport` | Non-conformite |
| `Buffer` | `tblbuffer` | Occupation, variation stock |
| `BufferPosition` | `tblbufferpos` | Occupation, variation stock |

## Securite

- Mots de passe haches avec scrypt (`werkzeug.security`)
- Sessions Flask signees (`SECRET_KEY`)
- RBAC : 3 roles (admin, responsable, employe) avec `@role_required`
- Protection CSRF sur les formulaires d'import
- Validation des noms de table dans l'API CSV (anti-injection SQL)

## Tests

61 tests pytest couvrant :
- Services KPI (calculs avec donnees de test)
- Routes (auth, protection, rendu)
- Auth (login, logout, roles, hachage)

Execution : `python -m pytest tests/ -v`

## Deploiement

### Docker (production)
```bash
docker compose up --build
```
3 services : MariaDB + Adminer + Flask.
Le `sanitize-sql.sh` nettoie les dumps avant import.

### Local (developpement)
```bash
pip install -r requirements.txt
flask run
```
Utilise SQLite (`data/mes4.db`) genere depuis le dump SQL.

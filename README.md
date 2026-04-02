# T'ELEFAN MES 4.0

Tableau de bord industriel pour le pilotage d'une ligne de production semi-automatisee FESTO CP Factory.

Projet SAE BUT3 QLIO Science des Donnees.

---

## Prerequis

- [Python 3.10+](https://www.python.org/downloads/) (cocher **"Add Python to PATH"** lors de l'installation)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (uniquement pour la methode Docker)

---

## Methode 1 — Local avec SQLite (sans Docker)

Cette methode utilise une base SQLite deja incluse dans le projet (`data/mes4.db`).
Aucune installation de Docker n'est necessaire.

### Etape 1 — Cloner le projet

```bash
git clone <url-du-depot>
cd SAE-QLIO-SD
```

### Etape 2 — Creer et activer l'environnement virtuel

```bash
python -m venv venv
```

Activer le venv :

- **Windows (cmd)** : `venv\Scripts\activate`
- **Windows (PowerShell)** : `venv\Scripts\Activate.ps1`
- **Windows (Git Bash)** : `source venv/Scripts/activate`
- **Linux / macOS** : `source venv/bin/activate`

Le prefixe `(venv)` doit apparaitre dans le terminal. **Toutes les commandes suivantes supposent le venv actif.**

### Etape 3 — Installer les dependances

```bash
pip install -r requirements.txt
```

> **Note weasyprint (export PDF) :** Sur Windows, `weasyprint` necessite GTK3.
> Si l'installation echoue, ce n'est **pas bloquant** : l'export PDF bascule automatiquement en HTML.
> Pour activer le PDF natif : installer GTK3 depuis https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

### Etape 4 — Configurer le fichier .env

Copier le fichier d'exemple :

```bash
cp .env.example .env
```

Puis **modifier** la ligne `DATABASE_URL` dans `.env` pour pointer vers SQLite :

```env
DATABASE_URL=sqlite:///data/mes4.db
```

Le fichier `.env` complet doit ressembler a :

```env
DATABASE_URL=sqlite:///data/mes4.db
SECRET_KEY=exemple-secret-key-2025
FLASK_APP=app.run:app
FLASK_DEBUG=1
```

### Etape 5 — Lancer l'application

```bash
flask run
```

L'application est accessible sur **http://localhost:5000**.

### Etape 6 — Se connecter

Voir la section [Comptes](#comptes) ci-dessous.

---

## Methode 2 — Docker (MariaDB + Flask)

Cette methode lance **tout dans Docker** : MariaDB, Adminer et l'application Flask.
Le dump SQL (`FestoMES-2026-03-31.sql`) est importe automatiquement au premier demarrage.

### Etape 1 — Cloner le projet

```bash
git clone <url-du-depot>
cd SAE-QLIO-SD
```

### Etape 2 — Verifier que Docker Desktop est demarre

```bash
docker info
```

Si cette commande affiche une erreur, ouvrir Docker Desktop et attendre que l'icone baleine apparaisse dans la barre des taches.

### Etape 3 — Configurer le fichier .env

Copier le fichier d'exemple :

```bash
cp .env.example .env
```

Puis **modifier** la ligne `DATABASE_URL` dans `.env` pour pointer vers le conteneur Docker :

```env
DATABASE_URL=mysql+pymysql://example_user:example_password@db:3306/mes4
```

Le fichier `.env` complet doit ressembler a :

```env
DATABASE_URL=mysql+pymysql://example_user:example_password@db:3306/mes4
SECRET_KEY=exemple-secret-key-2025
FLASK_APP=app.run:app
FLASK_DEBUG=1
```

> **Important :** l'hote est bien `db` (nom du service Docker), pas `localhost`.

### Etape 4 — Construire et lancer les conteneurs

```bash
docker compose up --build
```

Au premier lancement :
- Docker telecharge les images MariaDB et Python (~500 Mo au total)
- Le dump SQL est importe automatiquement dans MariaDB (peut prendre 1-2 minutes)
- L'application Flask attend que MariaDB soit pret avant de demarrer (retries automatiques)

Attendre le message suivant dans les logs :

```
app-1  |  * Running on http://127.0.0.1:5000
```

### Etape 5 — Acceder a l'application

| Service | URL |
|---------|-----|
| Application Flask | http://localhost:5000 |
| Adminer (interface BDD) | http://localhost:8081 |

### Etape 6 — Se connecter

Voir la section [Comptes](#comptes) ci-dessous.

### Arreter les conteneurs

- **Arreter** : `CTRL+C` dans le terminal ou `docker compose stop`
- **Arreter et supprimer les conteneurs** : `docker compose down`
- **Arreter et supprimer les donnees MariaDB** : `docker compose down -v`

---

## Comptes

| Identifiant | Mot de passe | Role | Droits |
|-------------|-------------|------|--------|
| admin | admin123 | admin | Dashboard, export, config BDD |
| responsable | resp123 | responsable | Dashboard, export |
| operateur | oper123 | employe | Dashboard uniquement |

Les mots de passe sont haches avec scrypt (werkzeug.security).

---

## Tests

Les tests utilisent une base SQLite en memoire. **Docker n'est pas necessaire.**

```bash
python -m pytest tests/ -v
```

---

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
│   ├── convert_to_sqlite.py     # Conversion dump MySQL -> SQLite
│   └── sanitize-sql.sh          # Nettoyage octets nuls avant import MariaDB
├── tests/                       # 61 tests (pytest)
├── data/mes4.db                 # Base SQLite locale (convertie depuis le dump)
├── docker-compose.yml           # MariaDB + Adminer + Flask
├── Dockerfile                   # Image Docker de l'application Flask
├── .env.example                 # Modele de configuration (a copier en .env)
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

## Resolution des problemes

### "Can't connect to MySQL server"

- **Methode SQLite :** verifier que `DATABASE_URL` dans `.env` commence par `sqlite:///`
- **Methode Docker :** verifier que les conteneurs tournent (`docker compose ps`) et que `DATABASE_URL` utilise `@db:3306`

### L'application boucle au demarrage (retries BDD)

L'app tente 10 connexions espacees de 5 secondes. En methode Docker, MariaDB peut prendre 30-60 secondes pour s'initialiser au premier lancement (import du dump SQL). Patienter.

### Erreur "Access denied for user"

Supprimer les volumes Docker et relancer :

```bash
docker compose down -v
docker compose up --build
```

### weasyprint : erreur a l'export PDF

Ce n'est pas bloquant : l'application exporte en HTML si weasyprint n'est pas fonctionnel.
Pour activer le PDF natif sur Windows : installer GTK3 depuis https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

### Les tests echouent

Les tests n'utilisent ni Docker ni MariaDB. Verifier que le venv est actif et que les dependances sont installees :

```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

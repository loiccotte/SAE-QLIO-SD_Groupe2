# Prompt Scrum Master - Sprint 3 : Livraison Finale T'ELEFAN MES 4.0

## Contexte

Tu es Scrum Master sur le projet SAE MES 4.0 (T'ELEFAN), un tableau de bord industriel Flask pour piloter une ligne de production semi-automatisee FESTO (12 machines, fabrication de smartphones).

**Deadline : semaine 14, mars 2026.**

### Documents de reference

| Document | Chemin | Contenu |
|----------|--------|---------|
| Analyse projet | `ANALYSE_PROJET.md` | 12 KPIs, mapping SQL, problemes donnees |
| Mapping KPI-SQL | `Correspondance_KPI_sql.md` | Tables et colonnes par KPI |
| Maquette UI | `ressources/.../Maquette_Groupe2.pdf` | 8 pages de maquettes (login, dashboard, 5 details, 404) |
| Design system | `instructions/SKILL.md` | Regles UI/UX (adapte Flask/Jinja2 : ignorer React/Framer Motion) |
| Schema BDD | `ressources/schema_BDD.pdf` | Diagramme de la base |
| CDC client | `ressources/CDC_MES4.0_V2.pdf` | Cahier des charges complet |

---

## Ce qui a ete livre (Sprint 2 - Beta MVP)

L'application beta est fonctionnelle avec :

### Backend (app/)

**`__init__.py`** (23 lignes) :
- Flask factory avec SQLAlchemy + SECRET_KEY + 2 blueprints (main, auth)
- Configuration via .env (DATABASE_URL, FLASK_APP, FLASK_DEBUG)

**`models.py`** (144 lignes) :
10 modeles SQLAlchemy mappant les tables MES4 :

| Modele | Table | Lignes BDD | Role |
|--------|-------|------------|------|
| `Order` | tblfinorder | 189 | Ordres de fabrication |
| `OrderPosition` | tblfinorderpos | 411 | Pieces produites par ordre |
| `Step` | tblfinstep | 1 460 | Etapes de production terminees |
| `MachineReport` | tblmachinereport | 10 126 | Etats machine horodates (event-driven) |
| `ResourceOperation` | tblresourceoperation | 142 | Temps nominaux machine/operation |
| `Resource` | tblresource | 12 | Machines de la ligne |
| `PartsReport` | tblpartsreport | 1 191 | Detection pieces + erreurs |
| `Buffer` | tblbuffer | 10 | Zones de stockage |
| `BufferPosition` | tblbufferpos | 77 | Positions dans les buffers |
| `ErrorCode` | tblerrorcodes | 4 | Codes erreur de reference |

**`services.py`** (496 lignes) :
9 fonctions de calcul KPI implementees + 2 helpers :

| Fonction | KPI | Retourne |
|----------|-----|----------|
| `_get_machine_durations()` | Helper | DataFrame pandas des durees event-driven |
| `_get_resource_names()` | Helper | Dict ResourceID -> nom machine |
| `calculate_oee()` | KPI 1 : OEE | value, availability, performance, quality, status |
| `calculate_utilization()` | KPI 2 : Taux utilisation | overall, by_machine[], status |
| `calculate_throughput()` | KPI 3 : Cadence reelle | value (pieces/h), monthly[], status |
| `calculate_cycle_time()` | KPI 4 : Temps cycle | value (secondes), count, status |
| `calculate_non_conformity()` | KPI 5 : Non-conformite | value (%), rate_orders, rate_parts, by_machine[], status |
| `calculate_detection_time()` | KPI 6 : Detection defaut | value (secondes), by_event[], count, status |
| `calculate_lead_time()` | KPI 7 : Lead Time | value (heures), distribution[], count, status |
| `calculate_energy_summary()` | KPI 9-10 : Energie | value (Wh/u), air_value (L/u), status, note |
| `calculate_buffer_occupancy()` | KPI 11 : Occupation buffers | value (%), by_buffer[], status |

**FONCTIONS MANQUANTES :**
- `calculate_buffer_wait_time()` - KPI 8 : Temps d'attente en buffer
- `calculate_stock_variation()` - KPI 12 : Variation du niveau de stock
- Enrichissement de `calculate_energy_summary()` avec courbe temporelle
- Enrichissement de `calculate_lead_time()` (distribution deja presente, verifier format scatter)

**`auth.py`** (62 lignes) :
- 3 users hardcodes : `admin` (admin123, role admin), `responsable` (resp123, role responsable), `operateur` (oper123, role employe)
- Decorateur `@login_required` verifie `session['user']`
- Routes : `/login` (GET/POST), `/logout`
- Roles stockes en session mais **pas encore utilises pour RBAC**

**`routes.py`** (63 lignes) :
5 routes existantes :

| Route | Methode | Protection | Template |
|-------|---------|------------|----------|
| `/` | GET | Non | Redirect -> /login |
| `/dashboard` | GET | @login_required | dashboard.html |
| `/performance` | GET | @login_required | performance.html |
| `/qualite` | GET | @login_required | qualite.html |
| `/api/kpis` | GET | @login_required | JSON endpoint |

**ROUTES MANQUANTES :**
- `GET /delai` -> delai.html
- `GET /energie` -> energie.html
- `GET /stock` -> stock.html
- Export endpoints (PDF/Excel)
- Handler 404

### Frontend (templates/)

| Template | Lignes | Etat |
|----------|--------|------|
| `base.html` | 117 | OK - Header sticky (Actualiser + timer 5min + logo + logout), Tailwind CDN, Plotly.js CDN, Geist font, auto-refresh |
| `login.html` | 106 | OK - Standalone, formulaire identifiant/mot_de_passe |
| `dashboard.html` | 154 | OK - 5 cards KPI en grid (3+2), alertes visuelles, **mais cards Delai/Energie/Stock non cliquables** |
| `performance.html` | 212 | OK - 4 graphiques Plotly (gauge OEE, barres utilisation, courbe cadence, valeur cycle time) |
| `qualite.html` | 170 | OK - 2 graphiques Plotly (gauge non-conformite, barres detection defaut) |

**TEMPLATES MANQUANTS :**
- `delai.html` (page detail Delai)
- `energie.html` (page detail Energie)
- `stock.html` (page detail Stock)
- `404.html` (page erreur)

### Styling

**`static/css/custom.css`** (35 lignes) :
- 5 classes couleur : `.kpi-bar-perf` (#ff0000), `.kpi-bar-qualite` (#38b6ff), `.kpi-bar-delai` (#f2c0ff), `.kpi-bar-energie` (#09b200), `.kpi-bar-stock` (#737373)
- Animation alert-blink (opacity 1->0.2, 1.5s)
- Transitions hover/active sur les cards
- Fix responsive Plotly 100% width

**Tailwind config** (dans base.html) :
Couleurs custom : perf, qualite, delai, energie, stock. Font family : Geist + Geist Mono.

### Infrastructure

**`docker-compose.yml`** : 3 services (MariaDB 10.6 + phpMyAdmin + Flask)
**`Dockerfile`** : Python 3.10-slim
**`.env`** : DATABASE_URL, SECRET_KEY, FLASK_APP, FLASK_DEBUG
**`requirements.txt`** : flask, flask-sqlalchemy, pymysql, python-dotenv, pandas, plotly

### Problemes connus de la beta

1. L'app Flask peut crasher si la BDD n'est pas encore prete au premier demarrage (race condition malgre healthcheck)
2. Les donnees energie sont theoriques (ElectricEnergyReal = 0 partout dans la BDD) - fallback sur tblresourceoperation
3. Les 3 pages detail Delai, Energie, Stock ne sont pas implementees (cards non cliquables)
4. Pas de gestion d'erreur propre si une requete KPI echoue
5. Pas de tests
6. Pas de page 404
7. RBAC non implemente (les 3 roles ont acces a tout)
8. Le bouton EXPORTER dans le header est un placeholder vide (block header_actions)
9. CompressedAirReal = 0 partout (meme probleme que energie)
10. Codes erreur 5050 et 99 dans tblpartsreport n'existent pas dans tblerrorcodes

---

## Sprint 3 - Backlog (Livraison Finale, mars 2026)

---

### PRIORITE 1 : Pages detail manquantes (3 pages)

Implementer les 3 pages detail restantes en suivant **strictement** la maquette `Maquette_Groupe2.pdf` (pages 5, 6, 7).

Chaque page doit :
- Heriter de `base.html` ({% extends "base.html" %})
- Avoir un bloc breadcrumbs : `Accueil > NOM_PAGE`
- Afficher 2 graphiques Plotly cote a cote dans une grille 2 colonnes
- Avoir la barre de couleur de sa categorie en haut de chaque carte graphique
- Respecter le style des pages performance.html et qualite.html existantes
- `displayModeBar: false` sur tous les graphiques Plotly

---

#### Page DELAI (delai.html) - Couleur rose #f2c0ff

**Maquette page 5 :** 2 graphiques en grille 50/50

**Graphique gauche : Lead Time (scatter plot)**
- Type : nuage de points (scatter)
- Axe X : index temporel des ordres (ou timestamp Start)
- Axe Y : duree en heures (0h a 6h)
- Points : couleur rose #f2c0ff (ou variante plus saturee pour visibilite)
- Ligne horizontale "Threshold" en pointilles a 3h (seuil alerte : lead time > nominal x 1.1)
- Donnees : utiliser `calculate_lead_time()['distribution']` qui contient deja `{order, hours, start}`

**Graphique droit : Temps d'attente en buffer (courbe temporelle)**
- Type : ligne (scatter mode='lines')
- Axe X : index temporel
- Axe Y : duree en secondes (0 a 350s)
- Zone d'alerte : rectangle rose semi-transparent au-dessus du seuil (ex: > 300s, zone > nominal x 1.2)
- Annotation "Alert" visible dans la zone
- Donnees : **nouvelle fonction** `calculate_buffer_wait_time()`

**Sous les graphiques :**
- Resume textuel : Lead Time moyen, nombre d'ordres, temps buffer moyen

**Route :** `GET /delai`

**Service a creer - `calculate_buffer_wait_time()` (KPI 8) :**
```python
# Source : tblfinstep
# Filtre : OpNo entre 210 et 215 (operations buffer = stockage/destockage)
# Calcul : AVG(End - Start) pour ces etapes
# Retourne : {
#   'value': float (secondes),
#   'by_event': [{'timestamp': str, 'seconds': float, 'op': int}],
#   'count': int,
#   'status': 'warning' si > seuil
# }
```

---

#### Page ENERGIE (energie.html) - Couleur vert #09b200

**Maquette page 6 :** 2 graphiques en grille (plus large a gauche, ~60/40)

**Graphique gauche : Consommation energetique (courbe temporelle)**
- Type : ligne avec points (scatter mode='lines+markers')
- Axe X : horodatage (heures)
- Axe Y : consommation kWh (0 a 80)
- Couleur : vert #09b200
- Donnees : consommation energetique agrege par periode temporelle
- Note : utiliser valeurs theoriques `tblresourceoperation.ElectricEnergy` car les donnees reelles = 0

**Graphique droit : Consommation Air comprime (jauge)**
- Type : indicator (gauge)
- Plage : 0 a valeur max
- Zones de couleur : vert (normal) / rouge (hors tolerance +/-15%)
- Aiguille pointant vers la valeur actuelle
- Donnees : `calculate_energy_summary()['air_value']`

**Sous les graphiques :**
- Note explicative : "Valeurs theoriques (capteurs reels indisponibles)"
- Resume : kWh/unite, L air/unite

**Route :** `GET /energie`

**Enrichir `calculate_energy_summary()` :**
Ajouter un champ `timeline` avec la consommation agrege par periode :
```python
# Ajouter au retour :
# 'timeline': [{'period': str, 'kwh': float}]
# Agreger par heure ou par session de production
```

---

#### Page STOCK (stock.html) - Couleur gris #737373

**Maquette page 7 :** 2 graphiques en grille (plus large a gauche, ~60/40)

**Graphique gauche : Taux d'occupation des buffers (bar chart)**
- Type : barres verticales (bar)
- 1 barre par buffer
- Axe Y : pourcentage (0% a 100%)
- Couleur : gris #737373 par defaut, **rouge #ff0000 si taux > 90%**
- Annotation ">90%" sur les barres en alerte
- Donnees : `calculate_buffer_occupancy()['by_buffer']` contient deja `{name, capacity, occupied, rate}`

**Graphique droit : Variation du niveau de stock (bar chart)**
- Type : barres verticales (bar)
- Axe Y : pourcentage de variation (0% a 10%)
- Couleur : gris #737373
- Donnees : **nouvelle fonction** `calculate_stock_variation()`

**Sous les graphiques :**
- Resume : taux occupation global, nombre de buffers, alerte si > 90%

**Route :** `GET /stock`

**Service a creer - `calculate_stock_variation()` (KPI 12) :**
```python
# Source : tblbufferpos
# Calcul : Delta Quantity entre observations successives par buffer
# Retourne : {
#   'variations': [{'buffer': str, 'variation_pct': float}],
#   'max_variation': float,
#   'status': 'warning' si variation > 20%
# }
```

---

#### Modifications associees

**`routes.py`** - Ajouter 3 routes :
```python
@bp.route('/delai')
@login_required
def delai():
    lead_time = services.calculate_lead_time()
    buffer_wait = services.calculate_buffer_wait_time()
    return render_template('delai.html', lead_time=lead_time, buffer_wait=buffer_wait)

@bp.route('/energie')
@login_required
def energie():
    energy = services.calculate_energy_summary()
    return render_template('energie.html', energy=energy)

@bp.route('/stock')
@login_required
def stock():
    buffer_occ = services.calculate_buffer_occupancy()
    stock_var = services.calculate_stock_variation()
    return render_template('stock.html', buffer_occ=buffer_occ, stock_var=stock_var)
```

**`dashboard.html`** - Rendre les 3 cards restantes cliquables :
- Remplacer les `<div class="kpi-card ... opacity-90">` par des `<a href="{{ url_for('main.delai') }}">`
- Idem pour Energie et Stock
- Retirer le `opacity-90`

---

### PRIORITE 2 : Export PDF/Excel

Ajouter la fonctionnalite d'export demandee dans le CDC.

**Bouton EXPORTER :**
- Le block `{% block header_actions %}` dans base.html est prevu pour ca
- Afficher un bouton "Exporter" qui ouvre un dropdown/modal avec :
  - Choix du format : PDF ou Excel
  - Filtres temporels hierarchiques : Annee > Mois > Jour > Heure
  - Bouton de confirmation

**Export PDF :**
- Generer un rapport PDF contenant les KPIs actuels avec graphiques
- Library suggeree : `weasyprint` (pur Python, pas de dependance wkhtmltopdf)
- Alternative : `pdfkit` avec wkhtmltopdf
- Inclure les graphiques sous forme d'images statiques (Plotly peut exporter en base64)

**Export Excel :**
- Generer un fichier .xlsx avec les donnees brutes des KPIs
- Library : `openpyxl`
- Un onglet par categorie (Performance, Qualite, Delai, Energie, Stock)
- Inclure les filtres temporels appliques en en-tete

**Routes :**
```python
@bp.route('/export/pdf')
@login_required
def export_pdf():
    # Parametres : ?year=&month=&day=&hour=
    ...

@bp.route('/export/excel')
@login_required
def export_excel():
    # Parametres : ?year=&month=&day=&hour=
    ...
```

**Ajouter dans requirements.txt :** `weasyprint` (ou `pdfkit`), `openpyxl`

---

### PRIORITE 3 : Robustesse et gestion d'erreurs

**3.1 Try/except dans services.py :**
Entourer chaque fonction KPI d'un try/except qui retourne des valeurs par defaut si la BDD est inaccessible ou si une requete echoue. Pattern :
```python
def calculate_xxx():
    try:
        # ... calcul existant ...
    except Exception as e:
        print(f"Erreur KPI xxx: {e}")
        return {'value': 0, 'status': 'error', 'error': str(e)}
```

**3.2 Page 404 personnalisee :**
Maquette page 8 : pingouin avec casque de chantier.
- Template `templates/404.html`
- Centre : illustration pingouin (SVG inline ou image)
- Texte : "ERREUR 404" (titre gras) + "PAGE INTROUVABLE" (sous-titre)
- Bouton bleu : "RETOUR A L'ACCUEIL" -> lien vers /dashboard
- Pas de header/footer (page standalone comme login.html)
- Enregistrer le handler dans `__init__.py` :
```python
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
```

**3.3 Gestion BDD non prete :**
Si la connexion BDD echoue au demarrage :
- Afficher une page "Base de donnees en cours de chargement..." avec auto-retry (JS)
- Ou implementer un retry mechanism dans `__init__.py` (boucle de tentatives avec sleep)

---

### PRIORITE 4 : RBAC (3 roles)

Actuellement les 3 users ont acces a tout. Implementer les restrictions d'acces definies dans le CDC :

| Fonctionnalite | Admin | Responsable | Employe |
|----------------|-------|-------------|---------|
| Dashboard global | Oui | Oui | Oui |
| Pages detail | Oui | Oui | Oui |
| Export PDF/Excel | Oui | Oui | Non |
| Gestion users (futur) | Oui | Non | Non |

**Implementation :**

1. Creer un decorateur `role_required(min_role)` dans `auth.py` :
```python
ROLE_HIERARCHY = {'admin': 3, 'responsable': 2, 'employe': 1}

def role_required(min_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get('role', 'employe')
            if ROLE_HIERARCHY.get(user_role, 0) < ROLE_HIERARCHY.get(min_role, 0):
                flash("Acces non autorise.", "error")
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

2. Appliquer `@role_required('responsable')` sur les routes d'export

3. Conditionner l'affichage du bouton EXPORTER dans base.html :
```jinja2
{% if session.get('role') in ['admin', 'responsable'] %}
    <!-- Bouton Exporter -->
{% endif %}
```

---

### PRIORITE 5 : Tests

**Structure :**
```
tests/
├── conftest.py          # Fixtures : app de test, client, BDD de test
├── test_services.py     # Tests unitaires des 11+ fonctions KPI
├── test_routes.py       # Tests fonctionnels des routes
└── test_auth.py         # Tests d'authentification et RBAC
```

**conftest.py :**
- Creer une app Flask de test avec SQLite en memoire (ou MariaDB de test)
- Fixture `client` pour les requetes HTTP
- Fixture `auth_client` (client connecte)
- Injecter des donnees de test minimales dans la BDD

**test_services.py :**
- Tester chaque fonction KPI avec des donnees connues
- Verifier que les retours ont la bonne structure (cles attendues)
- Tester les cas limites : BDD vide, donnees aberrantes

**test_routes.py :**
- Tester que toutes les routes protegees redirigent vers /login si non connecte
- Tester que /dashboard, /performance, /qualite, /delai, /energie, /stock retournent 200 une fois connecte
- Tester que /export/* est interdit pour role employe

**test_auth.py :**
- Tester login valide / invalide
- Tester logout
- Tester la persistence de session

**Ajouter dans requirements.txt :** `pytest`, `pytest-flask`

---

### PRIORITE 6 : Documentation technique

**README.md** complet avec :
1. Description du projet (T'ELEFAN MES 4.0, ligne FESTO)
2. Captures d'ecran des pages principales
3. Prerequis : Docker, Docker Compose, navigateur Chrome/Edge
4. Installation et lancement :
   ```bash
   git clone ...
   cp .env.example .env
   docker-compose up --build
   ```
5. Acces :
   - App : http://localhost:5000
   - phpMyAdmin : http://localhost:8080
6. Comptes de test : admin/admin123, responsable/resp123, operateur/oper123
7. Architecture technique (arbre de fichiers commente)
8. Liste des 12 KPIs avec methode de calcul
9. Stack technique : Flask, SQLAlchemy, MariaDB, Tailwind CSS, Plotly.js, Docker
10. Problemes connus et limitations

---

## Consignes techniques

### Stack imposee
- **Backend :** Flask + Jinja2 + SQLAlchemy
- **Frontend :** Tailwind CSS (CDN) + Plotly.js (CDN) + police Geist
- **BDD :** MariaDB 10.6 via Docker, schema existant (64 tables, **pas de migration**)
- **Infra :** Docker Compose (3 services)

### Regles de design
- Lire et suivre `instructions/SKILL.md` (adapte a Flask/Jinja2 : ignorer les sections React/Framer Motion/Next.js)
- Suivre la maquette `Maquette_Groupe2.pdf` pour le layout de chaque page
- **Charte couleurs KPI :**
  - Performance : rouge `#ff0000`
  - Qualite : bleu `#38b6ff`
  - Delai : rose `#f2c0ff`
  - Energie : vert `#09b200`
  - Stock : gris `#737373`
- Coins arrondis : `rounded-2xl` sur les cartes
- Pas d'emoji dans le code ou l'interface (sauf illustration 404)
- Graphiques Plotly : `displayModeBar: false`, responsive, hauteur coherente (260-340px)

### Regles de code
- Projet niveau **BUT3 Science des Donnees** : propre, professionnel, pas de sur-ingenierie
- Garder la structure existante (Flask factory, blueprints main + auth)
- Ne pas modifier le schema de la BDD (les tables MES4 sont en lecture seule)
- Nommer les templates en francais sans accents : delai.html, energie.html, stock.html
- Variables et fonctions en anglais (convention existante)
- Pas de dependances inutiles

### References KPI
- `ANALYSE_PROJET.md` section 6 : Mapping KPI -> Tables -> Colonnes (detail complet des 12 KPIs)
- `Correspondance_KPI_sql.md` : Vue synthetique du mapping
- **Problemes donnees :**
  - ElectricEnergyReal = 0 partout -> utiliser valeurs theoriques de `tblresourceoperation`
  - CompressedAirReal = 0 partout -> idem
  - Codes erreur 5050 et 99 non references -> traiter comme "erreur inconnue"
  - Donnees de 2016 a 2025 = sessions de test -> agreger tout ou filtrer periodes pertinentes

---

## Resume des livrables Sprint 3

| # | Livrable | Fichiers a creer/modifier | Priorite |
|---|----------|---------------------------|----------|
| 1 | Page detail Delai | `templates/delai.html`, `services.py` (+calculate_buffer_wait_time), `routes.py` | P1 |
| 2 | Page detail Energie | `templates/energie.html`, `services.py` (enrichir energy_summary), `routes.py` | P1 |
| 3 | Page detail Stock | `templates/stock.html`, `services.py` (+calculate_stock_variation), `routes.py` | P1 |
| 4 | Cards dashboard cliquables | `dashboard.html` | P1 |
| 5 | Export PDF | `routes.py`, nouveau module `app/export.py`, `base.html`, `requirements.txt` | P2 |
| 6 | Export Excel | idem | P2 |
| 7 | Filtres temporels export | Modal/dropdown dans `base.html` ou template dedie | P2 |
| 8 | Try/except services | `services.py` | P3 |
| 9 | Page 404 | `templates/404.html`, `__init__.py` | P3 |
| 10 | Retry BDD | `__init__.py` | P3 |
| 11 | RBAC decorateur | `auth.py` | P4 |
| 12 | RBAC templates | `base.html`, routes d'export | P4 |
| 13 | Tests unitaires | `tests/conftest.py`, `tests/test_services.py` | P5 |
| 14 | Tests fonctionnels | `tests/test_routes.py`, `tests/test_auth.py` | P5 |
| 15 | README complet | `README.md` | P6 |

---

## Commandes de demarrage

```bash
docker-compose down -v        # Reset complet (reinitialise la BDD)
docker-compose up --build     # Demarrer les 3 services
# http://localhost:5000        -> App Flask
# http://localhost:8080        -> phpMyAdmin (example_user / example_password)
```

## Commandes de test

```bash
# Depuis le conteneur app ou en local avec venv
pip install pytest pytest-flask
pytest tests/ -v
```

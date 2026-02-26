# Executable standalone — T'ELEFAN MES 4.0

**Alternative a Docker :** un `.exe` Windows autonome avec base SQLite embarquee.
Aucune installation requise (ni Python, ni Docker, ni MariaDB).

---

## Telecharger et lancer

1. Aller sur la page **Releases** du depot GitHub
2. Telecharger `TelefanMES-windows.zip` (derniere release)
3. Dezipper dans un dossier (ex: `C:\TelefanMES\`)
4. Double-cliquer sur `TelefanMES.exe`
5. Le navigateur s'ouvre automatiquement sur `http://localhost:5000`

### Comptes de connexion

| Identifiant    | Mot de passe | Role           |
|----------------|-------------|----------------|
| `admin`        | `admin123`  | Administrateur |
| `responsable`  | `resp123`   | Responsable    |
| `operateur`    | `oper123`   | Employe        |

### Arreter l'application

Fermer la fenetre console noire.

---

## Fonctionnement technique

### Structure du dossier dezippe

```
TelefanMES/
  TelefanMES.exe          <- point d'entree
  config.example.ini      <- template config (optionnel)
  _internal/              <- donnees embarquees (PyInstaller 6.x)
      templates/           <- pages HTML Jinja2
      static/              <- CSS, JS, images
      data/mes4.db         <- base SQLite (~1.2 Mo, 10 tables, ~13 600 lignes)
      [modules Python]     <- Flask, SQLAlchemy, pandas, etc.
```

### Sequence de demarrage

```
TelefanMES.exe
  │
  ├─ 1. Calcul des chemins
  │     exe_dir  = dossier contenant l'exe    (pour config.ini)
  │     data_dir = _internal/ (sys._MEIPASS)  (pour templates, static, data)
  │
  ├─ 2. Resolution base de donnees (chaine de fallback)
  │     a) Variable d'environnement DATABASE_URL     -> si definie, utilisee
  │     b) Fichier config.ini a cote de l'exe        -> si present, lu
  │     c) Base SQLite embarquee _internal/data/mes4.db  -> defaut
  │
  ├─ 3. Verification fichier SQLite existe
  │     Si absent -> message erreur + attente touche Entree
  │
  ├─ 4. Creation app Flask (create_app)
  │     - Chemins absolus templates/static via sys._MEIPASS
  │     - SQLite : pas de pool_pre_ping ni retry connexion
  │
  ├─ 5. Timer 1.5s -> ouverture navigateur
  │
  ├─ 6. Affichage banniere console
  │
  └─ 7. waitress.serve() sur port 5000 (bloquant)
        - Serveur WSGI multi-thread (production)
        - Ecoute 0.0.0.0 (accessible sur le reseau local)
```

---

## Connecter une base distante (MariaDB/MySQL)

Quand la base MariaDB sera mise en place, il suffit de creer un fichier `config.ini` **a cote de l'exe** :

```ini
[database]
url = mysql+pymysql://utilisateur:motdepasse@serveur:3306/MES4

[app]
port = 5000
```

Au prochain lancement, l'exe utilisera la base distante au lieu de SQLite.
**Aucune recompilation necessaire.**

> Le fichier `config.example.ini` fourni dans le zip sert de modele.

---

## Build automatique (CI/CD)

Le workflow GitHub Actions `.github/workflows/build-exe.yml` :

- **Declencheur :** push sur `main` ou declenchement manuel
- **Etapes :**
  1. Checkout du code
  2. Python 3.10 + pip install
  3. Conversion dump MariaDB -> SQLite (`scripts/convert_to_sqlite.py`)
  4. Build PyInstaller (`pyinstaller telefan.spec`)
  5. Creation ZIP `TelefanMES-windows.zip`
  6. Publication en GitHub Release

Chaque push sur `main` genere automatiquement une nouvelle release telechargeable.

---

## Builder l'exe en local

### Prerequis

- Python 3.10+
- Dependances : `pip install -r requirements.txt && pip install pyinstaller`

### Etapes

```cmd
:: 1. Generer la base SQLite depuis le dump MariaDB
python scripts/convert_to_sqlite.py

:: 2. Builder l'exe
pyinstaller telefan.spec --noconfirm

:: 3. Le resultat est dans dist/TelefanMES/
dist\TelefanMES\TelefanMES.exe
```

### Fichiers cles du build

| Fichier | Role |
|---------|------|
| `standalone.py` | Point d'entree de l'exe |
| `telefan.spec` | Configuration PyInstaller |
| `scripts/convert_to_sqlite.py` | Conversion dump MySQL -> SQLite |
| `config.example.ini` | Template config base distante |

---

## Conversion MariaDB -> SQLite

Le script `scripts/convert_to_sqlite.py` :

- Lit le dump SQL `ressources/FestoMES-2025-03-27.sql`
- Extrait les 10 tables utilisees par l'ORM
- Convertit la syntaxe MySQL vers SQLite (types, echappement, mots-cles)
- Produit `data/mes4.db` (~1.2 Mo)

Tables incluses : `tblfinorder`, `tblfinorderpos`, `tblfinstep`, `tblmachinereport`, `tblresourceoperation`, `tblresource`, `tblpartsreport`, `tblbuffer`, `tblbufferpos`, `tblerrorcodes`

> **Note :** Les tables MySQL ont plus de colonnes que les modeles ORM (ex: `tblresource` a 15 colonnes MySQL mais 3 dans l'ORM). Les colonnes supplementaires sont conservees dans SQLite mais ignorees par SQLAlchemy a la lecture.

---

## Depannage

### La console se ferme immediatement

L'exe inclut un `try/except` qui affiche l'erreur et attend une touche.
Si ca se ferme quand meme, lancer depuis un terminal :

```cmd
cd C:\chemin\vers\TelefanMES
TelefanMES.exe
```

L'erreur restera visible dans le terminal.

### "Base de donnees introuvable"

Le fichier `_internal/data/mes4.db` est manquant. Le zip a ete mal decompresse ou le build a echoue. Re-telecharger la release.

### Les graphiques ne s'affichent pas

Plotly.js est charge via CDN. Une connexion internet est necessaire pour les graphiques interactifs.

### Port 5000 deja utilise

Creer un `config.ini` a cote de l'exe :

```ini
[app]
port = 8080
```

# Documentation technique — Environnement de travail

**Projet :** T'ELEFAN MES 4.0
**Plateforme cible :** Windows 10 / Windows 11
**Méthode :** Python venv (application) + Docker Desktop (base de données)

---

## Architecture de déploiement

```
┌─────────────────────────────────────────────────────────┐
│  Machine locale                                          │
│                                                          │
│   Python venv          Docker Desktop                    │
│  ┌───────────┐        ┌──────────────────────────────┐  │
│  │ Flask app │──────► │ MariaDB :3306  (conteneur db) │  │
│  │ port 5000 │        │ phpMyAdmin :8080              │  │
│  └───────────┘        └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

- L'**application Flask** tourne dans un environnement virtuel Python sur la machine
- La **base de données MariaDB** tourne dans un conteneur Docker (isolation, pas d'installation manuelle)
- L'import du dump SQL est automatique au premier démarrage du conteneur

---

## Prérequis logiciels

### 1. Python 3.10 ou supérieur

Vérifier si Python est déjà installé :

```cmd
python --version
```

Si Python n'est pas installé : https://www.python.org/downloads/

> **Important :** Pendant l'installation, cocher **"Add Python to PATH"**.

### 2. Docker Desktop

Docker Desktop fournit la base de données MariaDB sans installation complexe.

Télécharger Docker Desktop : https://www.docker.com/products/docker-desktop/

> Après installation, **démarrer Docker Desktop** et attendre que l'icône baleine apparaisse dans la barre des tâches (cela peut prendre 1-2 minutes au premier lancement).

---

## Lancement (méthode simple)

**Double-cliquer sur `LANCER_APP.bat`** à la racine du projet.

Le script automatise toutes les étapes :

| Étape | Action |
|-------|--------|
| 1 | Vérifie Python |
| 2 | Crée le venv `.venv` (une seule fois) |
| 3 | Active le venv |
| 4 | Installe les dépendances pip |
| 5 | Crée le fichier `.env` depuis `.env.example` |
| 6 | Vérifie que Docker Desktop est démarré |
| 7 | Lance les conteneurs MariaDB + phpMyAdmin |
| 8 | Attend que la base de données soit prête |
| 9 | Ouvre le navigateur sur http://localhost:5000 |
| 10 | Lance Flask |

> **Première exécution :** Docker télécharge l'image MariaDB (~500 Mo). L'opération peut prendre 2-5 minutes selon la connexion internet. Les exécutions suivantes sont immédiates.

---

## Lancement manuel (méthode détaillée)

Si `LANCER_APP.bat` ne convient pas, voici les étapes manuelles.

### Étape 1 — Cloner ou récupérer le projet

```cmd
git clone <url-du-depot>
cd SAE-QLIO-SD
```

Ou décompresser l'archive ZIP dans un dossier de votre choix.

---

### Étape 2 — Créer l'environnement virtuel Python

```cmd
python -m venv .venv
```

Activer l'environnement virtuel :

```cmd
.venv\Scripts\activate
```

Le préfixe `(.venv)` doit apparaître dans le terminal. **Toutes les commandes suivantes doivent être exécutées avec ce venv activé.**

---

### Étape 3 — Installer les dépendances Python

```cmd
pip install -r requirements.txt
```

> **Cas particulier — weasyprint sur Windows :**
> `weasyprint` nécessite des bibliothèques GTK3 pour fonctionner.
> Si l'installation échoue ou si l'export PDF génère une erreur, ce n'est pas bloquant : l'application bascule automatiquement sur un export HTML.
> Pour activer le PDF natif : installer GTK3 depuis https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

---

### Étape 4 — Configurer le fichier .env

```cmd
copy .env.example .env
```

Le fichier `.env` créé contient déjà les bonnes valeurs pour Docker :

```env
DATABASE_URL=mysql+pymysql://example_user:example_password@localhost:3306/MES4
SECRET_KEY=exemple-secret-key-2025
FLASK_APP=app.run:app
FLASK_DEBUG=1
```

---

### Étape 5 — Démarrer la base de données (Docker)

```cmd
docker compose up -d db phpmyadmin
```

Cette commande :
- démarre un conteneur MariaDB sur le port `3306`
- démarre un conteneur phpMyAdmin sur le port `8080`
- **importe automatiquement** le fichier `ressources/FestoMES-2025-03-27.sql` (64 tables)

Attendre que la base soit prête (~30 secondes) :

```cmd
docker compose ps
```

Le statut du service `db` doit passer à `healthy`.

---

### Étape 6 — Lancer l'application

```cmd
flask run
```

L'application est accessible sur : **http://localhost:5000**
phpMyAdmin est accessible sur : **http://localhost:8080**

---

## Comptes de test

| Identifiant | Mot de passe | Rôle | Accès export |
|-------------|-------------|------|-------------|
| `admin` | `admin123` | Administrateur | Oui |
| `responsable` | `resp123` | Responsable | Oui |
| `operateur` | `oper123` | Employé | Non |

---

## Lancer les tests unitaires

Les tests utilisent une base SQLite en mémoire. **Docker et MariaDB ne sont pas nécessaires pour les tests.**

```cmd
pytest tests/ -v
```

Résultat attendu : tous les tests passent au vert.

---

## Arrêter l'application

- **Arrêter Flask :** `CTRL+C` dans le terminal
- **Arrêter les conteneurs Docker :** `docker compose stop`
- **Supprimer les conteneurs et les données :** `docker compose down -v` *(attention : supprime la base)*

---

## Liste complète des paquets avec versions

| Paquet | Version | Rôle |
|--------|---------|------|
| Flask | 3.0.3 | Framework web principal |
| Flask-SQLAlchemy | 3.1.1 | ORM SQLAlchemy intégré à Flask |
| PyMySQL | 1.1.1 | Connecteur Python pur pour MariaDB/MySQL |
| python-dotenv | 1.0.1 | Chargement des variables d'environnement (.env) |
| pandas | 2.2.2 | Manipulation de DataFrames (calcul des KPIs) |
| plotly | 5.22.0 | Bibliothèque de graphiques interactifs |
| openpyxl | 3.1.3 | Génération de fichiers Excel (.xlsx) |
| weasyprint | 62.3 | Conversion HTML → PDF (nécessite GTK3 sur Windows) |
| pytest | 8.2.2 | Framework de tests unitaires |
| pytest-flask | 1.3.0 | Fixtures Flask pour pytest |

---

## Résolution des problèmes courants

### Docker Desktop ne démarre pas

- Vérifier que la virtualisation est activée dans le BIOS (VT-x / AMD-V)
- Sur Windows 10 : vérifier que WSL 2 est installé (`wsl --install` dans PowerShell admin)
- Redémarrer le PC après installation de Docker Desktop

### L'application ne démarre pas : "Can't connect to MySQL server"

- Vérifier que les conteneurs Docker sont démarrés : `docker compose ps`
- Si le statut est `starting` : attendre encore 30 secondes et réessayer
- Vérifier que `DATABASE_URL` dans `.env` utilise bien `@localhost:3306` et non `@db:3306`

### Erreur "Access denied for user 'example_user'"

- La base de données n'a peut-être pas fini de s'initialiser : attendre 1 minute et réessayer
- Supprimer le volume et recommencer : `docker compose down -v` puis relancer `LANCER_APP.bat`

### Page blanche ou erreur SQLAlchemy au démarrage

- Vérifier que l'import SQL s'est bien effectué : ouvrir http://localhost:8080 et vérifier que la base `MES4` contient 64 tables
- Vérifier `FLASK_DEBUG=1` dans `.env` pour voir les erreurs détaillées

### weasyprint : erreur à l'export PDF

- Ce n'est pas bloquant : l'application exporte en HTML si weasyprint n'est pas fonctionnel
- Pour résoudre : installer GTK3 pour Windows (lien dans l'étape 3)

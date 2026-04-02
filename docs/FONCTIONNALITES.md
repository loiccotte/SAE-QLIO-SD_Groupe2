# Documentation technique — Fonctionnalités de la WebApp

**Projet :** T'ELEFAN MES 4.0
**Description :** Tableau de bord industriel pour le pilotage d'une ligne de production FESTO semi-automatisée (fabrication de smartphones, 12 machines, données MES réelles)

---

## Vue d'ensemble

L'application est un dashboard web à usage interne. Elle permet à différents profils (opérateur, responsable, administrateur) de consulter en temps réel les indicateurs de performance de la ligne de production. Toutes les données proviennent d'une base MariaDB en **lecture seule** — l'application n'écrit jamais dans la base.

### Architecture

```
Navigateur  →  Flask (routes/)  →  services/ (calcul KPIs)  →  SQLAlchemy  →  MariaDB ou SQLite
                    ↓
             templates Jinja2 + Tailwind CSS + Plotly.js + Leaflet.js
```

> Voir [ARCHITECTURE.md](ARCHITECTURE.md) pour le detail technique (Service Layer, Blueprints, etc.)

---

## Authentification et contrôle d'accès

### Page de connexion — `/login`

La page d'accueil redirige automatiquement vers le formulaire de connexion. Les identifiants sont validés côté serveur.

**Comptes disponibles :**

| Identifiant | Mot de passe | Rôle | Accès export |
|-------------|-------------|------|-------------|
| `admin` | `admin123` | Administrateur | Oui |
| `responsable` | `resp123` | Responsable | Oui |
| `operateur` | `oper123` | Employé | Non |

### Contrôle d'accès par rôle (RBAC)

Toutes les pages du dashboard sont protégées par le décorateur `@login_required`. Un utilisateur non connecté est redirigé vers `/login`.

La fonctionnalité d'**export** (PDF et Excel) est réservée aux rôles `admin` et `responsable`. Un opérateur connecté voit les indicateurs mais ne dispose pas des boutons d'export.

### Déconnexion

Un bouton de déconnexion est disponible dans le header sur toutes les pages authentifiées.

---

## Navigation

Le layout respecte le CDC (bandeau haut + bandeau gauche + contenu central) :

1. **Header (bandeau haut)** : logo, boutons rafraichir/exporter/config BDD, logout
2. **Sidebar (bandeau gauche)** : navigation KPI color-codee, filtre temporel annee/mois, infos utilisateur
3. **Fil d'Ariane** : position dans l'arborescence (Accueil > Page)

### Structure des pages

```
/login              → Page de connexion (standalone)
/dashboard          → Vue synthetique (5 cartes KPI)
  /performance      → Detail Performance (OEE, utilisation, cadence, cycle)
  /qualite          → Detail Qualite (non-conformite, detection)
  /delai            → Detail Delai (lead time, attente buffer)
  /energie          → Detail Energie (conso electrique, air comprime)
  /stock            → Detail Stock (occupation buffers, variation)
  /carte            → Plan interactif de la ligne FESTO (Leaflet.js)
/config-bdd         → Configuration base de donnees + import drag & drop
/api/kpis           → Donnees JSON (usage API)
/api/donnees        → Liste des tables sources (JSON)
/api/donnees/<table>→ Export CSV d'une table brute
```

### Filtre temporel

Un filtre annee/mois est present dans la sidebar sur toutes les pages KPI.
Quand l'utilisateur selectionne une periode, tous les indicateurs de la page
se recalculent sur cette plage. Le filtre est propage via query string
(`?year=2024&month=10`) et passe a chaque fonction de calcul KPI.

---

## Dashboard principal — `/dashboard`

Page centrale de l'application. Elle affiche **5 cartes KPI** résumées, chacune cliquable pour accéder à la page de détail correspondante.

| Carte | KPI affiché | Seuils d'alerte |
|-------|------------|-----------------|
| Performance | OEE (%) | < 60 % : critique, < 85 % : warning |
| Qualité | Taux de non-conformité (%) | > 2 % : critique |
| Délai | Lead Time moyen (heures) | > 3 h : warning |
| Énergie | Consommation électrique théorique (Wh/unité) | — |
| Stock | Taux d'occupation des buffers (%) | > 90 % : critique, > 80 % : warning |

Chaque carte affiche une couleur selon le statut : **vert** (normal), **orange** (warning), **rouge** (critique).

---

## Pages de détail

### Performance — `/performance`

Quatre indicateurs relatifs à l'efficacité de la ligne :

**OEE — Taux de Rendement Global**
- Formule NF E60-182 : Disponibilite x Performance x Qualite
- Disponibilite = temps Busy / duree cumulee des ordres de fabrication
- Performance = (pieces x cycle ideal) / temps Busy
- Qualite = pieces conformes / total pieces
- Affiché sous forme de jauge circulaire avec decomposition des trois composantes
- Sources : `tblmachinereport`, `tblfinstep`, `tblfinorder`, `tblfinorderpos`

**Taux d'utilisation machine**
- Ratio temps AutomaticMode / temps session par machine
- Graphique en barres horizontales — une barre par machine (IDs 1 à 8)
- Source : `tblmachinereport`

**Cadence réelle (pièces/heure)**
- Nombre de pièces finies divisé par la durée totale de production
- Graphique en courbe avec ventilation mensuelle
- Source : `tblfinorderpos`

**Temps moyen de cycle (secondes/pièce)**
- Moyenne des durées des étapes productives (OpNo < 200, sans erreur)
- Affiché sous forme de métrique avec nombre d'observations
- Source : `tblfinstep`

---

### Qualité — `/qualite`

**Taux de non-conformité (%)**
- Combinaison de deux sources : ordres en erreur (`tblfinorderpos`) et détections capteurs (`tblpartsreport`)
- Graphique en barres par machine
- Seuil critique : > 2 %

**Temps de détection de défaut (secondes)**
- Mesure le délai entre le déclenchement d'une erreur machine (ErrorL0 ou ErrorL2) et l'arrêt effectif
- Graphique scatter des 20 derniers événements d'erreur
- Source : `tblmachinereport`

---

### Délai — `/delai`

**Lead Time (heures)**
- Durée moyenne entre le début et la fin d'un ordre de fabrication
- Graphique scatter — un point par ordre (axe X : date de début, axe Y : durée)
- Filtre : durées > 24 h exclues (gaps inter-sessions de test)
- Source : `tblfinorder`

**Temps d'attente en buffer (secondes)**
- Durée moyenne passée dans les zones de stockage intermédiaire
- Identifié par les étapes avec OpNo entre 210 et 215
- Source : `tblfinstep`

---

### Énergie — `/energie`

**Consommation electrique theorique (Wh/unite)**
- Basee sur `tblfinstep.ElectricEnergyCalc` (valeurs theoriques par etape)
- Conversion : mWs -> Wh (1 kWh = 3.6e9 mWs)
- Graphique timeline par heure de production

**Consommation air comprime theorique (L/unite)**
- Basee sur `tblfinstep.CompressedAirCalc`
- Conversion : mNl -> L (1 L = 1000 mNl)

> **Note importante :** Les valeurs de consommation réelle (`ElectricEnergyReal`, `CompressedAirReal`) sont à 0 dans la base de données. L'application affiche systématiquement les valeurs théoriques avec une mention explicite.

---

### Stock — `/stock`

**Taux d'occupation des buffers (%)**
- Ratio positions occupées / capacité totale par zone de stockage
- Graphique en barres par buffer
- Sources : `tblbuffer` (dimensions), `tblbufferpos` (positions)

**Variation du niveau de stock (%)**
- Delta moyen entre quantités successives par buffer
- Plafonné à 10 % pour l'affichage
- Sources : `tblbuffer`, `tblbufferpos`

---

## Fonctionnalité d'export

Accessible depuis le bouton **Exporter** dans le header (rôles admin et responsable uniquement).

### Export Excel (.xlsx)

Génère un fichier Excel avec une feuille par catégorie de KPI. Chaque feuille contient les valeurs calculées au moment de l'export.

### Export PDF

Génère un rapport PDF du dashboard courant. Nécessite `weasyprint` avec GTK3 sur Windows. En cas d'indisponibilité, bascule automatiquement sur un export HTML.

---

## Carte de la ligne — `/carte`

Page interactive montrant le plan de la ligne FESTO CP Factory avec Leaflet.js.

- **Layout** : machines positionnees en boucle (topologie reelle 1→2→3→4→5→6→7→1 + branche 1→8)
- **Couleurs** : vert (auto), bleu (busy), rouge (erreur), gris (off)
- **Cercle interne** : proportionnel au taux d'utilisation
- **Click** : detail du poste (utilisation, busy %) dans le panneau lateral
- **Tableau** : recapitulatif de tous les postes avec etat et metriques
- **Buffers** : barres de progression dans le panneau lateral

---

## Configuration BDD — `/config-bdd`

Page d'administration (role admin uniquement) permettant de :

1. **Connecter a MariaDB** : saisie IP/port/user/pass, test de connexion, application
2. **Importer un fichier SQL** : drag & drop de dumps HeidiSQL/mysqldump
   - Nettoyage automatique des octets nuls
   - Conversion MySQL→SQLite (types, ENGINE, CHARSET, INSERT multi-lignes)
   - Switch d'engine immediat (pas besoin de redemarrer)
3. **Revenir a la base locale** : retour au SQLite embarque

---

## API

### `/api/kpis` — KPIs calcules (JSON)

Endpoint protege retournant les KPIs du dashboard. Supporte le filtre temporel (`?year=2024&month=10`).

### `/api/donnees` — Liste des tables (JSON)

Retourne la liste des tables avec nombre de lignes et lien CSV.
CDC point 4 : "acces aux donnees sources sous forme de lien URL".

### `/api/donnees/<table>` — Export CSV

Telecharge une table brute en CSV. Exemple : `/api/donnees/tblmachinereport`.

---

## Page d'erreur 404

Page personnalisée (`templates/404.html`) affichée lorsqu'une URL inexistante est demandée. Design cohérent avec le reste de l'application (Tailwind CSS, couleurs du projet).

---

## Sécurité

- Mots de passe haches avec scrypt (`werkzeug.security.generate_password_hash`)
- Toutes les routes (sauf `/login`) requierent une session active (`@login_required`)
- Les sessions Flask sont signees avec `SECRET_KEY`
- RBAC : 3 roles (admin, responsable, employe) via `@role_required`
- API CSV : validation des noms de table contre `inspector.get_table_names()` (anti-injection)
- En Docker, les imports ne modifient pas le `.env` (protection `/.dockerenv`)

---

## Technologies utilisées

| Couche | Technologie |
|--------|------------|
| Backend | Flask 3.0.3 + SQLAlchemy + Jinja2 |
| Base de données | MariaDB 10.6 (64 tables, schéma MES4) |
| Driver BDD | PyMySQL 1.1.1 (pure Python) |
| Frontend | Tailwind CSS (CDN) + Plotly.js (CDN) + Leaflet.js + police Outfit |
| Calcul KPIs | Pandas 2.2.2 |
| Export Excel | openpyxl 3.1.3 |
| Export PDF | weasyprint 62.3 |
| Tests | pytest 8.2.2 + pytest-flask 1.3.0 |

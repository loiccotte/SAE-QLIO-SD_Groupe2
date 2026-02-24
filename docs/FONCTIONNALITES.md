# Documentation technique — Fonctionnalités de la WebApp

**Projet :** T'ELEFAN MES 4.0
**Description :** Tableau de bord industriel pour le pilotage d'une ligne de production FESTO semi-automatisée (fabrication de smartphones, 12 machines, données MES réelles)

---

## Vue d'ensemble

L'application est un dashboard web à usage interne. Elle permet à différents profils (opérateur, responsable, administrateur) de consulter en temps réel les indicateurs de performance de la ligne de production. Toutes les données proviennent d'une base MariaDB en **lecture seule** — l'application n'écrit jamais dans la base.

### Architecture

```
Navigateur  →  Flask (routes.py)  →  services.py (calcul KPIs)  →  SQLAlchemy  →  MariaDB (MES4)
                     ↓
              templates Jinja2 + Tailwind CSS + Plotly.js
```

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

La navigation repose sur deux niveaux :

1. **Header** : présent sur toutes les pages, avec le logo, le minuteur de rafraîchissement, le bouton d'export et la déconnexion.
2. **Fil d'Ariane** : indique la position dans l'arborescence (Accueil > Catégorie).

La structure des pages est :

```
/login
/dashboard          → Vue synthétique (5 cartes KPI)
  /performance      → Détail Performance
  /qualite          → Détail Qualité
  /delai            → Détail Délai
  /energie          → Détail Énergie
  /stock            → Détail Stock
/api/kpis           → Données JSON (usage API)
```

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
- Formule : Disponibilité × Performance × Qualité
- Affiché sous forme de jauge circulaire avec décomposition des trois composantes
- Sources : `tblmachinereport`, `tblfinstep`, `tblresourceoperation`, `tblfinorderpos`

**Taux d'utilisation machine**
- Ratio temps actif (Busy) / temps total par machine
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

**Consommation électrique théorique (Wh/unité)**
- Basée sur les valeurs nominales de `tblresourceoperation` (ElectricEnergy)
- Graphique en courbe par heure de production

**Consommation air comprimé théorique (L/unité)**
- Jauges circulaires pour la pression d'air
- Source : `tblresourceoperation` (CompressedAir)

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

## API JSON — `/api/kpis`

Endpoint protégé (`@login_required`) retournant les KPIs du dashboard au format JSON. Prévu pour une intégration future avec un client JavaScript ou une interface externe.

Exemple de réponse :

```json
{
  "oee": {"value": 73.5, "availability": 82.1, "performance": 94.2, "quality": 95.0, "status": "warning"},
  "non_conformity": {"value": 1.45, "status": "normal"},
  "lead_time": {"value": 1.8, "status": "normal"},
  "energy": {"value": 12.4, "unit": "Wh/u", "status": "normal"},
  "buffer": {"value": 44.2, "status": "normal"}
}
```

---

## Page d'erreur 404

Page personnalisée (`templates/404.html`) affichée lorsqu'une URL inexistante est demandée. Design cohérent avec le reste de l'application (Tailwind CSS, couleurs du projet).

---

## Sécurité

- Toutes les routes (sauf `/login`) requièrent une session active
- Les sessions Flask sont signées avec `SECRET_KEY`
- Le contrôle d'accès aux exports est appliqué via un décorateur `@role_required`
- La base de données est accédée en lecture seule (aucun `INSERT`, `UPDATE`, `DELETE` dans le code)
- Les identifiants sont stockés dans le code source (pas en base) — acceptable pour un projet pédagogique

---

## Technologies utilisées

| Couche | Technologie |
|--------|------------|
| Backend | Flask 3.0.3 + SQLAlchemy + Jinja2 |
| Base de données | MariaDB 10.6 (64 tables, schéma MES4) |
| Driver BDD | PyMySQL 1.1.1 (pure Python) |
| Frontend | Tailwind CSS (CDN) + Plotly.js (CDN) + police Geist |
| Calcul KPIs | Pandas 2.2.2 |
| Export Excel | openpyxl 3.1.3 |
| Export PDF | weasyprint 62.3 |
| Tests | pytest 8.2.2 + pytest-flask 1.3.0 |

# Analyse complète du projet SAE MES4.0 - Groupe 2

## 1. Contexte du projet

### L'entreprise fictive
**T'EleFan** : fabricant de smartphones durables, a investi dans une **ligne de production semi-automatisée FESTO** et a besoin d'un **tableau de bord MES** (Manufacturing Execution System) pour piloter sa production en temps réel.

### Les équipes
- **QLIO** 
- **SD** 
- **Encadrants** 

### Planning

| Jalon | Date | Contenu |
|-------|------|---------|
| Lancement | 23 sept 2025 | Prise en main |
| Sprint 1 / Revue client 1 | Semaine 49 (déc 2025) | CDC + 12 KPIs + Maquette |
| **Rendu 23 janvier 2026** | **23 jan 2026** | Note de synthèse + Maquette + MCD + Dictionnaire |
| **Sprint 2 SD** | **Semaine 9 (fév 2026)** | Revue client SD uniquement |
| Sprint 3 / Livraison finale | Semaine 14 (mars 2026) | App Python complète + docs |

---

## 2. Ce qui est demandé (CDC v2.0)

### 2.1 Les 12 KPIs obligatoires

| # | KPI | Catégorie | Couleur | Seuil d'alerte |
|---|-----|-----------|---------|----------------|
| 1 | OEE (Taux de Rendement Global) | Performance | Rouge `#ff0000` | < 85% |
| 2 | Taux d'utilisation machine | Performance | Rouge | Baisse > 10% sur 7j |
| 3 | Cadence réelle (pièces/h) | Performance | Rouge | < nominale -10% |
| 4 | Temps moyen de cycle (s/pièce) | Performance | Rouge | > nominal x 1.1 |
| 5 | Taux de non-conformité (%) | Qualité | Bleu `#38b6ff` | > 2% |
| 6 | Temps de détection défaut (s) | Qualité | Bleu | > 10s |
| 7 | Lead Time / unité | Délai | Rose `#f2c0ff` | > nominal x 1.1 |
| 8 | Temps d'attente en buffer | Délai | Rose | > nominal x 1.2 |
| 9 | Consommation énergétique (kWh/unit) | Énergie | Vert `#09b200` | Dérive +10%/sem |
| 10 | Consommation air comprimé (L/unit) | Énergie | Vert | Tolérance +/-15% |
| 11 | Taux d'occupation des buffers (%) | Stock | Gris `#737373` | > 90% |
| 12 | Variation du niveau de stock | Stock | Gris | Variation > 20% |

### 2.2 Fonctionnalités attendues

1. **Authentification** : login + 3 rôles (Admin / Responsable / Employé) + bouton LOGOUT
2. **Actualisation** : auto toutes les 5 min + bouton "Actualiser" manuel
3. **Graphiques** : jauges semi-circulaires, histogrammes, courbes, nuages de points
4. **Alertes visuelles** : icône clignotante si KPI hors seuil
5. **Export PDF/Excel** : avec filtres temporels (Année > Mois > Jour > Heure)
6. **Charte graphique** : couleurs par catégorie, angles arrondis 15, flèches tendance
7. **Pages détaillées** : chaque catégorie cliquable ouvre une page dédiée

### 2.3 Exigences techniques

- Python (Flask), MariaDB, Docker
- Compatible Windows 11 / Chrome / Edge
- Tests unitaires et fonctionnels
- Documentation technique (installation + utilisation)

---

## 3. Ce qui a été livré (rendu du 23 janvier)

| Document | Contenu |
|----------|---------|
| Note de synthèse (.docx) | Architecture Flask+MariaDB+Docker, 12 KPIs, ergonomie, sécurité RBAC |
| Maquette (.pdf, 8 pages) | Maquettes visuelles du tableau de bord (images uniquement) |
| MCD (.pdf) | Schéma en étoile : table de faits `FAIT_PRODUCTION` + 7 dimensions |
| Dictionnaire de données (.xlsx) | 16 variables documentées (12 obligatoires + 4 bonus) |

### KPIs bonus proposés dans le dictionnaire

| Variable | Description |
|----------|-------------|
| `ecart_lancement` | Écart entre début planifié et début réel |
| `respect_delais` | % commandes terminées dans les délais |
| `efficience_energetique` | Ratio conso théorique / réelle |
| `performance_operateur` | Temps cycle réel vs standard par opérateur |

---

## 4. État actuel du code

### Architecture existante

```
SAE-QLIO-SD/
├── app/
│   ├── __init__.py      # Factory Flask + SQLAlchemy
│   ├── models.py        # 2 modèles : Order, Step (squelette)
│   ├── routes.py        # 1 route "/" (contient un bug)
│   ├── services.py      # 1 calcul : calculate_lead_time()
│   └── run.py           # Point d'entrée
├── templates/
│   └── index.html       # HTML basique (juste lead time)
├── docker-compose.yml   # MariaDB + phpMyAdmin + app
├── Dockerfile           # Python 3.10
├── requirements.txt     # flask, flask-sqlalchemy, pymysql, pandas, plotly
└── ressources/          # PDFs, SQL dump, CSV, documents rendus
```

### Bug identifié
`routes.py:6` : utilise `@app.route('/')` au lieu de `@bp.route('/')` (Blueprint déclaré mais non utilisé correctement).

### Ce qui fonctionne
- 1 seul KPI implémenté : Lead Time moyen (basique)
- Infrastructure Docker prête (MariaDB + phpMyAdmin + Flask)

---

## 5. La base de données MES4

### Vue d'ensemble

- **64 tables** au total dans le dump SQL
- **Base MES générique Festo**, pas conçue pour l'analytique
- Données = **jeux de test** (pas de production continue)

### Les 12 machines de la ligne

| ID | Nom | Description |
|----|-----|-------------|
| 1 | CP-F-ASRS32-P | Stockage automatisé palettes/capots |
| 2 | CP-AM-iPICK | Pick by light (sélection composants) |
| 3 | CP-AM-CAM | Contrôle caméra |
| 4 | CP-AM-MAG-BACK | Alimentation capots arrière |
| 5 | CP-AM-MPRESS | Presse musculaire |
| 6 | CP-AM-MAN | Poste manuel |
| 7 | CP-F-COBOT | Cobot UR3e (assemblage) |
| 8 | CP-F-ASRS20-B | Stockage automatisé boîtes |
| 9 | MAN-MOBILE | Poste mobile manuel |
| 10 | LOG-MR-B | Robot mobile Robotino |
| 11 | (station) | Autre station |
| 90 | SPARE PARTS | Stock pièces détachées |

### Le produit fabriqué

Smartphone = capot avant (noir/gris/bleu/rouge) + capot arrière + PCB + fusibles + étiquette.
Gamme typique : stock -> pick composants -> assemblage cobot -> pressage -> contrôle caméra -> étiquetage -> mise en boîte -> stockage.

### Tables clés et volume de données

| Table | Lignes | Rôle |
|-------|--------|------|
| `tblmachinereport` | 10 126 | États machine horodatés (Busy, Errors) |
| `tblfinstep` | 1 460 | Étapes de production terminées |
| `tblpartsreport` | 1 191 | Détection pièces + erreurs |
| `tblfinstepparameter` | 5 830 | Paramètres des étapes |
| `tblfinorderpos` | 411 | Pièces produites (positions d'ordres) |
| `tblfinorder` | 189 | Ordres de fabrication terminés |
| `tblresourceoperation` | 142 | Capacités machine (temps nominaux) |
| `tblbufferpos` | 77 | Positions dans les buffers |
| `tblresource` | 12 | Machines |
| `tblbuffer` | 10 | Zones de stockage |

### Tables vides (7 sans données)

`tblaltoperationparameter`, `tblautomaticorder`, `tblbookedbufmsg`, `tblpallet`, `tblpalletdef`, `tblpalletpos`, `tblservicetimetable`

---

## 6. Mapping KPI -> Tables -> Colonnes

### KPI 1 : OEE (Taux de Rendement Global)

| Composante | Source | Calcul |
|------------|--------|--------|
| Disponibilité | `tblmachinereport` (Busy, ErrorL0/L2, TimeStamp) | Temps Busy / Temps total (hors erreurs) |
| Performance | `tblfinstep` (Start, End) + `tblresourceoperation` (WorkingTime) | Temps nominal / Temps réel |
| Qualité | `tblfinorderpos` (Error) | Pièces OK / Total pièces |

### KPI 2 : Taux d'utilisation machine

| Source | Colonnes | Calcul |
|--------|----------|--------|
| `tblmachinereport` | ResourceID, TimeStamp, Busy | Durée cumul Busy=1 / Durée totale observation |

Attention : c'est de l'event-driven, il faut calculer la durée **entre deux événements consécutifs** pour une même machine.

### KPI 3 : Cadence réelle

| Source | Colonnes | Calcul |
|--------|----------|--------|
| `tblfinorderpos` | End, ONo | Count(pièces avec End dans période) / Durée période |

### KPI 4 : Temps moyen de cycle

| Source | Colonnes | Calcul |
|--------|----------|--------|
| `tblfinstep` | Start, End | AVG(End - Start) par type d'opération |

### KPI 5 : Taux de non-conformité

| Source | Colonnes | Calcul |
|--------|----------|--------|
| `tblfinorderpos` | Error | Count(Error != 0) / Count(total) |
| `tblpartsreport` | ErrorID | Count(ErrorID != 0) / Count(total) |

Données réelles : **4 erreurs sur 411 pièces** (~1%) dans `tblfinorderpos`, **27 erreurs sur 1191** dans `tblpartsreport`.

### KPI 6 : Temps de détection défaut

| Source | Colonnes | Calcul |
|--------|----------|--------|
| `tblmachinereport` | TimeStamp, ErrorL0, ErrorL2 | Delta temps entre ErrorLx passant à 1 et Busy passant à 0 |

Note : ErrorL1 n'est **jamais** activé dans les données.

### KPI 7 : Lead Time

| Source | Colonnes | Calcul |
|--------|----------|--------|
| `tblfinorder` | Start, End | End - Start par ordre |

189 ordres disponibles, de 2016 à mars 2025.

### KPI 8 : Temps d'attente en buffer

| Source | Colonnes | Calcul |
|--------|----------|--------|
| `tblfinstep` | Start, End, OpNo | Durée des étapes dont OpNo correspond à une opération buffer (OpNo 210-215 = stockage/déstockage) |

### KPI 9 : Consommation énergétique

| Source | Colonnes | Calcul |
|--------|----------|--------|
| `tblfinstep` | ElectricEnergyReal | SUM / nb pièces |
| `tblresourceoperation` | ElectricEnergy (théorique) | Fallback : seules ResID 4 et 5 ont des valeurs |

**PROBLEME : ElectricEnergyReal = 0 sur 100% des lignes.** Il faudra utiliser les valeurs théoriques ou simuler.
Unité : mWs (milli-Watt-secondes). 1 kWh = 3 600 000 000 mWs.

### KPI 10 : Consommation air comprimé

| Source | Colonnes | Calcul |
|--------|----------|--------|
| `tblfinstep` | CompressedAirReal | SUM / nb pièces |
| `tblresourceoperation` | CompressedAir (théorique) | Fallback : seules ResID 4 et 5 ont des valeurs |

**MEME PROBLEME : CompressedAirReal = 0 partout.**
Unité : mNl (milli-Normal-litres). 1 L = 1000 mNl.

### KPI 11 : Taux d'occupation buffers

| Source | Colonnes | Calcul |
|--------|----------|--------|
| `tblbuffer` | Rows, Columns | Capacité max = Rows x Columns |
| `tblbufferpos` | Quantity, TimeStamp | Occupation = SUM(Quantity) / Capacité max |

10 buffers définis, 77 positions actuelles.

### KPI 12 : Variation du niveau de stock

| Source | Colonnes | Calcul |
|--------|----------|--------|
| `tblbufferpos` | Quantity, TimeStamp | Delta Quantity entre deux TimeStamps consécutifs |

---

## 7. Problèmes identifiés dans les données

### Critiques

| Problème | Impact | Solution possible |
|----------|--------|-------------------|
| `ElectricEnergyReal` = 0 partout | KPI 9 non calculable en réel | Utiliser valeurs théoriques de `tblresourceoperation` (seulement 2 machines renseignées) |
| `CompressedAirReal` = 0 partout | KPI 10 non calculable en réel | Idem |
| `tblstepdef` vide (0 lignes) | Pas de temps standards par étape | Utiliser `tblresourceoperation.WorkingTime` comme référence |
| Codes erreur incohérents | ErrorID 5050 et 99 dans `tblpartsreport` n'existent pas dans `tblerrorcodes` | Gérer comme erreurs "inconnues" |

### Modérés

| Problème | Impact | Solution possible |
|----------|--------|-------------------|
| Dates de 2016 à 2025 | Données = sessions de test, pas production continue | Filtrer les périodes pertinentes ou tout agréger |
| `tblfinorderpos.ResourceID` = 0 partout | Pas de lien direct pièce-machine dans cette table | Passer par `tblfinstep` qui a bien ResourceID |
| `tblfinorderpos.Error` = 0 sur 99% | Très peu d'erreurs (4/411) | Le taux sera très bas - c'est peut-être réaliste pour des tests |
| ErrorL1 jamais activé | Un niveau d'erreur inutilisé | Ignorer ErrorL1 |
| Seulement 15/142 `tblresourceoperation` avec WorkingTime | Beaucoup d'opérations sans temps nominal | Limiter le calcul OEE aux machines renseignées |

---

## 8. Ce qui reste à faire

### Développement

1. Corriger le bug `routes.py` (`@bp.route` au lieu de `@app.route`)
2. Implémenter les **12 KPIs** avec leurs requêtes SQL
3. Créer le **modèle de données intermédiaire** (schéma en étoile du MCD)
4. Construire l'**interface complète** selon la maquette et la charte graphique
5. Ajouter l'**authentification** (login, 3 rôles RBAC, LOGOUT)
6. Système d'**alertes visuelles** (seuils/dérives clignotants)
7. **Filtres temporels** et actualisation auto/manuelle
8. **Export PDF/Excel**
9. **Pages détaillées** par catégorie de KPI
10. **Tests** unitaires et fonctionnels
11. **Documentation** technique (installation + utilisation)

### Décisions à prendre

- Comment gérer les KPIs énergie/air avec des données à 0 ?
- Faut-il implémenter le schéma en étoile (MCD) ou requêter directement la BDD MES4 ?
- Quelles périodes de données filtrer (ignorer 2016-2017 ?)

# Analyse des Différences : Site Actuel vs CDC + Maquette

> Analyse exhaustive, zéro tolérance. Chaque écart entre les templates HTML actuels et les documents de référence (CDC_MES4.0_V2.pdf + Maquette_Groupe2.pdf) est listé.

---

## 0. Sources de référence

| Document | Pages clés |
|---|---|
| CDC p.11 | Fonctions attendues (login, actualisation, alertes, exports) |
| CDC p.12 | Charte graphique (couleurs exactes, transparences, flèches tendance) |
| CDC p.13 | Interface voulue (zones KPI et graphiques par thème) |
| CDC p.14 | Figure 5 — wireframe dashboard global |
| CDC p.15 | Figure 6 — wireframe page Qualité |
| Maquette p.1 | Page de connexion |
| Maquette p.2 | Dashboard global |
| Maquette p.3 | Page Performance |
| Maquette p.4 | Page Qualité |
| Maquette p.5 | Page Délai |
| Maquette p.6 | Page Énergie |
| Maquette p.7 | Page Stock |
| Maquette p.8 | Page 404 |

---

## 1. Page de Connexion (`login.html`)

### Comparaison : Maquette p.1

| # | Élément | Maquette / CDC | Actuel | Priorité |
|---|---|---|---|---|
| 1.1 | Couleur logo "T'ÉLÉFAN" | Bleu marine foncé (~#1a2b5e) | Noir (`zinc-900` = #18181b) | HAUTE |
| 1.2 | Couleur bouton "SE CONNECTER" | Bleu marine (même bleu que logo) | Noir (`zinc-900`) | HAUTE |
| 1.3 | Texte bouton | "SE CONNECTER" (capitales) | "Se connecter" → classe `uppercase` le rend en caps ✓ mais couleur fausse | HAUTE (couleur) |
| 1.4 | Copyright | `© T'ÉLÉFAN 2023` | `T'ELEFAN 2026` — manque `©`, accents absents | BASSE |
| 1.5 | Accent sur le nom | `T'ÉLÉFAN` (deux É accentués) | `T'ELEFAN` (aucun accent) | MOYENNE |
| 1.6 | Fond de page | Gris clair / blanc cassé | `bg-zinc-50` ≈ correct ✓ | — |
| 1.7 | Carte centrée | Carte blanche avec ombre légère | Conforme ✓ | — |

---

## 2. Dashboard Global (`dashboard.html`)

### Comparaison : Maquette p.2 + CDC p.12–14

| # | Élément | Maquette / CDC | Actuel | Priorité |
|---|---|---|---|---|
| 2.1 | **Titre "TABLEAU DE BORD GLOBAL"** | Affiché en grand titre visible dans la page | Seulement dans le breadcrumb en petit texte | HAUTE |
| 2.2 | **Flèches de tendance (▲▼)** | Obligatoires sur chaque carte KPI (CDC p.12) — ▲ vert `#16a637`, ▼ rouge `#ff000f` | **Absentes** sur toutes les cartes | HAUTE |
| 2.3 | **Position LOGOUT** | Coin inférieur droit de la page (hors header) | Dans l'en-tête en haut à droite | HAUTE |
| 2.4 | **Couleur Performance** | `#ff0000` (rouge pur) — CDC p.12 | `#dc2626` (rouge légèrement différent) | HAUTE |
| 2.5 | **Couleur Qualité** | `#38b6ff` (bleu clair) — CDC p.12 | `#0284c7` (bleu plus foncé) | HAUTE |
| 2.6 | **Couleur Délai** | `#f2c0ff` (rose clair / lavande) — CDC p.12 | `#db2777` (rose vif / magenta) | HAUTE |
| 2.7 | **Couleur Énergie** | `#09b200` (vert vif) — CDC p.12 | `#16a34a` (vert légèrement différent) | HAUTE |
| 2.8 | **Couleur Stock** | `#737373` (gris moyen) — CDC p.12 | `#52525b` (gris plus foncé) | HAUTE |
| 2.9 | **Fond des cartes** | "Transparence fond: 25%" avec couleur thème (CDC p.12) | Fond blanc pur + seulement une fine barre colorée (1.5px) en haut | HAUTE |
| 2.10 | **Alerte sur carte Énergie** | Le CDC exige une alerte ⚠ clignotante si dérive > 10%/sem | Aucun indicateur de statut/alerte sur la carte Énergie du dashboard | MOYENNE |
| 2.11 | Séparateur breadcrumb | `Accueil > PERFORMANCE` (symbole `>`) | `Accueil / Performance` (slash `/`) | MOYENNE |
| 2.12 | Disposition des 5 cartes | 3 en haut (Perf, Qualité, Délai) + 2 en bas (Énergie, Stock) | Identique ✓ | — |
| 2.13 | 1 KPI résumé par carte | Conforme maquette (OEE, Non-conformité, Lead Time, Conso, Occupation) | Conforme ✓ | — |
| 2.14 | Bouton Actualiser (5min) | Présent en haut gauche | Présent ✓ | — |
| 2.15 | Bouton Exporter | Présent en haut droite | Présent ✓ | — |

---

## 3. Page Performance (`performance.html`)

### Comparaison : Maquette p.3 + CDC p.13

| # | Élément | Maquette / CDC | Actuel | Priorité |
|---|---|---|---|---|
| 3.1 | **En-tête sur pages thème** | Pages 4–7 maquette : titre de page ("QUALITÉ", "DÉLAI"…) AU CENTRE du header, à la place du logo T'ÉLÉFAN | T'ÉLÉFAN logo toujours centré dans le header sur toutes les pages | HAUTE |
| 3.2 | **Taux d'utilisation — axe X** | Maquette : barres par MOIS (Jan, Fév, Mar… Déc) — une barre rouge labellisée ">10%" | Barres par NOM DE MACHINE | HAUTE |
| 3.3 | **Taux d'utilisation — orientation** | CDC p.13 : "Histogramme ou barres horizontales" | Barres verticales | MOYENNE |
| 3.4 | **Cadence réelle — ligne nominale** | CDC p.13 : "Ligne cadence nominale (barre droite objectif) avec ligne de cadence réel à côté" → ligne de référence objectif obligatoire | Aucune ligne de cadence nominale sur le graphique | HAUTE |
| 3.5 | **Cadence réelle — axe X** | Maquette : axe temporel (18:00, 18:30… 23:00) | Axe mensuel (mois) | MOYENNE |
| 3.6 | OEE — jauge semi-circulaire | Conforme (gauge Plotly) ✓ | Conforme ✓ | — |
| 3.7 | OEE — zones couleurs | Maquette : rouge (bas) → orange → vert (haut) | Rouge/jaune/vert — proche ✓ | — |
| 3.8 | Temps moyen de cycle — affichage valeur | Conforme (grande valeur en s) ✓ | Conforme ✓ | — |
| 3.9 | Alerte ⚠ sur Temps moyen de cycle | Présent dans maquette | Présent ✓ | — |
| 3.10 | Titre "PERFORMANCE" | Gros titre visible dans le contenu ou l'en-tête | Petit h2 "Performance" dans le contenu | BASSE |

---

## 4. Page Qualité (`qualite.html`)

### Comparaison : Maquette p.4 + CDC p.13

| # | Élément | Maquette / CDC | Actuel | Priorité |
|---|---|---|---|---|
| 4.1 | En-tête (même problème) | "QUALITÉ" au centre du header | T'ÉLÉFAN logo centré | HAUTE |
| 4.2 | **Temps de détection défaut — axe X** | Maquette : axe temporel/horaire (07:30, 08:00, 09:00…) | `Machine #N` (événements numérotés) | HAUTE |
| 4.3 | Taux de non-conformité — jauge | Conforme (semi-circulaire) ✓ | Conforme ✓ | — |
| 4.4 | Seuil non-conformité | Alerte si > 2% (CDC p.8) | Threshold à 2% présent ✓ | — |
| 4.5 | Seuil temps détection | Alerte si > 10s (CDC p.8) | Threshold à 10s présent ✓ | — |

---

## 5. Page Délai (`delai.html`)

### Comparaison : Maquette p.5 + CDC p.13

| # | Élément | Maquette / CDC | Actuel | Priorité |
|---|---|---|---|---|
| 5.1 | En-tête (même problème) | "DÉLAI" au centre du header | T'ÉLÉFAN logo centré | HAUTE |
| 5.2 | **Lead Time — axe X** | Maquette : axe temporel (00:00 à 30:00) | "Index ordre" (0, 1, 2, 3…) | MOYENNE |
| 5.3 | **Temps d'attente buffer — axe X** | Maquette : axe temporel (00:00 à 30:00) | "Index temporel" (entier) | MOYENNE |
| 5.4 | Lead Time — type graphique | Nuage de points (scatter) — CDC ✓ | Scatter ✓ | — |
| 5.5 | Temps buffer — type graphique | Courbe d'évolution — CDC ✓ | Ligne ✓ | — |
| 5.6 | Zone d'alerte buffer | Maquette montre zone rose "Alert" | Zone rect rose présente ✓ | — |

---

## 6. Page Énergie (`energie.html`)

### Comparaison : Maquette p.6 + CDC p.13

| # | Élément | Maquette / CDC | Actuel | Priorité |
|---|---|---|---|---|
| 6.1 | En-tête (même problème) | "ÉNERGIE" au centre du header | T'ÉLÉFAN logo centré | HAUTE |
| 6.2 | **Section "Résumé" en bas** | Absente de la maquette | Présente (carte avec valeurs récapitulatives) | MOYENNE |
| 6.3 | **Jauge Air comprimé — zones** | Maquette : zones fixes rouge/vert/rouge (tolérance ±15% de la nominale) | Zones calculées dynamiquement relative à la valeur courante | MOYENNE |
| 6.4 | Consommation énergétique — type graphique | Courbe d'évolution — CDC ✓ | Courbe ✓ | — |
| 6.5 | Consommation air — type graphique | Jauge semi-circulaire — CDC ✓ | Gauge ✓ | — |

---

## 7. Page Stock (`stock.html`)

### Comparaison : Maquette p.7 + CDC p.13

| # | Élément | Maquette / CDC | Actuel | Priorité |
|---|---|---|---|---|
| 7.1 | En-tête (même problème) | "STOCK" au centre du header | T'ÉLÉFAN logo centré | HAUTE |
| 7.2 | **Section "Résumé" en bas** | Absente de la maquette | Présente | MOYENNE |
| 7.3 | **Variation stock — plage axe Y** | CDC p.9 : "Alerte si variation > 20%" → Y doit inclure 0–25%+ | Axe Y fixé à [0, 10%] — alerte à 20% jamais visible | HAUTE |
| 7.4 | Taux occupation buffers — barre rouge >90% | Maquette : une barre en rouge avec label ">90%" | Rouge sur barres >90% ✓ mais label ">90%" dans annotation pas au-dessus de la barre | BASSE |
| 7.5 | Type graphique buffers | Histogramme — CDC ✓ | Bar chart ✓ | — |
| 7.6 | Type graphique variation | Histogramme — CDC ✓ | Bar chart ✓ | — |

---

## 8. Export (toutes pages — `base.html`)

### Comparaison : CDC p.11

| # | Élément | CDC | Actuel | Priorité |
|---|---|---|---|---|
| 8.1 | **Filtre de période** | "Ajouter des filtres permettant de choisir la période voulue : Année → Mois → Jour → Heure" | **Complètement absent** — l'export exporte les données actuelles sans aucun filtre temporel | HAUTE |
| 8.2 | Formats export | PDF et Excel | PDF et Excel ✓ | — |
| 8.3 | Réservé admin/responsable | Oui | Oui ✓ | — |

---

## 9. Problèmes transversaux (toutes pages)

| # | Élément | Attendu | Actuel | Priorité |
|---|---|---|---|---|
| 9.1 | **LOGOUT position** | Coin inférieur droit de la page (hors header) — toutes les pages maquette | Dans le header en haut à droite | HAUTE |
| 9.2 | **Accents T'ÉLÉFAN** | `T'ÉLÉFAN` (deux É accentués) | `T'ELEFAN` affiché sans accents dans h1 et titre | MOYENNE |
| 9.3 | **Séparateur breadcrumb** | `>` (Accueil > Page) | `/` (Accueil / Page) | MOYENNE |
| 9.4 | Actualisation auto 5min | Obligatoire | Présent + compteur ✓ | — |
| 9.5 | Alerte ⚠ clignotante | Sur chaque KPI hors seuil | Présent pour perf, qualité, délai, stock ✓ — manque énergie | MOYENNE |
| 9.6 | Rôles (admin/responsable/employé) | Trois rôles distincts | Session role vérifié ✓ | — |

---

## 10. Récapitulatif par priorité

### PRIORITÉ HAUTE — À corriger immédiatement

1. **Couleurs des thèmes** : 5 couleurs incorrectes (Performance, Qualité, Délai, Énergie, Stock)
2. **Fond des cartes dashboard** : 25% transparence couleur thème manquante
3. **Flèches de tendance ▲▼** sur les 5 cartes du dashboard
4. **Position LOGOUT** : bas droite page au lieu du header
5. **Titre "TABLEAU DE BORD GLOBAL"** visible en grand sur le dashboard
6. **En-tête pages thème** : titre de page ("PERFORMANCE", "QUALITÉ"…) au centre du header, pas le logo T'ÉLÉFAN
7. **Taux d'utilisation** : barres par mois (pas par machine), orientation horizontale
8. **Ligne cadence nominale** sur le graphique Cadence réelle (Performance)
9. **Axe X temporel** sur Temps de détection défaut (Qualité)
10. **Variation stock** : axe Y jusqu'à au moins 25% (alerte > 20%)
11. **Export : filtre de période** (Année → Mois → Jour → Heure)
12. **Bouton login** : bleu marine (pas noir)

### PRIORITÉ MOYENNE

13. Accents `T'ÉLÉFAN` (partout sans accent actuellement)
14. Séparateur breadcrumb `>` au lieu de `/`
15. Sections "Résumé" inutiles sur Énergie et Stock (non présentes dans maquette)
16. Jauge Air comprimé : zones fixes ±15%
17. Axes X temporels sur Lead Time et Temps d'attente buffer (Délai)
18. Alerte énergie manquante sur dashboard

### PRIORITÉ BASSE

19. Copyright login (© manquant, année)
20. Label ">90%" positionné sur la barre en rouge (Stock)
21. Taille du titre "Performance" dans le contenu

---

## 11. Ce qui est CONFORME (ne pas toucher)

- Structure 5 cartes dashboard (3+2 lignes) ✓
- Types de graphiques : OEE gauge, NC gauge, Lead Time scatter, Buffer wait line, Energy line, Air gauge, Stock bars ✓
- Seuils d'alerte : OEE < 85%, NC > 2%, Détection > 10s, Occupation buffer > 90% ✓
- Auto-refresh 5 minutes + compteur ✓
- Bouton Actualiser en haut gauche ✓
- Bouton Exporter en haut droite ✓
- Réservation export aux rôles admin/responsable ✓
- Breadcrumb "Accueil > Page" sur pages thème ✓ (sauf séparateur)
- Pages cliquables par thème (dashboard → page détail) ✓
- Sous-détail OEE (Disponibilité / Performance / Qualité) ✓
- Icône ⚠ clignotante sur Performance, Qualité, Délai, Stock ✓

# Documentation analytique — Indicateurs et données

**Projet :** T'ELEFAN MES 4.0
**Contexte :** Ligne de production semi-automatisée FESTO MES 4.0, fabrication de smartphones

---

## Contexte industriel

La ligne T'ELEFAN est une ligne de production pédagogique FESTO de type MES 4.0 (Manufacturing Execution System). Elle simule la fabrication de smartphones en faisant transiter des pièces à travers 8 machines de production réelles et un système de stockage automatisé (ASRS). Les données couvrent la période 2016–2025, sur des sessions de test non continues.

### Architecture de la ligne

| Ressource | Type | Rôle |
|-----------|------|------|
| Machines 1 à 8 | Production | Assemblage, vissage, soudure, test |
| ASRS (AS/RS) | Stockage | Rayonnage automatisé |
| Buffers 1 à n | Attente | Zones de transit entre machines |

### Données disponibles

La base MES4 contient 64 tables. Les 10 tables utilisées dans ce projet sont :

| Table | Volume | Contenu |
|-------|--------|---------|
| `tblfinorder` | 189 lignes | Ordres de fabrication |
| `tblfinorderpos` | 411 lignes | Pièces produites par ordre |
| `tblfinstep` | 1 460 lignes | Étapes d'opération par pièce |
| `tblmachinereport` | 10 126 lignes | États machine horodatés |
| `tblresourceoperation` | 142 lignes | Temps nominaux et énergie par opération |
| `tblresource` | 12 lignes | Référentiel machines |
| `tblpartsreport` | 1 191 lignes | Détections capteurs et codes erreur |
| `tblbuffer` | 10 lignes | Zones de stockage |
| `tblbufferpos` | 77 lignes | Positions individuelles dans les buffers |
| `tblerrorcodes` | 4 lignes | Référentiel codes erreur |

---

## Pourquoi ces 5 axes d'analyse ?

Le cahier des charges demande de couvrir la performance globale d'une ligne de production industrielle. Les cinq axes retenus correspondent aux dimensions classiques du pilotage industriel (méthode QCDSE — Qualité, Coût, Délai, Sécurité, Environnement), adaptées aux données disponibles :

| Axe | Justification |
|-----|---------------|
| **Performance** | Mesure l'efficacité intrinsèque de la ligne — indicateur central en production |
| **Qualité** | Sans qualité, la performance n'a pas de valeur — indicateur de premier ordre |
| **Délai** | La réactivité logistique est un critère de compétitivité essentiel |
| **Énergie** | Enjeu environnemental et économique croissant (Industrie 4.0) |
| **Stock** | Les buffers saturés créent des goulots d'étranglement — indicateur de fluidité |

---

## Justification de chaque KPI

### KPI 1 — OEE (Taux de Rendement Global)

**Définition :** Mesure globale de l'efficacité d'une ligne de production, combinant trois sous-indicateurs.

**Formule :**
```
OEE = Disponibilité × Performance × Qualité
```
- Disponibilité = temps Busy / temps total (`tblmachinereport`)
- Performance = temps nominal / temps réel (`tblfinstep` × `tblresourceoperation`)
- Qualité = pièces OK / total pièces (`tblfinorderpos`)

**Pertinence :** L'OEE est le KPI le plus utilisé en industrie manufacturière (norme ISO 22400). Une valeur < 60 % signale une ligne sous-performante. Il synthétise en un chiffre les pertes liées aux arrêts, aux ralentissements et aux rebuts.

**Valeurs observées :** L'OEE calculé se situe autour de 70–80 %, ce qui est cohérent avec une ligne de test pédagogique. La composante Qualité est proche de 95 %, la Performance proche de 90 %, mais la Disponibilité est la plus pénalisante (sessions courtes, arrêts fréquents).

---

### KPI 2 — Taux d'utilisation machine

**Définition :** Proportion du temps pendant lequel chaque machine est en état Busy (en production).

**Formule :** Temps Busy / Temps total par machine

**Pertinence :** Identifier les machines sous-utilisées (goulots aval) ou sur-sollicitées (goulots). Une utilisation < 70 % sur une machine en milieu de ligne indique un déséquilibrage de la ligne.

**Observations :** Les machines de la ligne T'ELEFAN présentent des taux d'utilisation hétérogènes, certaines machines atteignant > 80 % tandis que d'autres restent < 50 %. Cela reflète les temps de cycle nominaux différents entre postes.

---

### KPI 3 — Cadence réelle (pièces/heure)

**Définition :** Nombre de pièces finies par unité de temps de production effective.

**Formule :** Nombre de pièces finies / durée totale de production (heures)

**Pertinence :** La cadence est le premier indicateur de production pour un chef d'atelier. Elle permet de comparer la production réelle à l'objectif nominal et de détecter des dérives dans le temps.

**Observations :** La ventilation mensuelle révèle que les sessions de test sont regroupées sur certaines périodes, avec une cadence variable reflet des durées de sessions.

---

### KPI 4 — Temps moyen de cycle (secondes/pièce)

**Définition :** Durée moyenne d'une étape de production (d'une machine à l'autre), hors étapes en erreur.

**Formule :** Moyenne des durées (End - Start) pour OpNo < 200 et ErrorStep = 0

**Pertinence :** Le temps de cycle est la base du calcul de capacité d'une ligne. S'il dépasse le temps nominal (`tblresourceoperation.WorkingTime`), cela indique une dégradation des équipements ou un problème de réglage.

**Observations :** Le temps de cycle moyen observé est cohérent avec les temps nominaux de la ligne FESTO. Les valeurs aberrantes (> 1 heure) sont filtrées car elles correspondent à des pauses ou redémarrages de session.

---

### KPI 5 — Taux de non-conformité (%)

**Définition :** Proportion de pièces non conformes détectées, combinant deux sources de données.

**Formule :**
```
Taux = (Erreurs ordres + Erreurs capteurs) / (Total ordres + Total capteurs) × 100
```

**Pertinence :** La qualité est un enjeu central en production. Un taux > 2 % signale un problème systémique (réglage machine, pièces entrantes défectueuses). La ventilation par machine permet de localiser la source du problème.

**Observations :** Le taux global est < 2 % sur la ligne T'ELEFAN, ce qui est satisfaisant. Certaines machines présentent toutefois des taux locaux plus élevés. Attention : les codes erreur 5050 et 99 de `tblpartsreport` n'ont pas de correspondance dans `tblerrorcodes`, ce qui peut biaiser légèrement le calcul.

---

### KPI 6 — Temps de détection de défaut (secondes)

**Définition :** Délai moyen entre l'apparition d'une erreur (ErrorL0 ou ErrorL2 = 1) et l'arrêt effectif de la machine (Busy = 0).

**Pertinence :** Un temps de détection long signifie que la machine continue à produire des pièces non conformes après l'apparition du défaut. Réduire ce temps est un objectif clé des systèmes de contrôle qualité en temps réel (Jidoka, industrie 4.0).

**Observations :** Les temps de détection sont très courts sur la ligne FESTO (< 5 secondes en moyenne), ce qui est caractéristique d'un système de détection automatisé efficace.

---

### KPI 7 — Lead Time (heures/unité)

**Définition :** Durée totale entre le début et la fin d'un ordre de fabrication complet.

**Formule :** Moyenne de (End - Start) par ordre, en heures

**Pertinence :** Le lead time est un indicateur de réactivité de la chaîne de production. Un lead time élevé augmente les en-cours, les coûts de stockage et réduit la flexibilité face aux variations de demande. C'est un indicateur clé dans les approches lean.

**Observations :** Le lead time moyen est d'environ 1 à 2 heures sur la ligne T'ELEFAN (sessions de test courtes). Les outliers > 24 h sont filtrés car ils correspondent à des reprises de session après une interruption.

---

### KPI 8 — Temps d'attente en buffer (secondes)

**Définition :** Durée moyenne passée par une pièce dans les zones de stockage intermédiaire (OpNo 210–215).

**Pertinence :** Un temps d'attente buffer élevé indique un déséquilibrage de la ligne (une machine aval plus lente que l'amont) ou une saturation du système de stockage. C'est un indicateur de fluidité de la production (théorie des contraintes).

**Observations :** Les temps d'attente observés sont modérés. Ils augmentent naturellement lorsque la machine aval est arrêtée (maintenance, erreur).

---

### KPI 9-10 — Consommation énergétique (électricité et air comprimé)

**Définition :** Quantité d'énergie consommée par unité produite, pour l'électricité et l'air comprimé.

**Pertinence :** L'énergie représente un coût direct et un enjeu environnemental. Mesurer la consommation par unité permet de détecter des dérives (machine mal réglée, fuites d'air) et de définir des objectifs de réduction.

**Limite identifiée :** Les capteurs réels de la ligne T'ELEFAN ne remontent pas de données dans la base (`ElectricEnergyReal` et `CompressedAirReal` sont à 0 pour toutes les lignes). Ce KPI utilise donc les **valeurs théoriques** de la table `tblresourceoperation`, ce qui donne une estimation de référence mais pas une mesure réelle. Cela est indiqué explicitement dans l'interface.

---

### KPI 11 — Taux d'occupation des buffers (%)

**Définition :** Ratio entre les positions occupées et la capacité totale de chaque zone de stockage.

**Formule :** Positions occupées (PNo > 0) / Capacité totale (Rows × Columns × Sides)

**Pertinence :** Un buffer saturé (> 90 %) bloque la machine amont et crée un goulot d'étranglement en aval. Un buffer vide peut indiquer un problème d'approvisionnement. La surveillance de l'occupation en temps réel est un élément clé des systèmes SCADA/MES.

---

### KPI 12 — Variation du niveau de stock (%)

**Définition :** Amplitude des fluctuations de quantité dans chaque buffer au cours du temps.

**Pertinence :** Une forte variation indique un flux de production irrégulier (production en rafales vs flux tiré). Une faible variation est caractéristique d'un flux continu et régulier (objectif du lean manufacturing).

---

## Ce que les données révèlent

### Points forts de la ligne T'ELEFAN

1. **Qualité satisfaisante** : Le taux de non-conformité reste < 2 %, ce qui indique un processus maîtrisé.
2. **Détection rapide des défauts** : Les erreurs sont détectées en moins de 5 secondes en moyenne, signe d'une instrumentation efficace.
3. **OEE raisonnable** : Autour de 70–80 %, cohérent avec une ligne de test non optimisée pour la production en série.

### Points d'amélioration identifiés

1. **Disponibilité pénalisante** : La composante qui tire l'OEE vers le bas est la disponibilité (arrêts fréquents liés à la nature des sessions de test).
2. **Déséquilibre entre machines** : Les taux d'utilisation très hétérogènes (certaines machines < 50 %) indiquent que la ligne n'est pas équilibrée — certaines machines attendent régulièrement.
3. **Données énergétiques inexploitables** : L'absence de données réelles de consommation est une limite importante pour tout objectif de réduction d'énergie.
4. **Codes erreur orphelins** : Les codes 5050 et 99 présents dans `tblpartsreport` n'ont pas de libellé dans `tblerrorcodes`, rendant leur interprétation impossible sans documentation complémentaire.

### Limites de l'analyse

- Les données couvrent 2016–2025 mais de façon **discontinue** (sessions de test). Les KPIs agrègent toutes les périodes sans distinction, ce qui peut masquer des tendances temporelles.
- La ligne est **pédagogique** : certains comportements (arrêts fréquents, courtes sessions) ne sont pas représentatifs d'une ligne industrielle en production continue.
- L'absence de données énergétiques réelles limite la pertinence de l'axe Énergie à une référence théorique.

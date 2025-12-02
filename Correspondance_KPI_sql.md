# 📊 Indicateurs Clés de Performance (KPI) pour la Production

Ce tableau répertorie les indicateurs clés de performance (KPI) utilisés pour l'analyse des données de production, avec les tables SQL sources et les méthodes de calcul associées.

| Catégorie | KPI (Indicateur) | Table(s) SQL | Colonnes Clés | Méthode de Calcul / Remarque |
| :--- | :--- | :--- | :--- | :--- |
| **Performance** | 1. OEE / TRG (Taux de Rendement Global) | `tblmachinereport`, `tblfinstep`, `tblresourceoperation`, `tblfinorderpos` | `Busy`, `TimeStamp`, `Start`, `End`, `WorkingTime`, `Error` | Combinaison de la **Disponibilité** (`Busy`), de la **Performance** (Réel vs `WorkingTime`) et de la **Qualité** (`Error`). |
| | 2. Taux d'utilisation machine | `tblmachinereport` | `ResourceID`, `TimeStamp`, `Busy` | Somme des durées où le statut `Busy` est actif (généralement `Busy=1`) sur la période d'analyse. |
| | 3. Cadence réelle (pièces/heure) | `tblfinorderpos` | `End`, `ONo` | Compter le nombre de pièces finies (`ONo` / `OPos` avec un timestamp `End` dans l'intervalle) rapporté au temps de production. |
| | 4. Temps moyen de cycle (s/pièce) | `tblfinstep` | `Start`, `End` | Calcul de la moyenne des durées d'opération (`End` - `Start`) au niveau de l'étape de production. |
| **Qualité** | 5. Taux de non-conformité | `tblfinorderpos`, `tblpartsreport` | `Error` (`finorderpos`), `ErrorID` (`partsreport`) | Ratio des pièces marquées comme en erreur ou ayant un `ErrorID` dans `tblpartsreport` par rapport au nombre total de pièces produites. |
| | 6. Temps de détection défaut | `tblmachinereport`, `tblpartsreport` | `TimeStamp`, `ErrorL0/L1/L2` | Différence temporelle entre le déclenchement d'une erreur (`ErrorL0/L1/L2` passe à 1) et l'arrêt machine ou l'enregistrement de l'événement. |
| **Logistique** | 7. Lead Time (Temps de traversée) | `tblfinorder` | `Start`, `End` | Durée totale de fabrication de l'ordre (`End` - `Start` de l'ordre). |
| | 8. Temps d'attente en buffer | `tblfinstep` | `Start`, `End`, `OpNo` | Durée des étapes (`End` - `Start`) dont le code opération (`OpNo`) correspond à une opération de mise en ou de sortie de buffer. |
| | 9. Taux d'occupation des buffers | `tblbufferpos`, `tblbuffer` | `Quantity`, `Rows`, `Columns` | Ratio entre la quantité actuelle de pièces/palettes (via `tblbufferpos`) et la capacité maximale (`Rows` * `Columns` dans `tblbuffer`). |
| | 10. Variation du niveau de stock | `tblbufferpos` | `Quantity`, `TimeStamp` | Analyse de l'évolution de la colonne `Quantity` dans la table des positions de buffer au fil du temps. |
| **Énergie** | 11. Consommation Énergétique (kWh/unit) | `tblfinstep` | `ElectricEnergyReal` | Somme de `ElectricEnergyReal` imputée à chaque pièce (ou ordre) en fonction des étapes réalisées. |
| | 12. Consommation Air Comprimé (L/unit) | `tblfinstep` | `CompressedAirReal` | Somme de `CompressedAirReal` imputée à chaque pièce (ou ordre) en fonction des étapes réalisées. |

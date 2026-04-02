"""
Configuration centralisee de l'application.

Regroupe les seuils d'alerte, les IDs machines, les constantes de
conversion et les parametres de filtrage utilises par les services KPI.
Modifier ces valeurs ici impacte tous les calculs et affichages.
"""

# -- Machines --
# IDs des machines / resources de la ligne FESTO
# 1-8 : postes de production, 9 : robotino, 10 : AGV, 90 : magasin pieces
REAL_MACHINE_IDS: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# -- Filtrage des donnees aberrantes --
MAX_EVENT_DURATION_SEC: int = 86_400        # 24h : au-dela, c'est un gap entre sessions
CYCLE_TIME_MAX_FILTER_SEC: float = 3600.0   # 1h max par etape
DETECTION_TIME_MAX_FILTER_SEC: float = 3600.0
LEAD_TIME_MAX_FILTER_HOURS: float = 24.0
BUFFER_WAIT_MAX_FILTER_SEC: float = 7200.0  # 2h

# -- Seuils d'alerte : OEE --
OEE_CRITICAL_THRESHOLD: float = 60.0
OEE_WARNING_THRESHOLD: float = 85.0

# -- Seuils d'alerte : Utilisation machine --
UTILIZATION_WARNING_THRESHOLD: float = 70.0
UTILIZATION_CRITICAL_THRESHOLD: float = 90.0

# -- Seuils d'alerte : Temps de cycle --
CYCLE_TIME_WARNING_SEC: float = 50.0

# -- Seuils d'alerte : Non-conformite --
NON_CONFORMITY_CRITICAL_PCT: float = 2.0

# -- Seuils d'alerte : Detection defaut --
DETECTION_TIME_CRITICAL_SEC: float = 10.0

# -- Seuils d'alerte : Lead time --
LEAD_TIME_WARNING_HOURS: float = 3.0

# -- Seuils d'alerte : Buffer --
BUFFER_WAIT_WARNING_SEC: float = 300.0
BUFFER_OCC_CRITICAL_PCT: float = 90.0
BUFFER_OCC_WARNING_PCT: float = 80.0

# -- Seuils d'alerte : Stock --
STOCK_VARIATION_WARNING_PCT: float = 20.0
STOCK_VARIATION_CAP_PCT: float = 10.0

# -- Conversion d'unites --
MWS_PER_KWH: int = 3_600_000_000   # 1 kWh = 3.6e9 milliWatt-secondes
MNL_PER_LITER: int = 1_000         # 1 L = 1000 milliNormLitres

# -- Labels mois (francais abrege) --
MONTH_LABELS: dict[int, str] = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Avr',
    5: 'Mai', 6: 'Jui', 7: 'Jul', 8: 'Aou',
    9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec',
}

"""
Couche metier — Calcul des KPIs industriels.

Ce module centralise les 11 fonctions de calcul de KPI du dashboard
T'ELEFAN MES 4.0. Chaque fonction interroge la base MES4 via SQLAlchemy
et retourne un dictionnaire pret a etre consomme par les templates Jinja
ou l'API JSON.

Correspondance KPI <-> Tables SQL
==================================

+-----+-------------------------------+---------------------------------------------------+
| KPI | Fonction                      | Tables sources (colonnes cles)                    |
+-----+-------------------------------+---------------------------------------------------+
|  1  | calculate_oee()               | tblmachinereport (Busy, Duration)                 |
|     |                               | tblfinstep (Start, End, ResourceID, OpNo)         |
|     |                               | tblresourceoperation (WorkingTime)                |
|     |                               | tblfinorderpos (Error)                            |
+-----+-------------------------------+---------------------------------------------------+
|  2  | calculate_utilization()       | tblmachinereport (ResourceID, Busy, Duration)     |
|     |                               | tblresource (ResourceName)                        |
+-----+-------------------------------+---------------------------------------------------+
|  3  | calculate_throughput()        | tblfinorderpos (End)                              |
+-----+-------------------------------+---------------------------------------------------+
|  4  | calculate_cycle_time()        | tblfinstep (Start, End, OpNo, ErrorStep)          |
+-----+-------------------------------+---------------------------------------------------+
|  5  | calculate_non_conformity()    | tblfinorderpos (Error)                            |
|     |                               | tblpartsreport (ErrorID, ResourceID)              |
|     |                               | tblresource (ResourceName)                        |
+-----+-------------------------------+---------------------------------------------------+
|  6  | calculate_detection_time()    | tblmachinereport (ErrorL0, ErrorL2, Busy, TS)     |
|     |                               | tblresource (ResourceName)                        |
+-----+-------------------------------+---------------------------------------------------+
|  7  | calculate_lead_time()         | tblfinorder (Start, End, ONo)                     |
+-----+-------------------------------+---------------------------------------------------+
|  8  | calculate_buffer_wait_time()  | tblfinstep (Start, End, OpNo 210-215)             |
+-----+-------------------------------+---------------------------------------------------+
| 9-10| calculate_energy_summary()    | tblresourceoperation (ElectricEnergy, CompAir)    |
|     |                               | tblfinstep (ResourceID, OpNo, Start, End)         |
+-----+-------------------------------+---------------------------------------------------+
|  11 | calculate_buffer_occupancy()  | tblbuffer (Rows, Columns, Sides)                  |
|     |                               | tblbufferpos (PNo)                                |
+-----+-------------------------------+---------------------------------------------------+
|  12 | calculate_stock_variation()   | tblbuffer, tblbufferpos (Quantity)                |
+-----+-------------------------------+---------------------------------------------------+

Convention de retour :
- Chaque fonction retourne un ``dict`` contenant au minimum une cle ``status``
  ('normal', 'warning', 'critical' ou 'error').
- En cas d'exception, le decorateur ``@_safe_kpi`` capture l'erreur et
  retourne un dict par defaut avec ``status='error'``.
"""

import logging
from functools import wraps
from typing import Any, Callable

import pandas as pd

from . import db
from .models import (
    Buffer,
    BufferPosition,
    MachineReport,
    Order,
    OrderPosition,
    PartsReport,
    Resource,
    ResourceOperation,
    Step,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Constantes
# ============================================================================

# IDs des machines de production reelles (exclut 0, 9, 10, 90 = test/virtuelles)
REAL_MACHINE_IDS: list[int] = [1, 2, 3, 4, 5, 6, 7, 8]

# Duree max d'un evenement en secondes (filtre les gaps entre sessions de test)
MAX_EVENT_DURATION_SEC: int = 86_400  # 24 h

# --- Seuils d'alerte par KPI ---
OEE_CRITICAL_THRESHOLD: float = 60.0       # % OEE en dessous = critique
OEE_WARNING_THRESHOLD: float = 85.0        # % OEE en dessous = warning

UTILIZATION_WARNING_THRESHOLD: float = 70.0  # % utilisation machine

CYCLE_TIME_WARNING_SEC: float = 50.0       # secondes / piece
CYCLE_TIME_MAX_FILTER_SEC: float = 3600.0  # filtre les aberrations

NON_CONFORMITY_CRITICAL_PCT: float = 2.0   # % non-conformite

DETECTION_TIME_CRITICAL_SEC: float = 10.0  # secondes
DETECTION_TIME_MAX_FILTER_SEC: float = 3600.0

LEAD_TIME_WARNING_HOURS: float = 3.0       # heures
LEAD_TIME_MAX_FILTER_HOURS: float = 24.0   # filtre les aberrations

BUFFER_WAIT_WARNING_SEC: float = 300.0     # secondes
BUFFER_WAIT_MAX_FILTER_SEC: float = 7200.0 # 2 h

BUFFER_OCC_CRITICAL_PCT: float = 90.0      # % occupation
BUFFER_OCC_WARNING_PCT: float = 80.0

STOCK_VARIATION_WARNING_PCT: float = 20.0  # % variation
STOCK_VARIATION_CAP_PCT: float = 10.0      # plafond d'affichage

# Conversion d'unites
MWS_PER_KWH: int = 3_600_000_000           # 1 kWh = 3.6e9 milliWatt-secondes
MNL_PER_LITER: int = 1_000                 # 1 L = 1 000 milliNormLitres


# ============================================================================
# Utilitaires internes
# ============================================================================

def _safe_kpi(default_return: dict) -> Callable:
    """Decorateur try/except generique pour les fonctions KPI.

    En cas d'exception non geree, log l'erreur et retourne une copie
    du ``default_return`` enrichie des cles ``status='error'`` et
    ``error=<message>``.

    Args:
        default_return: Dictionnaire de valeurs par defaut a retourner
                        en cas d'erreur.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> dict:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                logger.exception("Erreur KPI %s", func.__name__)
                result = default_return.copy() if isinstance(default_return, dict) else default_return
                if isinstance(result, dict):
                    result['status'] = 'error'
                    result['error'] = str(exc)
                return result
        return wrapper
    return decorator


def _get_machine_durations() -> pd.DataFrame:
    """Calcule les durees entre evenements consecutifs de ``tblmachinereport``.

    Pour chaque machine reelle, trie les evenements par timestamp puis
    calcule la duree de chaque etat par difference avec le timestamp
    suivant. Filtre les durees negatives, nulles et superieures a 24 h
    (gaps inter-sessions).

    Returns:
        DataFrame avec colonnes :
        ``ResourceID``, ``TimeStamp``, ``Busy``, ``ErrorL0``, ``ErrorL2``,
        ``Duration`` (secondes).
    """
    reports = db.session.query(
        MachineReport.ResourceID,
        MachineReport.TimeStamp,
        MachineReport.Busy,
        MachineReport.ErrorL0,
        MachineReport.ErrorL2,
    ).filter(
        MachineReport.ResourceID.in_(REAL_MACHINE_IDS)
    ).order_by(
        MachineReport.ResourceID, MachineReport.TimeStamp
    ).all()

    if not reports:
        return pd.DataFrame()

    df = pd.DataFrame(reports, columns=[
        'ResourceID', 'TimeStamp', 'Busy', 'ErrorL0', 'ErrorL2',
    ])

    # Duree = timestamp suivant - timestamp courant (par machine)
    df['NextTimeStamp'] = df.groupby('ResourceID')['TimeStamp'].shift(-1)
    df['Duration'] = (df['NextTimeStamp'] - df['TimeStamp']).dt.total_seconds()

    # Nettoyage : supprime les NaN, les durees <= 0 et les gaps > 24 h
    df = df.dropna(subset=['Duration'])
    df = df[(df['Duration'] > 0) & (df['Duration'] < MAX_EVENT_DURATION_SEC)]

    return df


def _get_resource_names() -> dict[int, str]:
    """Retourne un dictionnaire ``{ResourceID: ResourceName}`` pour les machines reelles."""
    resources = Resource.query.filter(
        Resource.ResourceID.in_(REAL_MACHINE_IDS)
    ).all()
    return {r.ResourceID: r.ResourceName for r in resources}


# ============================================================================
# KPI 1 : OEE (Taux de Rendement Global)
# ============================================================================

@_safe_kpi({'value': 0, 'availability': 0, 'performance': 0, 'quality': 0})
def calculate_oee() -> dict:
    """Calcule le TRG (OEE) = Disponibilite x Performance x Qualite.

    Formule :
        - **Disponibilite** = temps Busy / temps total
          (source : ``tblmachinereport``)
        - **Performance** = somme(temps nominal) / somme(temps reel)
          (source : ``tblfinstep`` JOIN ``tblresourceoperation``)
        - **Qualite** = pieces OK / total pieces
          (source : ``tblfinorderpos``)

    Returns:
        dict avec cles : value, availability, performance, quality, status.
    """
    # --- Disponibilite ---
    df = _get_machine_durations()
    if df.empty:
        return {
            'value': 0, 'availability': 0, 'performance': 0,
            'quality': 0, 'status': 'critical',
        }

    total_time = df['Duration'].sum()
    busy_time = df[df['Busy'] == 1]['Duration'].sum()
    availability = (busy_time / total_time * 100) if total_time > 0 else 0

    # --- Performance (temps nominal vs temps reel) ---
    steps_with_nominal = db.session.query(
        Step.ResourceID, Step.OpNo, Step.Start, Step.End,
        ResourceOperation.WorkingTime,
    ).join(
        ResourceOperation,
        db.and_(
            Step.ResourceID == ResourceOperation.ResourceID,
            Step.OpNo == ResourceOperation.OpNo,
        ),
    ).filter(
        Step.End.isnot(None),
        Step.Start.isnot(None),
        ResourceOperation.WorkingTime > 0,
    ).all()

    if steps_with_nominal:
        total_nominal = sum(s.WorkingTime for s in steps_with_nominal)
        total_actual = sum(
            (s.End - s.Start).total_seconds()
            for s in steps_with_nominal
            if (s.End - s.Start).total_seconds() > 0
        )
        performance = (total_nominal / total_actual * 100) if total_actual > 0 else 0
        performance = min(performance, 100)  # Plafonner a 100 %
    else:
        performance = 85.0  # Valeur par defaut raisonnable

    # --- Qualite (pieces OK / total) ---
    total_pieces = OrderPosition.query.filter(
        OrderPosition.End.isnot(None)
    ).count()
    error_pieces = OrderPosition.query.filter(
        OrderPosition.End.isnot(None),
        OrderPosition.Error != 0,
    ).count()
    quality = ((total_pieces - error_pieces) / total_pieces * 100) if total_pieces > 0 else 0

    # OEE = produit des trois composantes
    oee = (availability / 100) * (performance / 100) * (quality / 100) * 100

    status = 'critical' if oee < OEE_CRITICAL_THRESHOLD else (
        'warning' if oee < OEE_WARNING_THRESHOLD else 'normal'
    )

    return {
        'value': round(oee, 1),
        'availability': round(availability, 1),
        'performance': round(performance, 1),
        'quality': round(quality, 1),
        'status': status,
    }


# ============================================================================
# KPI 2 : Taux d'utilisation machine
# ============================================================================

@_safe_kpi({'overall': 0, 'by_machine': []})
def calculate_utilization() -> dict:
    """Calcule le taux d'utilisation par machine.

    Formule : duree Busy / duree totale par ResourceID.

    Source : ``tblmachinereport`` (durees calculees par ``_get_machine_durations``).

    Returns:
        dict avec cles : overall, by_machine (liste de dicts), status.
    """
    df = _get_machine_durations()
    if df.empty:
        return {'overall': 0, 'by_machine': [], 'status': 'normal'}

    names = _get_resource_names()

    by_machine = []
    for res_id, group in df.groupby('ResourceID'):
        total = group['Duration'].sum()
        busy = group[group['Busy'] == 1]['Duration'].sum()
        rate = (busy / total * 100) if total > 0 else 0
        by_machine.append({
            'id': int(res_id),
            'name': names.get(res_id, f'Machine {res_id}'),
            'value': round(rate, 1),
        })

    by_machine.sort(key=lambda m: m['id'])
    overall = sum(m['value'] for m in by_machine) / len(by_machine) if by_machine else 0

    return {
        'overall': round(overall, 1),
        'by_machine': by_machine,
        'status': 'warning' if overall < UTILIZATION_WARNING_THRESHOLD else 'normal',
    }


# ============================================================================
# KPI 3 : Cadence reelle (pieces / heure)
# ============================================================================

@_safe_kpi({'value': 0, 'monthly': []})
def calculate_throughput() -> dict:
    """Calcule la cadence reelle en pieces par heure.

    Formule : nombre de pieces finies / duree totale de production (heures).
    Ventilation mensuelle pour le graphique en ligne.

    Source : ``tblfinorderpos`` (colonne End).

    Returns:
        dict avec cles : value, monthly (liste de dicts), status.
    """
    positions = db.session.query(
        OrderPosition.End
    ).filter(
        OrderPosition.End.isnot(None)
    ).order_by(OrderPosition.End).all()

    if len(positions) < 2:
        return {'value': 0, 'monthly': [], 'status': 'normal'}

    total_pieces = len(positions)
    first_end = positions[0].End
    last_end = positions[-1].End
    total_hours = (last_end - first_end).total_seconds() / 3600

    overall = (total_pieces / total_hours) if total_hours > 0 else 0

    # Ventilation mensuelle pour le graphique
    df = pd.DataFrame([{'End': p.End} for p in positions])
    df['month'] = df['End'].dt.to_period('M').astype(str)
    monthly_counts = df.groupby('month').size().reset_index(name='pieces')
    monthly = [
        {'month': row['month'], 'value': int(row['pieces'])}
        for _, row in monthly_counts.iterrows()
    ]

    return {
        'value': round(overall, 1),
        'monthly': monthly,
        'status': 'normal',
    }


# ============================================================================
# KPI 4 : Temps moyen de cycle (secondes / piece)
# ============================================================================

@_safe_kpi({'value': 0, 'count': 0})
def calculate_cycle_time() -> dict:
    """Calcule le temps de cycle moyen des etapes productives.

    Formule : AVG(End - Start) pour les etapes productives
    (OpNo < 200, sans erreur, duree entre 0 et 1 h).

    Source : ``tblfinstep`` (Start, End, OpNo, ErrorStep).

    Returns:
        dict avec cles : value (secondes), count, status.
    """
    steps = Step.query.filter(
        Step.Start.isnot(None),
        Step.End.isnot(None),
        Step.OpNo < 200,             # Exclure les etapes buffer (>= 200)
        Step.ErrorStep == 0,          # Exclure les etapes en erreur
    ).all()

    durations = [
        (s.End - s.Start).total_seconds()
        for s in steps
        if 0 < (s.End - s.Start).total_seconds() < CYCLE_TIME_MAX_FILTER_SEC
    ]

    if not durations:
        return {'value': 0, 'count': 0, 'status': 'normal'}

    avg_time = sum(durations) / len(durations)

    return {
        'value': round(avg_time, 1),
        'count': len(durations),
        'status': 'warning' if avg_time > CYCLE_TIME_WARNING_SEC else 'normal',
    }


# ============================================================================
# KPI 5 : Taux de non-conformite (%)
# ============================================================================

@_safe_kpi({'value': 0, 'rate_orders': 0, 'rate_parts': 0, 'total_pieces': 0, 'total_errors': 0, 'by_machine': []})
def calculate_non_conformity() -> dict:
    """Calcule le taux de non-conformite combine.

    Deux sources de donnees :
    1. ``tblfinorderpos`` : pieces avec Error != 0
    2. ``tblpartsreport`` : detections avec ErrorID != 0

    Le taux combine est la moyenne ponderee par le nombre d'observations.
    Ventilation par machine depuis tblpartsreport.

    Returns:
        dict avec cles : value, rate_orders, rate_parts, total_pieces,
        total_errors, by_machine, status.
    """
    # Source 1 : tblfinorderpos
    total_orders = OrderPosition.query.filter(OrderPosition.End.isnot(None)).count()
    errors_orders = OrderPosition.query.filter(
        OrderPosition.End.isnot(None),
        OrderPosition.Error != 0,
    ).count()
    rate_orders = (errors_orders / total_orders * 100) if total_orders > 0 else 0

    # Source 2 : tblpartsreport
    total_parts = PartsReport.query.count()
    errors_parts = PartsReport.query.filter(PartsReport.ErrorID != 0).count()
    rate_parts = (errors_parts / total_parts * 100) if total_parts > 0 else 0

    # Taux combine (moyenne ponderee par nombre d'observations)
    total_observations = total_orders + total_parts
    combined = (
        (errors_orders + errors_parts) / total_observations * 100
    ) if total_observations > 0 else 0

    # Ventilation par machine (pour le graphique barres)
    reports_by_machine = db.session.query(
        PartsReport.ResourceID,
        db.func.count().label('total'),
        db.func.sum(
            db.case((PartsReport.ErrorID != 0, 1), else_=0)
        ).label('errors'),
    ).group_by(PartsReport.ResourceID).all()

    names = _get_resource_names()
    by_machine = [
        {
            'name': names.get(r.ResourceID, f'Machine {r.ResourceID}'),
            'total': r.total,
            'errors': r.errors,
            'rate': round(r.errors / r.total * 100, 2) if r.total > 0 else 0,
        }
        for r in reports_by_machine
        if r.ResourceID in REAL_MACHINE_IDS
    ]

    return {
        'value': round(combined, 2),
        'rate_orders': round(rate_orders, 2),
        'rate_parts': round(rate_parts, 2),
        'total_pieces': total_orders,
        'total_errors': errors_orders + errors_parts,
        'by_machine': by_machine,
        'status': 'critical' if combined > NON_CONFORMITY_CRITICAL_PCT else 'normal',
    }


# ============================================================================
# KPI 6 : Temps de detection defaut (secondes)
# ============================================================================

@_safe_kpi({'value': 0, 'by_event': [], 'count': 0})
def calculate_detection_time() -> dict:
    """Calcule le temps moyen de detection des defauts.

    Methode : pour chaque front montant d'erreur (ErrorL0 ou ErrorL2
    passant de 0 a 1), mesure le delta jusqu'au prochain evenement
    ou Busy passe a 0 (arret machine).

    Source : ``tblmachinereport`` (ErrorL0, ErrorL2, Busy, TimeStamp).

    Returns:
        dict avec cles : value (secondes), by_event (20 derniers), count, status.
    """
    reports = MachineReport.query.filter(
        MachineReport.ResourceID.in_(REAL_MACHINE_IDS)
    ).order_by(
        MachineReport.ResourceID, MachineReport.TimeStamp
    ).all()

    if not reports:
        return {'value': 0, 'by_event': [], 'count': 0, 'status': 'normal'}

    df = pd.DataFrame([{
        'ResourceID': r.ResourceID,
        'TimeStamp': r.TimeStamp,
        'Busy': r.Busy,
        'ErrorL0': r.ErrorL0,
        'ErrorL2': r.ErrorL2,
    } for r in reports])

    names = _get_resource_names()
    detection_times = []

    for res_id, group in df.groupby('ResourceID'):
        group = group.sort_values('TimeStamp').reset_index(drop=True)

        # Detecter les fronts montants d'erreur (0 -> 1)
        group['PrevErrorL0'] = group['ErrorL0'].shift(1).fillna(0).astype(int)
        group['PrevErrorL2'] = group['ErrorL2'].shift(1).fillna(0).astype(int)

        error_starts = group[
            ((group['ErrorL0'] == 1) & (group['PrevErrorL0'] == 0))
            | ((group['ErrorL2'] == 1) & (group['PrevErrorL2'] == 0))
        ]

        # Pour chaque front montant, chercher le prochain arret machine
        for _, error_event in error_starts.iterrows():
            subsequent = group[
                (group['TimeStamp'] > error_event['TimeStamp'])
                & (group['Busy'] == 0)
            ]
            if not subsequent.empty:
                stop_event = subsequent.iloc[0]
                dt = (stop_event['TimeStamp'] - error_event['TimeStamp']).total_seconds()
                if 0 < dt < DETECTION_TIME_MAX_FILTER_SEC:
                    detection_times.append({
                        'machine': names.get(res_id, f'Machine {res_id}'),
                        'seconds': round(dt, 1),
                        'timestamp': str(error_event['TimeStamp']),
                    })

    avg_time = (
        sum(d['seconds'] for d in detection_times) / len(detection_times)
        if detection_times else 0
    )

    return {
        'value': round(avg_time, 1),
        'by_event': detection_times[-20:],  # 20 derniers pour le graphique
        'count': len(detection_times),
        'status': 'critical' if avg_time > DETECTION_TIME_CRITICAL_SEC else 'normal',
    }


# ============================================================================
# KPI 7 : Lead Time (heures / unite)
# ============================================================================

@_safe_kpi({'value': 0, 'distribution': [], 'count': 0})
def calculate_lead_time() -> dict:
    """Calcule le temps de traversee moyen par ordre de fabrication.

    Formule : AVG(End - Start) en heures, filtre entre 0 et 24 h.

    Source : ``tblfinorder`` (Start, End).

    Returns:
        dict avec cles : value (heures), distribution, count, status.
    """
    orders = Order.query.filter(
        Order.Start.isnot(None),
        Order.End.isnot(None),
    ).all()

    if not orders:
        return {'value': 0, 'distribution': [], 'count': 0, 'status': 'normal'}

    # Filtrer les durees aberrantes (> 24 h = gap inter-sessions)
    valid_orders = []
    for o in orders:
        dt_hours = (o.End - o.Start).total_seconds() / 3600
        if 0 < dt_hours < LEAD_TIME_MAX_FILTER_HOURS:
            valid_orders.append((o, dt_hours))

    if not valid_orders:
        return {'value': 0, 'distribution': [], 'count': 0, 'status': 'normal'}

    durations_hours = [dt for _, dt in valid_orders]
    avg_lt = sum(durations_hours) / len(durations_hours)

    # Distribution pour le scatter plot
    distribution = [
        {
            'order': o.ONo,
            'hours': round(dt, 2),
            'start': str(o.Start),
        }
        for o, dt in valid_orders
    ]

    return {
        'value': round(avg_lt, 1),
        'distribution': distribution,
        'count': len(durations_hours),
        'status': 'warning' if avg_lt > LEAD_TIME_WARNING_HOURS else 'normal',
    }


# ============================================================================
# KPI 8 : Temps d'attente en buffer (secondes)
# ============================================================================

@_safe_kpi({'value': 0, 'by_event': [], 'count': 0})
def calculate_buffer_wait_time() -> dict:
    """Calcule le temps moyen d'attente en zone buffer.

    Formule : AVG(End - Start) pour les etapes avec OpNo entre 210 et 215
    (operations de stockage/destockage), filtre < 2 h.

    Source : ``tblfinstep`` (Start, End, OpNo).

    Returns:
        dict avec cles : value (secondes), by_event, count, status.
    """
    steps = Step.query.filter(
        Step.Start.isnot(None),
        Step.End.isnot(None),
        Step.OpNo.between(210, 215),  # Operations buffer uniquement
    ).order_by(Step.Start).all()

    if not steps:
        return {'value': 0, 'by_event': [], 'count': 0, 'status': 'normal'}

    events = []
    durations = []
    for s in steps:
        dt = (s.End - s.Start).total_seconds()
        if 0 < dt < BUFFER_WAIT_MAX_FILTER_SEC:
            durations.append(dt)
            events.append({
                'timestamp': str(s.Start),
                'seconds': round(dt, 1),
                'op': s.OpNo,
            })

    if not durations:
        return {'value': 0, 'by_event': [], 'count': 0, 'status': 'normal'}

    avg_wait = sum(durations) / len(durations)

    return {
        'value': round(avg_wait, 1),
        'by_event': events,
        'count': len(durations),
        'status': 'warning' if avg_wait > BUFFER_WAIT_WARNING_SEC else 'normal',
    }


# ============================================================================
# KPI 9-10 : Consommation energetique (resume dashboard)
# ============================================================================

@_safe_kpi({'value': 0, 'unit': 'Wh/u', 'air_value': 0, 'air_unit': 'L/u', 'timeline': [], 'note': ''})
def calculate_energy_summary() -> dict:
    """Calcule la consommation energetique par unite produite.

    **Attention** : les valeurs reelles (ElectricEnergyReal, CompressedAirReal)
    sont toujours a 0 dans la base. Ce KPI utilise donc les valeurs
    *theoriques* issues de ``tblresourceoperation``.

    Conversions :
    - Electricite : mWs -> kWh  (1 kWh = 3 600 000 000 mWs)
    - Air comprime : mNl -> L   (1 L = 1 000 mNl)

    Sources : ``tblresourceoperation`` (ElectricEnergy, CompressedAir)
              + ``tblfinstep`` (compte de pieces par operation).

    Returns:
        dict avec cles : value (Wh/u), unit, air_value (L/u), air_unit,
        timeline, status, note.
    """
    # --- Electricite theorique ---
    ops = ResourceOperation.query.filter(
        ResourceOperation.ElectricEnergy > 0
    ).all()

    total_energy_mws = 0
    total_pieces = 0

    for op in ops:
        piece_count = Step.query.filter(
            Step.ResourceID == op.ResourceID,
            Step.OpNo == op.OpNo,
            Step.End.isnot(None),
        ).count()
        total_energy_mws += op.ElectricEnergy * piece_count
        total_pieces = max(total_pieces, piece_count)

    kwh_total = total_energy_mws / MWS_PER_KWH
    kwh_per_unit = (kwh_total / total_pieces) if total_pieces > 0 else 0

    # --- Air comprime theorique ---
    ops_air = ResourceOperation.query.filter(
        ResourceOperation.CompressedAir > 0
    ).all()

    total_air_mnl = 0
    for op in ops_air:
        piece_count = Step.query.filter(
            Step.ResourceID == op.ResourceID,
            Step.OpNo == op.OpNo,
            Step.End.isnot(None),
        ).count()
        total_air_mnl += op.CompressedAir * piece_count

    liters_per_unit = (total_air_mnl / MNL_PER_LITER / total_pieces) if total_pieces > 0 else 0

    # --- Timeline : consommation agregee par heure de production ---
    steps_with_energy = db.session.query(
        Step.Start, Step.End, Step.ResourceID, Step.OpNo,
    ).filter(
        Step.Start.isnot(None),
        Step.End.isnot(None),
        Step.ResourceID.in_(REAL_MACHINE_IDS),
    ).order_by(Step.Start).all()

    hourly: dict[str, int] = {}
    for s in steps_with_energy:
        op = ResourceOperation.query.filter_by(
            ResourceID=s.ResourceID, OpNo=s.OpNo,
        ).first()
        if op and op.ElectricEnergy > 0:
            hour_key = s.Start.strftime('%H:00')
            hourly[hour_key] = hourly.get(hour_key, 0) + op.ElectricEnergy

    timeline = [
        {'period': hour, 'kwh': round(mws / MWS_PER_KWH * 1000, 1)}
        for hour, mws in sorted(hourly.items())
    ]

    return {
        'value': round(kwh_per_unit * 1000, 1),  # Affichage en Wh pour lisibilite
        'unit': 'Wh/u',
        'air_value': round(liters_per_unit, 2),
        'air_unit': 'L/u',
        'timeline': timeline,
        'status': 'normal',
        'note': 'Valeurs theoriques (capteurs reels indisponibles)',
    }


# ============================================================================
# KPI 11 : Taux d'occupation des buffers
# ============================================================================

@_safe_kpi({'value': 0, 'total_capacity': 0, 'occupied': 0, 'by_buffer': []})
def calculate_buffer_occupancy() -> dict:
    """Calcule le taux d'occupation global et par buffer.

    Formule :
    - Capacite par buffer = Rows x Columns x max(Sides, 1)
    - Position occupee si PNo > 0

    Sources : ``tblbuffer`` (dimensions) + ``tblbufferpos`` (PNo).

    Returns:
        dict avec cles : value (%), total_capacity, occupied, by_buffer, status.
    """
    buffers = Buffer.query.all()
    positions = BufferPosition.query.all()

    # Capacite totale = somme des dimensions de chaque buffer
    total_capacity = sum(
        b.Rows * b.Columns * max(b.Sides, 1)
        for b in buffers
    )

    # Positions occupees (PNo > 0 = piece presente)
    occupied = sum(1 for p in positions if p.PNo and p.PNo > 0)
    rate = (occupied / total_capacity * 100) if total_capacity > 0 else 0

    # Ventilation par buffer
    by_buffer = []
    for b in buffers:
        capacity = b.Rows * b.Columns * max(b.Sides, 1)
        buf_positions = [
            p for p in positions
            if p.ResourceId == b.ResourceId and p.BufNo == b.BufNo
        ]
        buf_occupied = sum(1 for p in buf_positions if p.PNo and p.PNo > 0)
        by_buffer.append({
            'name': b.Description or f'Buffer {b.ResourceId}-{b.BufNo}',
            'capacity': capacity,
            'occupied': buf_occupied,
            'rate': round(buf_occupied / capacity * 100, 1) if capacity > 0 else 0,
        })

    status = 'critical' if rate > BUFFER_OCC_CRITICAL_PCT else (
        'warning' if rate > BUFFER_OCC_WARNING_PCT else 'normal'
    )

    return {
        'value': round(rate, 1),
        'total_capacity': total_capacity,
        'occupied': occupied,
        'by_buffer': by_buffer,
        'status': status,
    }


# ============================================================================
# KPI 12 : Variation du niveau de stock (%)
# ============================================================================

@_safe_kpi({'variations': [], 'max_variation': 0})
def calculate_stock_variation() -> dict:
    """Calcule la variation de stock par buffer.

    Methode :
    - Si >= 2 quantites disponibles : delta moyen entre valeurs successives.
    - Sinon : variation basee sur l'ecart entre positions occupees et capacite.

    Le pourcentage est plafonne a ``STOCK_VARIATION_CAP_PCT`` pour l'affichage.

    Sources : ``tblbuffer`` + ``tblbufferpos`` (Quantity).

    Returns:
        dict avec cles : variations (liste), max_variation, status.
    """
    buffers = Buffer.query.all()
    positions = BufferPosition.query.all()

    variations = []
    for b in buffers:
        buf_positions = [
            p for p in positions
            if p.ResourceId == b.ResourceId and p.BufNo == b.BufNo
        ]
        if not buf_positions:
            continue

        quantities = [p.Quantity for p in buf_positions if p.Quantity is not None]
        buffer_name = b.Description or f'Buffer {b.ResourceId}-{b.BufNo}'

        if len(quantities) >= 2:
            # Delta moyen entre quantites successives
            deltas = [abs(quantities[i] - quantities[i - 1]) for i in range(1, len(quantities))]
            avg_delta = sum(deltas) / len(deltas) if deltas else 0
            total_qty = sum(quantities)
            variation_pct = (avg_delta / total_qty * 100) if total_qty > 0 else 0
        else:
            # Fallback : ecart entre occupation et capacite
            capacity = b.Rows * b.Columns * max(b.Sides, 1)
            occupied = sum(1 for p in buf_positions if p.PNo and p.PNo > 0)
            variation_pct = (abs(capacity - occupied) / capacity * 100) if capacity > 0 else 0

        variations.append({
            'buffer': buffer_name,
            'variation_pct': round(min(variation_pct, STOCK_VARIATION_CAP_PCT), 1),
        })

    max_var = max((v['variation_pct'] for v in variations), default=0)

    return {
        'variations': variations,
        'max_variation': round(max_var, 1),
        'status': 'warning' if max_var > STOCK_VARIATION_WARNING_PCT else 'normal',
    }

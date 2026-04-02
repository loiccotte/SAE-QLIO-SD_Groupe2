"""
KPIs Qualite : taux de non-conformite et temps de detection des defauts.

Non-conformite = combine les erreurs des pieces (tblfinorderpos)
et les detections de tblpartsreport pour donner un taux global.
Detection = mesure le temps entre apparition d'une erreur et arret machine.
"""

import pandas as pd
from typing import Optional

from .. import db
from ..models import MachineReport, OrderPosition, PartsReport
from ..config import (
    REAL_MACHINE_IDS,
    NON_CONFORMITY_CRITICAL_PCT,
    DETECTION_TIME_CRITICAL_SEC,
    DETECTION_TIME_MAX_FILTER_SEC,
)
from ._helpers import safe_kpi, get_resource_names, build_time_filter


@safe_kpi({'value': 0, 'rate_orders': 0, 'rate_parts': 0, 'total_pieces': 0, 'total_errors': 0, 'by_machine': [], 'trend': 'stable'})
def calculate_non_conformity(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Taux de non-conformite combine (pieces en erreur + detections)."""

    # Source 1 : pieces avec erreur dans tblfinorderpos
    pos_query = OrderPosition.query.filter(OrderPosition.End.isnot(None))
    for f in build_time_filter(OrderPosition.End, year, month):
        pos_query = pos_query.filter(f)
    total_orders = pos_query.count()

    err_query = OrderPosition.query.filter(OrderPosition.End.isnot(None), OrderPosition.Error != 0)
    for f in build_time_filter(OrderPosition.End, year, month):
        err_query = err_query.filter(f)
    errors_orders = err_query.count()
    rate_orders = (errors_orders / total_orders * 100) if total_orders > 0 else 0

    # Source 2 : detections dans tblpartsreport
    parts_query = PartsReport.query
    for f in build_time_filter(PartsReport.TimeStamp, year, month):
        parts_query = parts_query.filter(f)
    total_parts = parts_query.count()

    err_parts_query = PartsReport.query.filter(PartsReport.ErrorID != 0)
    for f in build_time_filter(PartsReport.TimeStamp, year, month):
        err_parts_query = err_parts_query.filter(f)
    errors_parts = err_parts_query.count()
    rate_parts = (errors_parts / total_parts * 100) if total_parts > 0 else 0

    # Taux combine (pondere par le nombre d'observations)
    total_observations = total_orders + total_parts
    combined = ((errors_orders + errors_parts) / total_observations * 100) if total_observations > 0 else 0

    # Ventilation par machine (depuis tblpartsreport)
    names = get_resource_names()
    reports_query = db.session.query(
        PartsReport.ResourceID,
        db.func.count().label('total'),
        db.func.sum(db.case((PartsReport.ErrorID != 0, 1), else_=0)).label('errors'),
    )
    for f in build_time_filter(PartsReport.TimeStamp, year, month):
        reports_query = reports_query.filter(f)
    reports_by_machine = reports_query.group_by(PartsReport.ResourceID).all()

    by_machine = [
        {'name': names.get(r.ResourceID, f'Machine {r.ResourceID}'),
         'total': r.total, 'errors': r.errors,
         'rate': round(r.errors / r.total * 100, 2) if r.total > 0 else 0}
        for r in reports_by_machine if r.ResourceID in REAL_MACHINE_IDS
    ]

    # Tendance
    trend = 'stable'
    sorted_pos = pos_query.order_by(OrderPosition.End).all()
    if len(sorted_pos) >= 4:
        half = len(sorted_pos) // 2
        r1 = sum(1 for p in sorted_pos[:half] if p.Error != 0) / half * 100
        r2 = sum(1 for p in sorted_pos[half:] if p.Error != 0) / (len(sorted_pos) - half) * 100
        if r2 > r1 * 1.02: trend = 'up'
        elif r2 < r1 * 0.98: trend = 'down'

    return {
        'value': round(combined, 2), 'rate_orders': round(rate_orders, 2),
        'rate_parts': round(rate_parts, 2), 'total_pieces': total_orders,
        'total_errors': errors_orders + errors_parts, 'by_machine': by_machine,
        'status': 'critical' if combined > NON_CONFORMITY_CRITICAL_PCT else 'normal',
        'trend': trend,
    }


@safe_kpi({'value': 0, 'by_event': [], 'count': 0})
def calculate_detection_time(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Temps moyen entre apparition d'un defaut (ErrorL0/L2) et arret (Busy=0)."""
    query = MachineReport.query.filter(MachineReport.ResourceID.in_(REAL_MACHINE_IDS))
    for f in build_time_filter(MachineReport.TimeStamp, year, month):
        query = query.filter(f)
    reports = query.order_by(MachineReport.ResourceID, MachineReport.TimeStamp).all()

    if not reports:
        return {'value': 0, 'by_event': [], 'count': 0, 'status': 'normal'}

    df = pd.DataFrame([{
        'ResourceID': r.ResourceID, 'TimeStamp': r.TimeStamp,
        'Busy': r.Busy, 'ErrorL0': r.ErrorL0, 'ErrorL2': r.ErrorL2,
    } for r in reports])

    names = get_resource_names()
    detection_times = []

    for res_id, group in df.groupby('ResourceID'):
        group = group.sort_values('TimeStamp').reset_index(drop=True)
        group['PrevEL0'] = group['ErrorL0'].shift(1).fillna(0).astype(int)
        group['PrevEL2'] = group['ErrorL2'].shift(1).fillna(0).astype(int)

        # Front montant = erreur passe de 0 a 1
        error_starts = group[
            ((group['ErrorL0'] == 1) & (group['PrevEL0'] == 0))
            | ((group['ErrorL2'] == 1) & (group['PrevEL2'] == 0))
        ]

        for _, evt in error_starts.iterrows():
            # Cherche le prochain arret (Busy=0) apres cette erreur
            subsequent = group[(group['TimeStamp'] > evt['TimeStamp']) & (group['Busy'] == 0)]
            if not subsequent.empty:
                dt = (subsequent.iloc[0]['TimeStamp'] - evt['TimeStamp']).total_seconds()
                if 0 < dt < DETECTION_TIME_MAX_FILTER_SEC:
                    ts = evt['TimeStamp']
                    detection_times.append({
                        'machine': names.get(res_id, f'Machine {res_id}'),
                        'seconds': round(dt, 1),
                        'timestamp': ts.strftime('%H:%M') if hasattr(ts, 'strftime') else str(ts)[11:16],
                    })

    avg_time = sum(d['seconds'] for d in detection_times) / len(detection_times) if detection_times else 0

    return {
        'value': round(avg_time, 1), 'by_event': detection_times[-20:],
        'count': len(detection_times),
        'status': 'critical' if avg_time > DETECTION_TIME_CRITICAL_SEC else 'normal',
    }

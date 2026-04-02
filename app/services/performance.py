"""
KPIs Performance : OEE, utilisation machine, cadence, temps de cycle.

L'OEE combine disponibilite, performance et qualite (norme NF E60-182).
Tous les calculs acceptent un filtre temporel optionnel (year, month)
passe par la sidebar de l'application.
"""

import pandas as pd
from typing import Optional

from .. import db
from ..models import OrderPosition, Step
from ..config import (
    REAL_MACHINE_IDS,
    OEE_CRITICAL_THRESHOLD,
    OEE_WARNING_THRESHOLD,
    UTILIZATION_WARNING_THRESHOLD,
    CYCLE_TIME_WARNING_SEC,
    CYCLE_TIME_MAX_FILTER_SEC,
    MONTH_LABELS,
)
from ._helpers import safe_kpi, get_machine_durations, get_resource_names, build_time_filter


@safe_kpi({'value': 0, 'availability': 0, 'performance': 0, 'quality': 0, 'trend': 'stable'})
def calculate_oee(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """OEE = Disponibilite x Performance x Qualite (NF E60-182).

    Disponibilite = temps Busy / duree cumulee des ordres de fabrication
    Performance   = (nb pieces x cycle ideal) / temps Busy
    Qualite       = pieces conformes / total pieces
    """
    from ..models import Order

    # -- Temps planifie = duree cumulee des OF (filtrees par periode) --
    order_query = Order.query.filter(Order.Start.isnot(None), Order.End.isnot(None))
    for f in build_time_filter(Order.Start, year, month):
        order_query = order_query.filter(f)
    orders = order_query.all()

    if not orders:
        return {'value': 0, 'availability': 0, 'performance': 0,
                'quality': 0, 'status': 'critical'}

    planned_seconds = sum(
        (o.End - o.Start).total_seconds() for o in orders
        if (o.End - o.Start).total_seconds() > 0
    )

    # -- Temps Busy (events machine sur la meme periode) --
    df = get_machine_durations(year, month)
    if df.empty:
        return {'value': 0, 'availability': 0, 'performance': 0,
                'quality': 0, 'status': 'critical'}

    busy_seconds = df[df['Busy'] == 1]['Duration'].sum()
    availability = min((busy_seconds / planned_seconds * 100) if planned_seconds > 0 else 0, 100)

    # -- Performance = (pieces x cycle ideal) / temps Busy --
    pos_query = OrderPosition.query.filter(OrderPosition.End.isnot(None))
    for f in build_time_filter(OrderPosition.End, year, month):
        pos_query = pos_query.filter(f)
    total_pieces = pos_query.count()

    step_query = Step.query.filter(
        Step.Start.isnot(None), Step.End.isnot(None),
        Step.ResourceID.in_(REAL_MACHINE_IDS), Step.ErrorStep == 0,
    )
    for f in build_time_filter(Step.Start, year, month):
        step_query = step_query.filter(f)
    all_steps = step_query.all()

    total_step_time = sum(
        (s.End - s.Start).total_seconds() for s in all_steps
        if 0 < (s.End - s.Start).total_seconds() < 3600
    )

    if total_pieces > 0 and busy_seconds > 0:
        cycle_ideal = total_step_time / total_pieces
        perf = min(total_pieces * cycle_ideal / busy_seconds * 100, 100)
    else:
        perf = 0.0

    # -- Qualite = pieces OK / total --
    err_query = OrderPosition.query.filter(OrderPosition.End.isnot(None), OrderPosition.Error != 0)
    for f in build_time_filter(OrderPosition.End, year, month):
        err_query = err_query.filter(f)
    error_pieces = err_query.count()
    quality = ((total_pieces - error_pieces) / total_pieces * 100) if total_pieces > 0 else 0

    oee = (availability / 100) * (perf / 100) * (quality / 100) * 100
    status = 'critical' if oee < OEE_CRITICAL_THRESHOLD else (
        'warning' if oee < OEE_WARNING_THRESHOLD else 'normal')

    # Tendance (premiere vs deuxieme moitie)
    trend = 'stable'
    if len(orders) >= 4:
        sorted_orders = sorted(orders, key=lambda o: o.Start)
        half = len(sorted_orders) // 2
        first = sum((o.End - o.Start).total_seconds() for o in sorted_orders[:half] if (o.End - o.Start).total_seconds() > 0)
        second = sum((o.End - o.Start).total_seconds() for o in sorted_orders[half:] if (o.End - o.Start).total_seconds() > 0)
        if first > 0 and second > 0:
            if second < first * 0.98: trend = 'up'
            elif second > first * 1.02: trend = 'down'

    return {
        'value': round(oee, 1), 'availability': round(availability, 1),
        'performance': round(perf, 1), 'quality': round(quality, 1),
        'status': status, 'trend': trend,
    }


@safe_kpi({'overall': 0, 'by_machine': [], 'by_month': []})
def calculate_utilization(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Taux d'utilisation par machine = temps AutomaticMode / temps session."""
    df = get_machine_durations(year, month)
    if df.empty:
        return {'overall': 0, 'by_machine': [], 'by_month': [], 'status': 'normal'}

    names = get_resource_names()

    # Par machine
    by_machine = []
    for res_id, group in df.groupby('ResourceID'):
        total = group['Duration'].sum()
        auto = group[group['AutomaticMode'] == 1]['Duration'].sum()
        rate = (auto / total * 100) if total > 0 else 0
        by_machine.append({
            'id': int(res_id),
            'name': names.get(res_id, f'Machine {res_id}'),
            'value': round(rate, 1),
        })
    by_machine.sort(key=lambda m: m['id'])
    overall = sum(m['value'] for m in by_machine) / len(by_machine) if by_machine else 0

    # Par mois
    df['month_num'] = df['TimeStamp'].dt.month
    monthly_rates = []
    for month_num, grp in df.groupby('month_num'):
        total_m = grp['Duration'].sum()
        auto_m = grp[grp['AutomaticMode'] == 1]['Duration'].sum()
        rate_m = (auto_m / total_m * 100) if total_m > 0 else 0
        monthly_rates.append((int(month_num), round(rate_m, 1)))
    monthly_rates.sort(key=lambda x: x[0])
    overall_avg = sum(r for _, r in monthly_rates) / len(monthly_rates) if monthly_rates else overall

    by_month = [
        {'month': MONTH_LABELS.get(mn, str(mn)), 'value': rate,
         'alert': abs(rate - overall_avg) > (overall_avg * 0.10)}
        for mn, rate in monthly_rates
    ]

    return {
        'overall': round(overall, 1), 'by_machine': by_machine, 'by_month': by_month,
        'status': 'warning' if overall < UTILIZATION_WARNING_THRESHOLD else 'normal',
    }


@safe_kpi({'value': 0, 'monthly': [], 'nominal': 60})
def calculate_throughput(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Cadence reelle en pieces/heure sur le temps Busy."""
    pos_query = db.session.query(OrderPosition.End).filter(OrderPosition.End.isnot(None))
    for f in build_time_filter(OrderPosition.End, year, month):
        pos_query = pos_query.filter(f)
    positions = pos_query.order_by(OrderPosition.End).all()

    if len(positions) < 2:
        return {'value': 0, 'monthly': [], 'nominal': 60, 'status': 'normal'}

    df = pd.DataFrame([{'End': p.End} for p in positions])
    df['month'] = df['End'].dt.to_period('M').astype(str)
    monthly = [
        {'month': row['month'], 'value': int(row['pieces'])}
        for _, row in df.groupby('month').size().reset_index(name='pieces').iterrows()
    ]

    machine_df = get_machine_durations(year, month)
    busy_hours = machine_df[machine_df['Busy'] == 1]['Duration'].sum() / 3600 if not machine_df.empty else 0
    overall = (len(positions) / busy_hours) if busy_hours > 0 else 0

    return {'value': round(overall, 1), 'monthly': monthly, 'nominal': 60, 'status': 'normal'}


@safe_kpi({'value': 0, 'count': 0})
def calculate_cycle_time(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Temps de cycle moyen des etapes productives (OpNo < 200, hors erreurs)."""
    query = Step.query.filter(
        Step.Start.isnot(None), Step.End.isnot(None),
        Step.OpNo < 200, Step.ErrorStep == 0,
    )
    for f in build_time_filter(Step.Start, year, month):
        query = query.filter(f)

    durations = [
        (s.End - s.Start).total_seconds() for s in query.all()
        if 0 < (s.End - s.Start).total_seconds() < CYCLE_TIME_MAX_FILTER_SEC
    ]

    if not durations:
        return {'value': 0, 'count': 0, 'status': 'normal'}

    avg_time = sum(durations) / len(durations)
    return {
        'value': round(avg_time, 1), 'count': len(durations),
        'status': 'warning' if avg_time > CYCLE_TIME_WARNING_SEC else 'normal',
    }

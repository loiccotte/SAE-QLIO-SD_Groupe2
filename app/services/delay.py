"""
KPIs Delai : lead time (temps de traversee) et temps d'attente buffer.

Lead time = duree moyenne d'un ordre Start -> End.
Buffer wait = temps passe dans les zones tampon (OpNo 210-215).
"""

from typing import Optional

from ..models import Order, Step
from ..config import (
    LEAD_TIME_WARNING_HOURS, LEAD_TIME_MAX_FILTER_HOURS,
    BUFFER_WAIT_WARNING_SEC, BUFFER_WAIT_MAX_FILTER_SEC,
)
from ._helpers import safe_kpi, build_time_filter


@safe_kpi({'value': 0, 'distribution': [], 'count': 0, 'trend': 'stable'})
def calculate_lead_time(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Temps moyen de traversee d'un OF, en heures."""
    query = Order.query.filter(Order.Start.isnot(None), Order.End.isnot(None))
    for f in build_time_filter(Order.Start, year, month):
        query = query.filter(f)
    orders = query.all()

    if not orders:
        return {'value': 0, 'distribution': [], 'count': 0, 'status': 'normal'}

    # Garder que les ordres dont la duree est realiste (< 24h)
    valid = [(o, (o.End - o.Start).total_seconds() / 3600)
             for o in orders if 0 < (o.End - o.Start).total_seconds() / 3600 < LEAD_TIME_MAX_FILTER_HOURS]

    if not valid:
        return {'value': 0, 'distribution': [], 'count': 0, 'status': 'normal'}

    hours = [dt for _, dt in valid]
    avg = sum(hours) / len(hours)

    distribution = [{'order': o.ONo, 'hours': round(dt, 2), 'start': str(o.Start)} for o, dt in valid]

    # Tendance
    trend = 'stable'
    if len(hours) >= 4:
        half = len(hours) // 2
        a1, a2 = sum(hours[:half]) / half, sum(hours[half:]) / (len(hours) - half)
        if a2 > a1 * 1.02: trend = 'up'
        elif a2 < a1 * 0.98: trend = 'down'

    return {
        'value': round(avg, 1), 'distribution': distribution,
        'count': len(hours),
        'status': 'warning' if avg > LEAD_TIME_WARNING_HOURS else 'normal',
        'trend': trend,
    }


@safe_kpi({'value': 0, 'by_event': [], 'count': 0})
def calculate_buffer_wait_time(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Temps moyen d'attente dans les buffers (OpNo 210-215)."""
    query = Step.query.filter(
        Step.Start.isnot(None), Step.End.isnot(None),
        Step.OpNo.between(210, 215),
    )
    for f in build_time_filter(Step.Start, year, month):
        query = query.filter(f)
    steps = query.order_by(Step.Start).all()

    if not steps:
        return {'value': 0, 'by_event': [], 'count': 0, 'status': 'normal'}

    events, durations = [], []
    for s in steps:
        dt = (s.End - s.Start).total_seconds()
        if 0 < dt < BUFFER_WAIT_MAX_FILTER_SEC:
            durations.append(dt)
            events.append({'timestamp': str(s.Start), 'seconds': round(dt, 1), 'op': s.OpNo})

    if not durations:
        return {'value': 0, 'by_event': [], 'count': 0, 'status': 'normal'}

    avg = sum(durations) / len(durations)
    return {
        'value': round(avg, 1), 'by_event': events, 'count': len(durations),
        'status': 'warning' if avg > BUFFER_WAIT_WARNING_SEC else 'normal',
    }

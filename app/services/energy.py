"""
KPIs Energie : consommation electrique et air comprime par piece.

Les capteurs reels sont a 0 dans la base, on utilise les valeurs
theoriques de tblfinstep (ElectricEnergyCalc, CompressedAirCalc).
Conversions : mWs -> Wh (electricite), mNl -> L (air comprime).
"""

from typing import Optional

from ..models import Step
from ..config import REAL_MACHINE_IDS, MWS_PER_KWH, MNL_PER_LITER
from ._helpers import safe_kpi, build_time_filter


@safe_kpi({'value': 0, 'unit': 'Wh/u', 'air_value': 0, 'air_unit': 'L/u', 'timeline': [], 'note': '', 'trend': 'stable'})
def calculate_energy_summary(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Consommation theorique par piece (electrique + air comprime)."""
    query = Step.query.filter(Step.End.isnot(None), Step.ResourceID.in_(REAL_MACHINE_IDS))
    for f in build_time_filter(Step.End, year, month):
        query = query.filter(f)
    steps = query.all()

    if not steps:
        return {
            'value': 0, 'unit': 'Wh/u', 'air_value': 0, 'air_unit': 'L/u',
            'timeline': [], 'status': 'normal', 'trend': 'stable',
            'note': 'Aucune etape terminee sur cette periode',
        }

    # Totaux energie et air comprime
    total_energy_mws = sum(s.ElectricEnergyCalc or 0 for s in steps)
    total_air_mnl = sum(s.CompressedAirCalc or 0 for s in steps)
    total_pieces = len([s for s in steps if s.OpNo and s.OpNo < 200]) or len(steps)

    kwh_per_unit = (total_energy_mws / MWS_PER_KWH / total_pieces) if total_pieces > 0 else 0
    liters_per_unit = (total_air_mnl / MNL_PER_LITER / total_pieces) if total_pieces > 0 else 0

    # Timeline horaire (repartition de la conso sur la journee)
    hourly: dict[str, int] = {}
    for s in steps:
        energy = s.ElectricEnergyCalc or 0
        if energy > 0 and s.Start:
            hour_key = s.Start.strftime('%H:00')
            hourly[hour_key] = hourly.get(hour_key, 0) + energy

    timeline = [{'period': h, 'kwh': round(v / MWS_PER_KWH * 1000, 1)} for h, v in sorted(hourly.items())]

    # Tendance : derive entre 1ere et 2eme moitie
    status, trend = 'normal', 'stable'
    if len(timeline) >= 4:
        half = len(timeline) // 2
        a1 = sum(t['kwh'] for t in timeline[:half]) / half
        a2 = sum(t['kwh'] for t in timeline[half:]) / (len(timeline) - half)
        if a1 > 0:
            drift = (a2 - a1) / a1 * 100
            if drift > 10: status, trend = 'warning', 'up'
            elif drift < -10: status, trend = 'warning', 'down'

    return {
        'value': round(kwh_per_unit * 1000, 1), 'unit': 'Wh/u',
        'air_value': round(liters_per_unit, 2), 'air_unit': 'L/u',
        'timeline': timeline, 'status': status, 'trend': trend,
        'note': 'Valeurs theoriques (capteurs reels indisponibles)',
    }

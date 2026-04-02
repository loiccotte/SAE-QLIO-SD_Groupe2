"""
KPIs Stock : occupation des buffers et variation du niveau de stock.

L'occupation = remplissage instantane de chaque zone tampon.
La variation = instabilite des niveaux, utile pour detecter les goulots.
Note : ces indicateurs sont des snapshots temps reel, le filtre
temporel n'a pas d'effet (les buffers n'ont pas d'historique).
"""

from typing import Optional

from ..models import Buffer, BufferPosition
from ..config import (
    BUFFER_OCC_CRITICAL_PCT, BUFFER_OCC_WARNING_PCT,
    STOCK_VARIATION_WARNING_PCT, STOCK_VARIATION_CAP_PCT,
)
from ._helpers import safe_kpi


@safe_kpi({'value': 0, 'total_capacity': 0, 'occupied': 0, 'by_buffer': [], 'trend': 'stable'})
def calculate_buffer_occupancy(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Taux d'occupation global et par buffer (snapshot actuel)."""
    buffers = Buffer.query.all()
    positions = BufferPosition.query.all()

    total_capacity = sum(b.Rows * b.Columns * max(b.Sides, 1) for b in buffers)
    occupied = sum(1 for p in positions if p.PNo and p.PNo > 0)
    rate = (occupied / total_capacity * 100) if total_capacity > 0 else 0

    by_buffer = []
    for b in buffers:
        cap = b.Rows * b.Columns * max(b.Sides, 1)
        buf_occ = sum(1 for p in positions
                      if p.ResourceId == b.ResourceId and p.BufNo == b.BufNo and p.PNo and p.PNo > 0)
        by_buffer.append({
            'name': b.Description or f'Buffer {b.ResourceId}-{b.BufNo}',
            'capacity': cap, 'occupied': buf_occ,
            'rate': round(buf_occ / cap * 100, 1) if cap > 0 else 0,
        })

    status = 'critical' if rate > BUFFER_OCC_CRITICAL_PCT else (
        'warning' if rate > BUFFER_OCC_WARNING_PCT else 'normal')

    return {
        'value': round(rate, 1), 'total_capacity': total_capacity,
        'occupied': occupied, 'by_buffer': by_buffer,
        'status': status, 'trend': 'stable',
    }


@safe_kpi({'variations': [], 'max_variation': 0})
def calculate_stock_variation(year: Optional[int] = None, month: Optional[int] = None) -> dict:
    """Variation de stock par buffer (snapshot actuel)."""
    buffers = Buffer.query.all()
    positions = BufferPosition.query.all()

    variations = []
    for b in buffers:
        buf_pos = [p for p in positions if p.ResourceId == b.ResourceId and p.BufNo == b.BufNo]
        if not buf_pos:
            continue

        name = b.Description or f'Buffer {b.ResourceId}-{b.BufNo}'
        quantities = [p.Quantity for p in buf_pos if p.Quantity is not None]

        if len(quantities) >= 2:
            deltas = [abs(quantities[i] - quantities[i - 1]) for i in range(1, len(quantities))]
            avg_delta = sum(deltas) / len(deltas) if deltas else 0
            total_qty = sum(quantities)
            var_pct = (avg_delta / total_qty * 100) if total_qty > 0 else 0
        else:
            cap = b.Rows * b.Columns * max(b.Sides, 1)
            occ = sum(1 for p in buf_pos if p.PNo and p.PNo > 0)
            var_pct = (abs(cap - occ) / cap * 100) if cap > 0 else 0

        variations.append({
            'buffer': name,
            'variation_pct': round(min(var_pct, STOCK_VARIATION_CAP_PCT), 1),
        })

    max_var = max((v['variation_pct'] for v in variations), default=0)
    return {
        'variations': variations, 'max_variation': round(max_var, 1),
        'status': 'warning' if max_var > STOCK_VARIATION_WARNING_PCT else 'normal',
    }

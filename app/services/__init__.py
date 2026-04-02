"""
Package services : calcul des KPIs industriels.

Re-exporte toutes les fonctions de calcul pour que les routes puissent
continuer a faire `from . import services` puis `services.calculate_oee()`.
"""

from .performance import (
    calculate_oee,
    calculate_utilization,
    calculate_throughput,
    calculate_cycle_time,
)
from .quality import (
    calculate_non_conformity,
    calculate_detection_time,
)
from .delay import (
    calculate_lead_time,
    calculate_buffer_wait_time,
)
from .energy import (
    calculate_energy_summary,
)
from .stock import (
    calculate_buffer_occupancy,
    calculate_stock_variation,
)

__all__ = [
    'calculate_oee',
    'calculate_utilization',
    'calculate_throughput',
    'calculate_cycle_time',
    'calculate_non_conformity',
    'calculate_detection_time',
    'calculate_lead_time',
    'calculate_buffer_wait_time',
    'calculate_energy_summary',
    'calculate_buffer_occupancy',
    'calculate_stock_variation',
]

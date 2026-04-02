"""
Helpers partages par tous les modules KPI.

- safe_kpi : decorateur try/except pour ne pas planter toute la page
- get_machine_durations : durees entre events machine (filtre temporel)
- get_resource_names : noms des machines (fallback si table absente)
- build_time_filter : construit les filtres SQLAlchemy depuis year/month
"""

import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd

from .. import db
from ..models import MachineReport
from ..config import REAL_MACHINE_IDS, MAX_EVENT_DURATION_SEC

logger = logging.getLogger(__name__)


def safe_kpi(default_return: dict) -> Callable:
    """Decorateur qui attrape les exceptions dans les fonctions KPI.

    Au lieu de planter la page entiere quand un calcul echoue,
    on retourne un dictionnaire par defaut avec status='error'.
    Ca permet d'afficher les autres KPIs normalement.
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


def build_time_filter(column, year: Optional[int] = None, month: Optional[int] = None) -> list:
    """Construit une liste de filtres SQLAlchemy sur une colonne DateTime.

    Utilise par toutes les fonctions KPI pour filtrer par annee/mois
    quand l'utilisateur selectionne une plage dans la sidebar.
    """
    filters = []
    if year:
        filters.append(db.extract('year', column) == year)
        if month:
            filters.append(db.extract('month', column) == month)
    return filters


def get_machine_durations(year: Optional[int] = None, month: Optional[int] = None) -> pd.DataFrame:
    """Durees entre events consecutifs de tblmachinereport.

    Chaque ligne = un etat machine avec sa duree (diff avec le timestamp suivant).
    On filtre les gaps > 24h (inter-sessions) et les durees invalides.
    Le filtre year/month permet de ne garder que les events d'une periode.
    """
    query = db.session.query(
        MachineReport.ResourceID,
        MachineReport.TimeStamp,
        MachineReport.Busy,
        MachineReport.AutomaticMode,
        MachineReport.ErrorL0,
        MachineReport.ErrorL2,
    ).filter(
        MachineReport.ResourceID.in_(REAL_MACHINE_IDS)
    )

    # Filtre temporel sur le timestamp
    for f in build_time_filter(MachineReport.TimeStamp, year, month):
        query = query.filter(f)

    reports = query.order_by(
        MachineReport.ResourceID, MachineReport.TimeStamp
    ).all()

    if not reports:
        return pd.DataFrame()

    df = pd.DataFrame(reports, columns=[
        'ResourceID', 'TimeStamp', 'Busy', 'AutomaticMode', 'ErrorL0', 'ErrorL2',
    ])

    df['NextTimeStamp'] = df.groupby('ResourceID')['TimeStamp'].shift(-1)
    df['Duration'] = (df['NextTimeStamp'] - df['TimeStamp']).dt.total_seconds()

    df = df.dropna(subset=['Duration'])
    df = df[(df['Duration'] > 0) & (df['Duration'] < MAX_EVENT_DURATION_SEC)]

    return df


def get_resource_names() -> dict[int, str]:
    """Dictionnaire {ResourceID: ResourceName} pour les machines reelles.

    Tente d'abord tblresource ; si la table n'existe pas (dump HeidiSQL),
    utilise des noms par defaut bases sur tbltopology ou fallback generique.
    """
    try:
        from ..models import Resource
        resources = Resource.query.filter(
            Resource.ResourceID.in_(REAL_MACHINE_IDS)
        ).all()
        if resources:
            return {r.ResourceID: r.ResourceName for r in resources}
    except Exception:
        pass

    # Fallback : noms generiques
    return {rid: f'Machine {rid}' for rid in REAL_MACHINE_IDS}

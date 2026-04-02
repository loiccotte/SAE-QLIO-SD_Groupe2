"""
Pages de detail KPI : performance, qualite, delai, energie, stock, carte.

Chaque route recupere le filtre temporel (year/month) depuis la sidebar,
le passe aux services de calcul, et rend le template correspondant.
"""

from flask import current_app, flash, render_template, request

from .. import db, services
from ..auth import login_required
from .dashboard import bp, _get_time_filter

_KPI_ERROR = {'value': None, 'status': 'error', 'error': True}


def _safe_call(fn, label: str, **kwargs) -> dict:
    """Appelle un service KPI avec gestion d'erreur."""
    try:
        return fn(**kwargs)
    except Exception as e:
        current_app.logger.error(f"{label} failed: {e}")
        return _KPI_ERROR.copy()


def _warn_if_errors(*kpis):
    """Flash un warning si au moins un KPI est en erreur."""
    if any(isinstance(k, dict) and k.get('status') == 'error' for k in kpis):
        flash("Certains indicateurs sont temporairement indisponibles.", "warning")


@bp.route('/performance')
@login_required
def performance():
    tf = _get_time_filter()
    oee = _safe_call(services.calculate_oee, 'oee', **tf)
    utilization = _safe_call(services.calculate_utilization, 'utilization', **tf)
    throughput = _safe_call(services.calculate_throughput, 'throughput', **tf)
    cycle_time = _safe_call(services.calculate_cycle_time, 'cycle_time', **tf)
    _warn_if_errors(oee, utilization, throughput, cycle_time)
    return render_template('performance.html', oee=oee, utilization=utilization,
                           throughput=throughput, cycle_time=cycle_time)


@bp.route('/qualite')
@login_required
def qualite():
    tf = _get_time_filter()
    non_conformity = _safe_call(services.calculate_non_conformity, 'non_conformity', **tf)
    detection_time = _safe_call(services.calculate_detection_time, 'detection_time', **tf)
    _warn_if_errors(non_conformity, detection_time)
    return render_template('qualite.html', non_conformity=non_conformity,
                           detection_time=detection_time)


@bp.route('/delai')
@login_required
def delai():
    tf = _get_time_filter()
    lead_time = _safe_call(services.calculate_lead_time, 'lead_time', **tf)
    buffer_wait = _safe_call(services.calculate_buffer_wait_time, 'buffer_wait', **tf)
    _warn_if_errors(lead_time, buffer_wait)
    return render_template('delai.html', lead_time=lead_time, buffer_wait=buffer_wait)


@bp.route('/energie')
@login_required
def energie():
    tf = _get_time_filter()
    energy = _safe_call(services.calculate_energy_summary, 'energy', **tf)
    _warn_if_errors(energy)
    return render_template('energie.html', energy=energy)


@bp.route('/stock')
@login_required
def stock():
    tf = _get_time_filter()
    buffer_occ = _safe_call(services.calculate_buffer_occupancy, 'buffer_occ', **tf)
    stock_var = _safe_call(services.calculate_stock_variation, 'stock_var', **tf)
    _warn_if_errors(buffer_occ, stock_var)
    return render_template('stock.html', buffer_occ=buffer_occ, stock_var=stock_var)


@bp.route('/carte')
@login_required
def carte():
    """Plan interactif de la ligne FESTO avec indicateurs par poste."""
    from ..models import MachineReport, BufferPosition, Buffer
    from ..config import REAL_MACHINE_IDS
    from ..services._helpers import get_machine_durations

    tf = _get_time_filter()
    duration_df = get_machine_durations(**tf)

    machines = []
    for res_id in REAL_MACHINE_IDS:
        last = MachineReport.query.filter_by(ResourceID=res_id).order_by(
            MachineReport.TimeStamp.desc()).first()

        util_pct, busy_pct = 0.0, 0.0
        if not duration_df.empty:
            grp = duration_df[duration_df['ResourceID'] == res_id]
            total = grp['Duration'].sum()
            if total > 0:
                util_pct = round(grp[grp['AutomaticMode'] == 1]['Duration'].sum() / total * 100, 1)
                busy_pct = round(grp[grp['Busy'] == 1]['Duration'].sum() / total * 100, 1)

        machines.append({
            'id': res_id,
            'auto': last.AutomaticMode if last else 0,
            'busy': last.Busy if last else 0,
            'error': (last.ErrorL0 or last.ErrorL2) if last else 0,
            'utilization': util_pct, 'busy_pct': busy_pct,
        })

    buffers = []
    for b in Buffer.query.all():
        cap = b.Rows * b.Columns * max(b.Sides, 1)
        occ = BufferPosition.query.filter_by(
            ResourceId=b.ResourceId, BufNo=b.BufNo
        ).filter(BufferPosition.PNo > 0).count()
        buffers.append({
            'resource_id': b.ResourceId, 'name': b.Description,
            'capacity': cap, 'occupied': occ,
            'rate': round(occ / cap * 100, 1) if cap > 0 else 0,
        })

    return render_template('carte.html', machines=machines, buffers=buffers)

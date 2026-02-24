"""
Routes principales de l'application T'ELEFAN MES 4.0.

Ce module definit le blueprint ``main`` qui regroupe :
- La page d'accueil (redirection vers login)
- Le dashboard global (5 categories de KPI)
- Les 5 pages de detail : Performance, Qualite, Delai, Energie, Stock
- L'endpoint API JSON pour le refresh AJAX

Toutes les routes (sauf ``/``) sont protegees par ``@login_required``.
Les calculs de KPI sont delegues au module ``services``.

Correspondance Route <-> KPIs affiches
=======================================

+-----------------+------------------------------------------------------------+
| Route           | KPIs calcules                                              |
+-----------------+------------------------------------------------------------+
| /dashboard      | OEE, Non-conformite, Lead Time, Energie, Buffers           |
| /performance    | OEE, Utilisation machine, Cadence, Temps de cycle          |
| /qualite        | Non-conformite, Temps de detection                         |
| /delai          | Lead Time, Temps d'attente buffer                          |
| /energie        | Resume energetique (electrique + air comprime)             |
| /stock          | Occupation buffers, Variation de stock                     |
| /api/kpis       | Idem /dashboard (format JSON)                              |
+-----------------+------------------------------------------------------------+
"""

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, url_for

from . import services
from .auth import login_required

bp = Blueprint('main', __name__)

_KPI_ERROR = {'value': None, 'status': 'error', 'error': True}


@bp.route('/')
def index():
    """Redirige vers la page de connexion."""
    return redirect(url_for('auth.login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard global avec les 5 categories de KPI.

    Affiche un resume de chaque categorie sous forme de cartes
    cliquables renvoyant vers les pages de detail.
    """
    kpis = {}

    try:
        kpis['oee'] = services.calculate_oee()
    except Exception as e:
        current_app.logger.error(f"calculate_oee failed: {e}")
        kpis['oee'] = _KPI_ERROR.copy()

    try:
        kpis['non_conformity'] = services.calculate_non_conformity()
    except Exception as e:
        current_app.logger.error(f"calculate_non_conformity failed: {e}")
        kpis['non_conformity'] = _KPI_ERROR.copy()

    try:
        kpis['lead_time'] = services.calculate_lead_time()
    except Exception as e:
        current_app.logger.error(f"calculate_lead_time failed: {e}")
        kpis['lead_time'] = _KPI_ERROR.copy()

    try:
        kpis['energy'] = services.calculate_energy_summary()
    except Exception as e:
        current_app.logger.error(f"calculate_energy_summary failed: {e}")
        kpis['energy'] = _KPI_ERROR.copy()

    try:
        kpis['buffer'] = services.calculate_buffer_occupancy()
    except Exception as e:
        current_app.logger.error(f"calculate_buffer_occupancy failed: {e}")
        kpis['buffer'] = _KPI_ERROR.copy()

    if any(v.get('status') == 'error' for v in kpis.values()):
        flash("Certains indicateurs sont temporairement indisponibles.", "warning")

    return render_template('dashboard.html', kpis=kpis)


@bp.route('/performance')
@login_required
def performance():
    """Page detail Performance : OEE, utilisation machine, cadence, temps de cycle."""
    try:
        oee = services.calculate_oee()
    except Exception as e:
        current_app.logger.error(f"calculate_oee failed: {e}")
        oee = _KPI_ERROR.copy()

    try:
        utilization = services.calculate_utilization()
    except Exception as e:
        current_app.logger.error(f"calculate_utilization failed: {e}")
        utilization = _KPI_ERROR.copy()

    try:
        throughput = services.calculate_throughput()
    except Exception as e:
        current_app.logger.error(f"calculate_throughput failed: {e}")
        throughput = _KPI_ERROR.copy()

    try:
        cycle_time = services.calculate_cycle_time()
    except Exception as e:
        current_app.logger.error(f"calculate_cycle_time failed: {e}")
        cycle_time = _KPI_ERROR.copy()

    kpis_perf = [oee, utilization, throughput, cycle_time]
    if any(isinstance(k, dict) and k.get('status') == 'error' for k in kpis_perf):
        flash("Certains indicateurs sont temporairement indisponibles.", "warning")

    return render_template(
        'performance.html',
        oee=oee,
        utilization=utilization,
        throughput=throughput,
        cycle_time=cycle_time,
    )


@bp.route('/qualite')
@login_required
def qualite():
    """Page detail Qualite : taux de non-conformite, temps de detection."""
    try:
        non_conformity = services.calculate_non_conformity()
    except Exception as e:
        current_app.logger.error(f"calculate_non_conformity failed: {e}")
        non_conformity = _KPI_ERROR.copy()

    try:
        detection_time = services.calculate_detection_time()
    except Exception as e:
        current_app.logger.error(f"calculate_detection_time failed: {e}")
        detection_time = _KPI_ERROR.copy()

    if any(isinstance(k, dict) and k.get('status') == 'error' for k in [non_conformity, detection_time]):
        flash("Certains indicateurs sont temporairement indisponibles.", "warning")

    return render_template(
        'qualite.html',
        non_conformity=non_conformity,
        detection_time=detection_time,
    )


@bp.route('/delai')
@login_required
def delai():
    """Page detail Delai : lead time, temps d'attente buffer."""
    try:
        lead_time = services.calculate_lead_time()
    except Exception as e:
        current_app.logger.error(f"calculate_lead_time failed: {e}")
        lead_time = _KPI_ERROR.copy()

    try:
        buffer_wait = services.calculate_buffer_wait_time()
    except Exception as e:
        current_app.logger.error(f"calculate_buffer_wait_time failed: {e}")
        buffer_wait = _KPI_ERROR.copy()

    if any(isinstance(k, dict) and k.get('status') == 'error' for k in [lead_time, buffer_wait]):
        flash("Certains indicateurs sont temporairement indisponibles.", "warning")

    return render_template(
        'delai.html',
        lead_time=lead_time,
        buffer_wait=buffer_wait,
    )


@bp.route('/energie')
@login_required
def energie():
    """Page detail Energie : consommation electrique et air comprime."""
    try:
        energy = services.calculate_energy_summary()
    except Exception as e:
        current_app.logger.error(f"calculate_energy_summary failed: {e}")
        energy = _KPI_ERROR.copy()

    if isinstance(energy, dict) and energy.get('status') == 'error':
        flash("Certains indicateurs sont temporairement indisponibles.", "warning")

    return render_template(
        'energie.html',
        energy=energy,
    )


@bp.route('/stock')
@login_required
def stock():
    """Page detail Stock : occupation des buffers, variation de stock."""
    try:
        buffer_occ = services.calculate_buffer_occupancy()
    except Exception as e:
        current_app.logger.error(f"calculate_buffer_occupancy failed: {e}")
        buffer_occ = _KPI_ERROR.copy()

    try:
        stock_var = services.calculate_stock_variation()
    except Exception as e:
        current_app.logger.error(f"calculate_stock_variation failed: {e}")
        stock_var = _KPI_ERROR.copy()

    if any(isinstance(k, dict) and k.get('status') == 'error' for k in [buffer_occ, stock_var]):
        flash("Certains indicateurs sont temporairement indisponibles.", "warning")

    return render_template(
        'stock.html',
        buffer_occ=buffer_occ,
        stock_var=stock_var,
    )


@bp.route('/api/kpis')
@login_required
def api_kpis():
    """Endpoint JSON renvoyant les KPIs du dashboard (usage AJAX futur)."""
    kpis = {}

    try:
        kpis['oee'] = services.calculate_oee()
    except Exception as e:
        current_app.logger.error(f"calculate_oee failed: {e}")
        kpis['oee'] = _KPI_ERROR.copy()

    try:
        kpis['non_conformity'] = services.calculate_non_conformity()
    except Exception as e:
        current_app.logger.error(f"calculate_non_conformity failed: {e}")
        kpis['non_conformity'] = _KPI_ERROR.copy()

    try:
        kpis['lead_time'] = services.calculate_lead_time()
    except Exception as e:
        current_app.logger.error(f"calculate_lead_time failed: {e}")
        kpis['lead_time'] = _KPI_ERROR.copy()

    try:
        kpis['energy'] = services.calculate_energy_summary()
    except Exception as e:
        current_app.logger.error(f"calculate_energy_summary failed: {e}")
        kpis['energy'] = _KPI_ERROR.copy()

    try:
        kpis['buffer'] = services.calculate_buffer_occupancy()
    except Exception as e:
        current_app.logger.error(f"calculate_buffer_occupancy failed: {e}")
        kpis['buffer'] = _KPI_ERROR.copy()

    if all(v.get('status') == 'error' for v in kpis.values()):
        return jsonify(kpis), 500

    return jsonify(kpis)

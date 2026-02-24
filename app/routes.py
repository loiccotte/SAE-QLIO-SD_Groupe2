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

from flask import Blueprint, jsonify, redirect, render_template, url_for

from . import services
from .auth import login_required

bp = Blueprint('main', __name__)


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
    kpis = {
        'oee': services.calculate_oee(),
        'non_conformity': services.calculate_non_conformity(),
        'lead_time': services.calculate_lead_time(),
        'energy': services.calculate_energy_summary(),
        'buffer': services.calculate_buffer_occupancy(),
    }
    return render_template('dashboard.html', kpis=kpis)


@bp.route('/performance')
@login_required
def performance():
    """Page detail Performance : OEE, utilisation machine, cadence, temps de cycle."""
    return render_template(
        'performance.html',
        oee=services.calculate_oee(),
        utilization=services.calculate_utilization(),
        throughput=services.calculate_throughput(),
        cycle_time=services.calculate_cycle_time(),
    )


@bp.route('/qualite')
@login_required
def qualite():
    """Page detail Qualite : taux de non-conformite, temps de detection."""
    return render_template(
        'qualite.html',
        non_conformity=services.calculate_non_conformity(),
        detection_time=services.calculate_detection_time(),
    )


@bp.route('/delai')
@login_required
def delai():
    """Page detail Delai : lead time, temps d'attente buffer."""
    return render_template(
        'delai.html',
        lead_time=services.calculate_lead_time(),
        buffer_wait=services.calculate_buffer_wait_time(),
    )


@bp.route('/energie')
@login_required
def energie():
    """Page detail Energie : consommation electrique et air comprime."""
    return render_template(
        'energie.html',
        energy=services.calculate_energy_summary(),
    )


@bp.route('/stock')
@login_required
def stock():
    """Page detail Stock : occupation des buffers, variation de stock."""
    return render_template(
        'stock.html',
        buffer_occ=services.calculate_buffer_occupancy(),
        stock_var=services.calculate_stock_variation(),
    )


@bp.route('/api/kpis')
@login_required
def api_kpis():
    """Endpoint JSON renvoyant les KPIs du dashboard (usage AJAX futur)."""
    kpis = {
        'oee': services.calculate_oee(),
        'non_conformity': services.calculate_non_conformity(),
        'lead_time': services.calculate_lead_time(),
        'energy': services.calculate_energy_summary(),
        'buffer': services.calculate_buffer_occupancy(),
    }
    return jsonify(kpis)

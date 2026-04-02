"""
Routes principales : page d'accueil, dashboard global, API JSON.

Le dashboard affiche les 5 KPIs principaux sous forme de cartes cliquables.
L'API /api/kpis sert au refresh AJAX automatique (toutes les 5 min).
Le filtre temporel (year, month) est passe via query string depuis la sidebar.
"""

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for

from .. import services
from ..auth import login_required

bp = Blueprint('main', __name__)

_KPI_ERROR = {'value': None, 'status': 'error', 'error': True}


def _get_time_filter() -> dict:
    """Recupere year/month depuis les query params de la sidebar."""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    return {'year': year, 'month': month}


def _safe_call(fn, label: str, **kwargs) -> dict:
    """Appelle une fonction KPI avec le filtre temporel, capture les erreurs."""
    try:
        return fn(**kwargs)
    except Exception as e:
        current_app.logger.error(f"{label} failed: {e}")
        return _KPI_ERROR.copy()


@bp.route('/')
def index():
    return redirect(url_for('auth.login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    tf = _get_time_filter()
    kpis = {
        'oee': _safe_call(services.calculate_oee, 'calculate_oee', **tf),
        'non_conformity': _safe_call(services.calculate_non_conformity, 'calculate_non_conformity', **tf),
        'lead_time': _safe_call(services.calculate_lead_time, 'calculate_lead_time', **tf),
        'energy': _safe_call(services.calculate_energy_summary, 'calculate_energy_summary', **tf),
        'buffer': _safe_call(services.calculate_buffer_occupancy, 'calculate_buffer_occupancy', **tf),
    }

    if any(v.get('status') == 'error' for v in kpis.values()):
        flash("Certains indicateurs sont temporairement indisponibles.", "warning")

    return render_template('dashboard.html', kpis=kpis)


@bp.route('/api/kpis')
@login_required
def api_kpis():
    """Endpoint JSON pour le refresh AJAX du dashboard."""
    tf = _get_time_filter()
    kpis = {
        'oee': _safe_call(services.calculate_oee, 'calculate_oee', **tf),
        'non_conformity': _safe_call(services.calculate_non_conformity, 'calculate_non_conformity', **tf),
        'lead_time': _safe_call(services.calculate_lead_time, 'calculate_lead_time', **tf),
        'energy': _safe_call(services.calculate_energy_summary, 'calculate_energy_summary', **tf),
        'buffer': _safe_call(services.calculate_buffer_occupancy, 'calculate_buffer_occupancy', **tf),
    }

    if all(v.get('status') == 'error' for v in kpis.values()):
        return jsonify(kpis), 500
    return jsonify(kpis)


@bp.route('/api/donnees')
@login_required
def api_donnees():
    """Liste les tables disponibles avec nombre de lignes et lien CSV.

    CDC point 4 : "acces aux donnees sources sous forme de lien URL".
    Chaque table est telechargeable en CSV via /api/donnees/<table>.
    """
    from sqlalchemy import text, inspect
    from .. import db

    inspector = inspect(db.engine)
    tables = []
    for table_name in sorted(inspector.get_table_names()):
        try:
            count = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        except Exception:
            count = 0
        tables.append({
            'name': table_name,
            'rows': count,
            'csv_url': f'/api/donnees/{table_name}',
        })
    return jsonify({'tables': tables})


@bp.route('/api/donnees/<table_name>')
@login_required
def api_donnees_csv(table_name: str):
    """Telecharge une table en CSV (acces aux donnees sources brutes)."""
    import csv
    import io
    from flask import Response
    from sqlalchemy import text, inspect
    from .. import db

    # Verifier que la table existe (securite anti-injection)
    inspector = inspect(db.engine)
    if table_name not in inspector.get_table_names():
        return jsonify({'error': f'Table {table_name} introuvable'}), 404

    tf = _get_time_filter()
    rows = db.session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
    columns = db.session.execute(text(f"SELECT * FROM {table_name} LIMIT 0")).keys()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={table_name}.csv'},
    )

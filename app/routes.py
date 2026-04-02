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

import os

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import text

from . import db, services
from .auth import login_required, role_required

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


# ============================================================================
# Configuration Base de Donnees (admin uniquement)
# ============================================================================

def _get_current_db_info() -> dict:
    """Retourne les infos de connexion BDD actuelle."""
    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if uri.startswith('sqlite'):
        return {'type': 'sqlite', 'host': 'Locale (SQLite)', 'status': 'connecte'}
    elif 'mysql' in uri or 'mariadb' in uri:
        # Parse mysql+pymysql://user:pass@host:port/db
        try:
            after_at = uri.split('@')[1] if '@' in uri else ''
            host_part = after_at.split('/')[0] if '/' in after_at else after_at
            db_name = after_at.split('/')[1] if '/' in after_at else 'MES4'
            return {'type': 'mysql', 'host': host_part, 'db': db_name, 'status': 'connecte'}
        except Exception:
            return {'type': 'mysql', 'host': uri, 'status': 'connecte'}
    return {'type': 'inconnu', 'host': uri or 'Non configuree', 'status': 'deconnecte'}


@bp.route('/config-bdd', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def config_bdd():
    """Page de configuration de la connexion base de donnees.

    Permet de tester et appliquer une connexion a une base MariaDB distante
    (ligne de test FESTO) ou de revenir a la base SQLite locale.
    """
    db_info = _get_current_db_info()
    test_result = None

    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'test':
            # Tester la connexion sans l'appliquer
            host = request.form.get('host', '').strip()
            port = request.form.get('port', '3306').strip()
            user = request.form.get('user', '').strip()
            password = request.form.get('password', '')
            dbname = request.form.get('dbname', 'MES4').strip()

            if not host or not user:
                test_result = {'success': False, 'message': 'Adresse IP et utilisateur requis.'}
            else:
                test_uri = f'mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}'
                test_result = _test_db_connection(test_uri)

        elif action == 'connect':
            # Appliquer la connexion
            host = request.form.get('host', '').strip()
            port = request.form.get('port', '3306').strip()
            user = request.form.get('user', '').strip()
            password = request.form.get('password', '')
            dbname = request.form.get('dbname', 'MES4').strip()

            if not host or not user:
                flash('Adresse IP et utilisateur requis.', 'error')
            else:
                new_uri = f'mysql+pymysql://{user}:{password}@{host}:{port}/{dbname}'
                result = _test_db_connection(new_uri)
                if result['success']:
                    _apply_db_connection(new_uri)
                    flash(f'Connexion reussie a {host}:{port}/{dbname} ! Redemarrage necessaire.', 'success')
                    db_info = _get_current_db_info()
                else:
                    flash(f'Echec de connexion : {result["message"]}', 'error')

        elif action == 'reset':
            # Revenir a la base SQLite locale
            _apply_sqlite_connection()
            flash('Connexion reinitialisee vers la base SQLite locale.', 'success')
            db_info = _get_current_db_info()

    return render_template('config_bdd.html', db_info=db_info, test_result=test_result)


def _test_db_connection(uri: str) -> dict:
    """Teste une connexion BDD sans l'appliquer."""
    from sqlalchemy import create_engine
    try:
        engine = create_engine(uri, connect_args={'connect_timeout': 5})
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
            # Verifier que les tables MES4 existent
            tables_check = conn.execute(
                text("SHOW TABLES LIKE 'tblmachinereport'")
            ).fetchone()
            if tables_check:
                row_count = conn.execute(
                    text('SELECT COUNT(*) FROM tblmachinereport')
                ).scalar()
                return {
                    'success': True,
                    'message': f'Connexion OK ! Base MES4 detectee ({row_count} evenements machine).',
                }
            else:
                return {
                    'success': True,
                    'message': 'Connexion OK mais la table tblmachinereport est absente. Verifiez le nom de la base.',
                }
        engine.dispose()
    except Exception as exc:
        msg = str(exc)
        if 'Access denied' in msg:
            return {'success': False, 'message': 'Identifiants incorrects (acces refuse).'}
        elif 'Can\'t connect' in msg or 'Connection refused' in msg or 'timed out' in msg:
            return {'success': False, 'message': 'Impossible de joindre le serveur. Verifiez l\'adresse IP et le port.'}
        elif 'Unknown database' in msg:
            return {'success': False, 'message': 'Base de donnees introuvable. Verifiez le nom (defaut : MES4).'}
        return {'success': False, 'message': f'Erreur : {msg[:200]}'}


def _apply_db_connection(uri: str) -> None:
    """Applique une nouvelle URI de connexion BDD."""
    os.environ['DATABASE_URL'] = uri
    current_app.config['SQLALCHEMY_DATABASE_URI'] = uri
    # Ecrire dans .env pour persister
    _write_env_database_url(uri)


def _apply_sqlite_connection() -> None:
    """Remet la connexion sur la base SQLite locale."""
    import sys
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base, 'data', 'mes4.db')
    uri = f'sqlite:///{db_path}'
    os.environ['DATABASE_URL'] = uri
    current_app.config['SQLALCHEMY_DATABASE_URI'] = uri
    _write_env_database_url(uri)


@bp.route('/import-bdd', methods=['POST'])
@login_required
@role_required('admin')
def import_bdd():
    """Importe un fichier SQL ou SQLite via upload/drag-drop."""
    import shutil
    import tempfile

    uploaded = request.files.get('db_file')
    if not uploaded or uploaded.filename == '':
        flash('Aucun fichier selectionne.', 'error')
        return redirect(url_for('main.config_bdd'))

    filename = uploaded.filename
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

    if ext not in ('sql', 'db', 'sqlite', 'sqlite3'):
        flash('Format non supporte. Utilisez .sql, .db ou .sqlite.', 'error')
        return redirect(url_for('main.config_bdd'))

    import sys
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)

    try:
        if ext == 'sql':
            # Importer le SQL dans une nouvelle base SQLite
            import sqlite3
            db_path = os.path.join(data_dir, 'mes4_import.db')
            conn = sqlite3.connect(db_path)
            sql_content = uploaded.read().decode('utf-8', errors='replace')
            conn.executescript(sql_content)
            conn.close()
            uri = f'sqlite:///{db_path}'
            _apply_db_connection(uri)
            flash(f'Fichier SQL importe avec succes dans {os.path.basename(db_path)}.', 'success')
        else:
            # Fichier .db/.sqlite : copier directement
            db_path = os.path.join(data_dir, 'mes4_import.db')
            uploaded.save(db_path)
            uri = f'sqlite:///{db_path}'
            _apply_db_connection(uri)
            flash(f'Base de donnees {filename} importee avec succes.', 'success')
    except Exception as exc:
        current_app.logger.error(f'Import BDD failed: {exc}')
        flash(f'Erreur lors de l\'import : {str(exc)[:200]}', 'error')

    return redirect(url_for('main.config_bdd'))


def _write_env_database_url(uri: str) -> None:
    """Met a jour DATABASE_URL dans le fichier .env (cree si besoin)."""
    import sys
    if getattr(sys, 'frozen', False):
        # Mode exe : ecrire config.ini a cote de l'exe
        exe_dir = os.path.dirname(sys.executable)
        config_path = os.path.join(exe_dir, 'config.ini')
        import configparser
        config = configparser.ConfigParser()
        if os.path.exists(config_path):
            config.read(config_path, encoding='utf-8')
        if not config.has_section('database'):
            config.add_section('database')
        config.set('database', 'url', uri)
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
    else:
        # Mode dev : ecrire dans .env
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base, '.env')
        lines = []
        found = False
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith('DATABASE_URL='):
                        lines.append(f'DATABASE_URL={uri}\n')
                        found = True
                    else:
                        lines.append(line)
        if not found:
            lines.append(f'DATABASE_URL={uri}\n')
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

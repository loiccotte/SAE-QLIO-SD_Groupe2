"""
Routes d'administration : configuration BDD et import de fichiers.

Ces routes ne sont accessibles qu'aux utilisateurs avec le role admin.
Elles permettent de basculer entre la base SQLite locale et une
connexion MariaDB distante (ligne de test FESTO).
"""

import os

from flask import current_app, flash, redirect, render_template, request, url_for
from sqlalchemy import text

from ..auth import login_required, role_required
from .dashboard import bp


def _get_current_db_info() -> dict:
    """Infos de connexion BDD actuelle (type, host, status)."""
    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if uri.startswith('sqlite'):
        return {'type': 'sqlite', 'host': 'Locale (SQLite)', 'status': 'connecte'}
    elif 'mysql' in uri or 'mariadb' in uri:
        try:
            after_at = uri.split('@')[1] if '@' in uri else ''
            host_part = after_at.split('/')[0] if '/' in after_at else after_at
            db_name = after_at.split('/')[1] if '/' in after_at else 'MES4'
            return {'type': 'mysql', 'host': host_part, 'db': db_name, 'status': 'connecte'}
        except Exception:
            return {'type': 'mysql', 'host': uri, 'status': 'connecte'}
    return {'type': 'inconnu', 'host': uri or 'Non configuree', 'status': 'deconnecte'}


def _test_db_connection(uri: str) -> dict:
    """Teste une connexion BDD sans l'appliquer."""
    from sqlalchemy import create_engine
    try:
        engine = create_engine(uri, connect_args={'connect_timeout': 5})
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
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
    """Applique une nouvelle URI, recree l'engine SQLAlchemy, et persiste.

    Flask-SQLAlchemy 3.x cache les engines dans _app_engines[app][None].
    On dispose l'ancien et on le remplace par un nouvel engine cree avec
    la nouvelle URI, ce qui prend effet immediatement sans redemarrage.
    """
    import sqlalchemy as sa
    from .. import db

    os.environ['DATABASE_URL'] = uri
    current_app.config['SQLALCHEMY_DATABASE_URI'] = uri
    _write_env_database_url(uri)

    # Fermer toutes les sessions existantes
    db.session.remove()

    # Remplacer l'engine dans le cache Flask-SQLAlchemy 3.x
    app = current_app._get_current_object()
    if hasattr(db, '_app_engines') and app in db._app_engines:
        old_engine = db._app_engines[app].get(None)
        if old_engine:
            old_engine.dispose()
        new_engine = sa.engine_from_config(
            {**db._engine_options, 'url': uri}, prefix='',
        )
        db._app_engines[app][None] = new_engine


def _apply_sqlite_connection() -> None:
    """Remet la connexion sur la base SQLite embarquee."""
    import sys
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base, 'data', 'mes4.db')
    uri = f'sqlite:///{db_path}'
    os.environ['DATABASE_URL'] = uri
    current_app.config['SQLALCHEMY_DATABASE_URI'] = uri
    _write_env_database_url(uri)


def _write_env_database_url(uri: str) -> None:
    """Met a jour DATABASE_URL dans .env (dev) ou config.ini (exe).

    En Docker (/.dockerenv), on ne persiste pas dans .env car le fichier
    est monte depuis l'hote et un chemin SQLite absolu du container
    casserait le prochain demarrage.
    """
    # Docker : changement en memoire uniquement (deja fait dans _apply_db_connection)
    if os.path.exists('/.dockerenv'):
        return

    import sys
    if getattr(sys, 'frozen', False):
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
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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


def _sanitize_sql_file(sql_path: str) -> str:
    """Nettoie un fichier SQL des octets nuls et normalise les fins de ligne.

    Les dumps HeidiSQL peuvent contenir des \\x00 parasites (buffer memoire)
    qui font planter MariaDB CLI et sqlite3. On les supprime in-place et
    on retourne le chemin (inchange) pour chainage.
    """
    with open(sql_path, 'rb') as f:
        data = f.read()
    null_count = data.count(b'\x00')
    if null_count == 0:
        return sql_path
    clean = data.replace(b'\x00', b'')
    with open(sql_path, 'wb') as f:
        f.write(clean)
    current_app.logger.info(
        "SQL sanitize: %d octets nuls supprimes de %s", null_count, sql_path,
    )
    return sql_path


def _convert_mysql_to_sqlite(sql_path: str, db_path: str) -> None:
    """Conversion simplifiee MySQL dump -> SQLite.

    Gere les dumps HeidiSQL / mysqldump :
    - Filtre CREATE DATABASE, USE, SET, LOCK, commentaires conditionnels
    - Adapte CREATE TABLE (types, ENGINE, CHARSET, COMMENT, KEY)
    - Gere les INSERT multi-lignes (HeidiSQL : VALUES sur ligne suivante)
    """
    import re
    import sqlite3

    _sanitize_sql_file(sql_path)

    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=OFF")
    conn.execute("PRAGMA synchronous=OFF")

    skip_prefixes = (
        'CREATE DATABASE', 'USE ', 'SET ', 'LOCK ', 'UNLOCK ',
        'DROP DATABASE', 'ALTER DATABASE', '/*!', '--',
    )

    in_create = False
    create_lines: list[str] = []
    in_insert = False
    insert_header = ''
    insert_rows: list[str] = []

    def _clean_create_sql(lines: list[str]) -> str:
        sql = ' '.join(l.strip() for l in lines)
        sql = sql.replace('`', '')
        sql = re.sub(r'\)\s*ENGINE\s*=.*$', ')', sql)
        sql = re.sub(r'\s*AUTO_INCREMENT\s*=?\s*\d*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\s*COLLATE\s+\S+', '', sql)
        sql = re.sub(r'\s*DEFAULT\s+CHARSET\s*=\s*\S+', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r"\s*COMMENT\s+'(?:[^'\\]|\\.)*'", '', sql)
        sql = re.sub(r'\bint\(\d+\)', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\btinyint\(\d+\)', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bsmallint\(\d+\)', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bbigint\(\d+\)', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bmediumint\(\d+\)', 'INTEGER', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bvarchar\(\d+\)', 'TEXT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\blongtext\b', 'TEXT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bmediumtext\b', 'TEXT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\btinytext\b', 'TEXT', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bdouble\b', 'REAL', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bfloat\b', 'REAL', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bdecimal\(\d+,\d+\)', 'REAL', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\benum\([^)]+\)', 'TEXT', sql, flags=re.IGNORECASE)
        # Supprimer les index KEY / UNIQUE KEY en fin de CREATE TABLE
        sql = re.sub(r',\s*(?:UNIQUE\s+)?KEY\s+\w+\s*\([^)]+\)', '', sql)
        return sql

    def _flush_insert(header: str, rows: list[str]) -> None:
        """Execute un INSERT multi-lignes par lots."""
        if not rows:
            return
        clean_header = header.replace('`', '')
        batch: list[str] = []
        for row in rows:
            row = row.strip().rstrip(',').rstrip(';').replace('`', '')
            if row:
                batch.append(row)
            # Executer par lots de 500 lignes pour eviter les limites
            if len(batch) >= 500:
                sql = f"{clean_header} VALUES {','.join(batch)};"
                try:
                    conn.execute(sql)
                except Exception:
                    # Fallback : inserer ligne par ligne
                    for single in batch:
                        try:
                            conn.execute(f"{clean_header} VALUES {single};")
                        except Exception:
                            pass
                batch = []
        if batch:
            sql = f"{clean_header} VALUES {','.join(batch)};"
            try:
                conn.execute(sql)
            except Exception:
                for single in batch:
                    try:
                        conn.execute(f"{clean_header} VALUES {single};")
                    except Exception:
                        pass

    with open(sql_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or any(stripped.upper().startswith(p) for p in skip_prefixes):
                continue

            # Si on est dans un INSERT multi-lignes
            if in_insert:
                # Lignes de donnees commencent par ( ou \t(
                if stripped.startswith('('):
                    insert_rows.append(stripped)
                    # Derniere ligne se termine par ;
                    if stripped.endswith(';'):
                        _flush_insert(insert_header, insert_rows)
                        in_insert = False
                        insert_header = ''
                        insert_rows = []
                    continue
                else:
                    # Ligne inattendue : flush ce qu'on a et sortir du mode insert
                    _flush_insert(insert_header, insert_rows)
                    in_insert = False
                    insert_header = ''
                    insert_rows = []
                    # Continuer le traitement normal de cette ligne

            # DROP TABLE : laisser passer
            if stripped.upper().startswith('DROP TABLE'):
                clean = stripped.replace('`', '')
                try:
                    conn.execute(clean)
                except Exception:
                    pass
                continue

            # CREATE TABLE
            if stripped.upper().startswith('CREATE TABLE'):
                in_create = True
                create_lines = [stripped]
                continue

            if in_create:
                create_lines.append(stripped)
                if re.match(r'\)\s*ENGINE', stripped) or stripped.rstrip(';') == ')':
                    sql = _clean_create_sql(create_lines)
                    try:
                        conn.execute(sql)
                    except Exception:
                        pass
                    in_create = False
                    create_lines = []
                continue

            # INSERT INTO
            if stripped.upper().startswith('INSERT INTO'):
                clean = stripped.replace('`', '')
                # Cas 1 : INSERT complet sur une seule ligne (se termine par ;)
                if stripped.endswith(';'):
                    try:
                        conn.execute(clean)
                    except Exception:
                        pass
                else:
                    # Cas 2 : HeidiSQL multi-lignes — INSERT ... VALUES\n\t(row),\n\t(row);
                    # Extraire le header "INSERT INTO table (cols)"
                    upper = stripped.upper()
                    val_idx = upper.find('VALUES')
                    if val_idx > 0:
                        insert_header = stripped[:val_idx].strip().replace('`', '')
                        # Il peut y avoir des donnees apres VALUES sur la meme ligne
                        after_values = stripped[val_idx + 6:].strip()
                        in_insert = True
                        insert_rows = []
                        if after_values:
                            insert_rows.append(after_values)
                            if after_values.endswith(';'):
                                _flush_insert(insert_header, insert_rows)
                                in_insert = False
                                insert_header = ''
                                insert_rows = []
                    else:
                        # INSERT sans VALUES encore — attendre
                        insert_header = clean
                        in_insert = True
                        insert_rows = []
                continue

    # Flush en cours si fichier coupe
    if in_insert:
        _flush_insert(insert_header, insert_rows)

    conn.commit()
    conn.close()


@bp.route('/config-bdd', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def config_bdd():
    """Configuration de la connexion BDD (test, appliquer, reset)."""
    db_info = _get_current_db_info()
    test_result = None

    if request.method == 'POST':
        action = request.form.get('action', '')

        if action == 'test':
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
            _apply_sqlite_connection()
            flash('Connexion reinitialisee vers la base SQLite locale.', 'success')
            db_info = _get_current_db_info()

    return render_template('config_bdd.html', db_info=db_info, test_result=test_result)


@bp.route('/import-bdd', methods=['POST'])
@login_required
@role_required('admin')
def import_bdd():
    """Importe un fichier SQL ou SQLite via upload/drag-drop."""
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
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)

    try:
        if ext == 'sql':
            # Les dumps MySQL contiennent des commandes incompatibles SQLite
            # (CREATE DATABASE, ENGINE, CHARSET...). On reutilise le convertisseur.
            import sqlite3
            import tempfile
            db_path = os.path.join(data_dir, 'mes4_import.db')

            # Sauvegarder le fichier uploade temporairement
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.sql')
            uploaded.save(tmp.name)
            tmp.close()

            try:
                _convert_mysql_to_sqlite(tmp.name, db_path)
            finally:
                os.unlink(tmp.name)

            uri = f'sqlite:///{db_path}'
            _apply_db_connection(uri)
            flash(f'Fichier SQL importe et converti avec succes.', 'success')
        else:
            db_path = os.path.join(data_dir, 'mes4_import.db')
            uploaded.save(db_path)
            uri = f'sqlite:///{db_path}'
            _apply_db_connection(uri)
            flash(f'Base de donnees {filename} importee avec succes.', 'success')
    except Exception as exc:
        current_app.logger.error(f'Import BDD failed: {exc}')
        flash(f'Erreur lors de l\'import : {str(exc)[:200]}', 'error')

    return redirect(url_for('main.config_bdd'))

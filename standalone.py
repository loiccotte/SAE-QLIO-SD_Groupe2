#!/usr/bin/env python3
"""Point d'entree standalone pour T'ELEFAN MES 4.0.

Ce script est utilise par PyInstaller pour creer l'executable.
Il configure automatiquement :
- La base de donnees SQLite embarquee (ou distante via config.ini)
- Le serveur WSGI waitress (production-ready)
- L'ouverture automatique du navigateur

Priorite de configuration de la base de donnees :
1. Variable d'environnement DATABASE_URL
2. Fichier config.ini a cote de l'executable
3. Base SQLite embarquee (data/mes4.db)
"""

import configparser
import os
import sys
import threading
import webbrowser


def get_exe_dir() -> str:
    """Chemin du dossier contenant l'exe (pour config.ini)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_data_dir() -> str:
    """Chemin des donnees embarquees (templates, static, data).

    PyInstaller 6.x place les donnees dans _internal/ (= sys._MEIPASS).
    En mode dev, c'est le dossier du projet.
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_database_url(exe_dir: str, data_dir: str) -> str:
    """Determine l'URL de la base de donnees avec fallback.

    1. Variable d'environnement DATABASE_URL (priorite max)
    2. Fichier config.ini a cote de l'exe (section [database], cle url)
    3. Base SQLite embarquee dans data_dir/data/mes4.db (defaut)
    """
    # 1. Variable d'environnement
    env_url = os.environ.get('DATABASE_URL')
    if env_url:
        return env_url

    # 2. Fichier config.ini (a cote de l'exe)
    config_path = os.path.join(exe_dir, 'config.ini')
    if os.path.exists(config_path):
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        if config.has_option('database', 'url'):
            url = config.get('database', 'url').strip()
            if url:
                return url

    # 3. Base SQLite embarquee
    db_path = os.path.join(data_dir, 'data', 'mes4.db')
    return f'sqlite:///{db_path}'


def main():
    exe_dir = get_exe_dir()
    data_dir = get_data_dir()

    # Configuration BDD
    db_url = get_database_url(exe_dir, data_dir)
    os.environ['DATABASE_URL'] = db_url
    os.environ.setdefault('SECRET_KEY', 'telefan-mes4-standalone-2026')

    # Verification base SQLite
    if db_url.startswith('sqlite'):
        db_file = db_url.replace('sqlite:///', '')
        if not os.path.exists(db_file):
            print(f"\n  [ERREUR] Base de donnees introuvable : {db_file}")
            print(f"  Lancez d'abord : python scripts/convert_to_sqlite.py")
            input("\n  Appuyez sur Entree pour quitter...")
            sys.exit(1)

    # Import Flask app
    from app import create_app
    app = create_app()

    # Configuration serveur
    config_path = os.path.join(exe_dir, 'config.ini')
    port = 5000
    if os.path.exists(config_path):
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        port = config.getint('app', 'port', fallback=5000)

    # Ouverture automatique du navigateur
    threading.Timer(1.5, lambda: webbrowser.open(f'http://localhost:{port}')).start()

    # Banniere
    db_mode = 'SQLite embarquee' if db_url.startswith('sqlite') else 'Base distante'
    print()
    print("  ============================================================")
    print("  T'ELEFAN MES 4.0 - Dashboard Industriel")
    print("  ============================================================")
    print()
    print(f"  Application : http://localhost:{port}")
    print(f"  Base donnees: {db_mode}")
    print()
    print("  Comptes :")
    print("    admin       / admin123    (administrateur)")
    print("    responsable / resp123     (responsable)")
    print("    operateur   / oper123     (employe)")
    print()
    print("  Fermez cette fenetre pour arreter l'application.")
    print("  ============================================================")
    print()

    # Serveur WSGI production
    from waitress import serve
    serve(app, host='0.0.0.0', port=port, _quiet=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        print()
        print("  ============================================================")
        print("  [ERREUR] L'application a plante :")
        print("  ============================================================")
        traceback.print_exc()
        print()
        input("  Appuyez sur Entree pour quitter...")
        sys.exit(1)

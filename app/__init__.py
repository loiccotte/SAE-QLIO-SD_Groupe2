"""
Application Flask T'ELEFAN MES 4.0 — Factory et initialisation.

Ce module constitue le point d'entree de l'application. Il expose :
- ``db`` : instance SQLAlchemy partagee par tous les modules
- ``create_app()`` : factory Flask qui configure la BDD, enregistre les
  blueprints (routes, auth, export) et gere les erreurs 404.

La connexion a MariaDB est tentee plusieurs fois au demarrage pour
absorber le delai de demarrage du conteneur Docker (race condition).
"""

import logging
import os
import time
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes de configuration
# ---------------------------------------------------------------------------
DB_CONNECT_RETRIES = 5          # Nombre de tentatives de connexion BDD
DB_CONNECT_DELAY_SEC = 3        # Delai entre chaque tentative (secondes)


def create_app() -> Flask:
    """Cree et configure l'application Flask.

    1. Charge la configuration depuis les variables d'environnement.
    2. Initialise SQLAlchemy et tente la connexion a la BDD.
    3. Enregistre les blueprints : ``routes``, ``auth``, ``export``.
    4. Enregistre le handler d'erreur 404.

    Returns:
        L'instance Flask configuree et prete a tourner.
    """
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static',
    )

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,   # Teste chaque connexion avant utilisation
        'pool_recycle': 300,     # Recycle les connexions toutes les 5 min
    }

    db.init_app(app)

    # Tentatives de connexion BDD (absorbe le delai Docker)
    _wait_for_database(app)

    # Enregistrement des blueprints
    with app.app_context():
        from . import auth, export, routes

        app.register_blueprint(routes.bp)
        app.register_blueprint(auth.bp)
        app.register_blueprint(export.bp)

    # Handler 404 personnalise
    @app.errorhandler(404)
    def page_not_found(error):  # noqa: ARG001
        return render_template('404.html'), 404

    return app


def _wait_for_database(app: Flask) -> None:
    """Tente de se connecter a la BDD avec retries.

    En environnement Docker, MariaDB peut ne pas etre pret au demarrage
    de l'application Flask. Cette fonction boucle jusqu'a obtenir une
    connexion ou epuiser les tentatives.

    Args:
        app: L'instance Flask (necessaire pour le contexte applicatif).
    """
    from sqlalchemy import text

    with app.app_context():
        for attempt in range(DB_CONNECT_RETRIES):
            try:
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("Connexion BDD reussie.")
                _log_data_summary(app)
                return
            except Exception as exc:
                if attempt < DB_CONNECT_RETRIES - 1:
                    logger.warning(
                        "BDD non prete (tentative %d/%d) : %s",
                        attempt + 1, DB_CONNECT_RETRIES, exc,
                    )
                    time.sleep(DB_CONNECT_DELAY_SEC)
                else:
                    logger.error(
                        "BDD inaccessible apres %d tentatives : %s",
                        DB_CONNECT_RETRIES, exc,
                    )


def _log_data_summary(app: Flask) -> None:
    """Affiche un resume des donnees presentes dans la BDD au demarrage."""
    from sqlalchemy import text

    tables = [
        ('tblmachinereport', 'Etats machine'),
        ('tblfinstep', 'Etapes de production'),
        ('tblfinorder', 'Ordres de fabrication'),
        ('tblfinorderpos', 'Pieces produites'),
        ('tblpartsreport', 'Rapports detection'),
    ]
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                for table, label in tables:
                    row = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    logger.info("  %s (%s) : %d lignes", table, label, row)
                    if row == 0:
                        logger.warning("  ATTENTION : %s est vide !", table)
        except Exception as exc:
            logger.warning("Impossible de verifier les donnees : %s", exc)

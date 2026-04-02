"""
Package routes : point d'entree unique pour le blueprint principal.

Les routes sont reparties dans trois fichiers par responsabilite :
- dashboard.py : accueil, tableau de bord, API JSON
- kpi_pages.py : pages de detail par categorie KPI
- admin.py : configuration BDD, import fichiers

Tous partagent le meme blueprint 'main' pour garder les url_for
coherents dans les templates (main.dashboard, main.performance, etc.).
"""

# L'import de kpi_pages et admin enregistre leurs routes sur le bp de dashboard
from .dashboard import bp  # noqa: F401
from . import kpi_pages  # noqa: F401
from . import admin  # noqa: F401

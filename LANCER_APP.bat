@echo off
title T'ELEFAN MES 4.0
echo ============================================
echo   T'ELEFAN MES 4.0 - Demarrage
echo ============================================
echo.

:: Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python non trouve. Installez Python 3.10+ depuis python.org
    pause
    exit /b 1
)

:: Creer le venv si absent
if not exist venv (
    echo [1/4] Creation de l'environnement virtuel...
    python -m venv venv
)

:: Activer le venv
echo [2/4] Activation du venv...
call venv\Scripts\activate.bat

:: Installer les dependances
echo [3/4] Installation des dependances...
pip install -r requirements.txt -q

:: Convertir la BDD si absente
if not exist data\mes4.db (
    echo [3.5/4] Conversion de la base de donnees...
    python -c "import sys; sys.path.insert(0,'.'); from app.routes.admin import _convert_mysql_to_sqlite; _convert_mysql_to_sqlite('FestoMES-2026-03-31.sql', 'data/mes4.db')"
)

:: Configurer SQLite pour le local
set DATABASE_URL=sqlite:///data/mes4.db

:: Lancer l'app
echo [4/4] Demarrage de l'application...
echo.
echo   Application : http://localhost:5000
echo   Comptes : admin/admin123, responsable/resp123, operateur/oper123
echo.
start http://localhost:5000
flask run

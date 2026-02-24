@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title T'ELEFAN MES 4.0

echo.
echo ============================================================
echo    T'ELEFAN MES 4.0 - Demarrage de l'application
echo ============================================================
echo.

:: ----------------------------------------------------------------
:: ETAPE 1 — Verifier que Python est installe
:: ----------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe sur cette machine.
    echo.
    echo Pour l'installer :
    echo   1. Aller sur https://www.python.org/downloads/
    echo   2. Telecharger Python 3.10 ou superieur
    echo   3. IMPORTANT : cocher "Add Python to PATH" lors de l'installation
    echo   4. Relancer ce fichier
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER% detecte.

:: ----------------------------------------------------------------
:: ETAPE 2 — Creer l'environnement virtuel si absent
:: ----------------------------------------------------------------
if not exist ".venv\Scripts\activate.bat" (
    echo.
    echo [INFO] Premiere execution : creation de l'environnement Python...
    echo        (cette etape ne s'effectue qu'une seule fois)
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo [ERREUR] Impossible de creer l'environnement virtuel.
        echo          Verifiez que Python est bien installe avec "Add Python to PATH".
        pause
        exit /b 1
    )
    echo [OK] Environnement virtuel cree.
)

:: ----------------------------------------------------------------
:: ETAPE 3 — Activer l'environnement virtuel
:: ----------------------------------------------------------------
call .venv\Scripts\activate.bat
echo [OK] Environnement virtuel active.

:: ----------------------------------------------------------------
:: ETAPE 4 — Installer ou mettre a jour les dependances
:: ----------------------------------------------------------------
echo.
echo [INFO] Verification des dependances Python...
echo        (peut prendre 1-2 minutes lors de la premiere execution)
pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 (
    echo.
    echo [ERREUR] Echec de l'installation des dependances.
    echo          Verifiez votre connexion internet et relancez ce script.
    pause
    exit /b 1
)
echo [OK] Toutes les dependances sont installees.

:: ----------------------------------------------------------------
:: ETAPE 5 — Creer le fichier .env si absent
:: ----------------------------------------------------------------
if not exist ".env" (
    echo.
    echo [INFO] Fichier de configuration absent - creation automatique...
    copy .env.example .env >nul
    echo [OK] Fichier .env cree.
)

:: ----------------------------------------------------------------
:: ETAPE 6 — Verifier que Docker est installe et demarre
:: ----------------------------------------------------------------
echo.
echo [INFO] Verification de Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERREUR] Docker n'est pas installe ou n'est pas demarre.
    echo.
    echo Pour installer Docker Desktop :
    echo   1. Aller sur https://www.docker.com/products/docker-desktop/
    echo   2. Telecharger et installer Docker Desktop
    echo   3. Demarrer Docker Desktop et attendre que le logo baleine
    echo      apparaisse dans la barre des taches
    echo   4. Relancer ce fichier
    echo.
    pause
    exit /b 1
)
echo [OK] Docker est demarre.

:: ----------------------------------------------------------------
:: ETAPE 7 — Demarrer la base de donnees (Docker)
:: ----------------------------------------------------------------
echo.
echo [INFO] Demarrage de la base de donnees...
echo        (premiere fois : telechargement de l'image MariaDB ~500 Mo)
docker compose up -d db phpmyadmin
if errorlevel 1 (
    echo.
    echo [ERREUR] Impossible de demarrer les conteneurs Docker.
    echo          Verifiez que Docker Desktop est bien ouvert.
    pause
    exit /b 1
)

:: ----------------------------------------------------------------
:: ETAPE 8 — Attendre que la base de donnees soit prete
:: ----------------------------------------------------------------
echo.
echo [INFO] Attente de la base de donnees (peut prendre 30-60 secondes)...
set /a RETRY=0

:wait_db
set /a RETRY+=1
if %RETRY% gtr 60 (
    echo.
    echo [ERREUR] La base de donnees n'a pas repondu apres 2 minutes.
    echo          Verifiez l'etat des conteneurs : docker compose logs db
    pause
    exit /b 1
)

powershell -Command "try { $t=New-Object Net.Sockets.TcpClient('localhost',3306); $t.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    set /p =. <nul
    timeout /t 2 >nul
    goto wait_db
)

echo.
echo [OK] Base de donnees accessible.

:: ----------------------------------------------------------------
:: ETAPE 9 — Ouvrir le navigateur automatiquement apres 3 secondes
:: ----------------------------------------------------------------
start "" cmd /c "timeout /t 3 >nul && start http://localhost:5000"

:: ----------------------------------------------------------------
:: ETAPE 10 — Lancer l'application Flask
:: ----------------------------------------------------------------
echo.
echo ============================================================
echo   Application disponible sur : http://localhost:5000
echo   phpMyAdmin disponible sur  : http://localhost:8080
echo   Le navigateur va s'ouvrir automatiquement...
echo.
echo   Comptes de connexion :
echo     admin        /  admin123   (administrateur, acces export)
echo     responsable  /  resp123    (responsable,    acces export)
echo     operateur    /  oper123    (employe,         lecture seule)
echo.
echo   Pour arreter l'application : appuyer sur CTRL+C
echo   Pour arreter la base de donnees : docker compose stop
echo ============================================================
echo.

flask run

echo.
echo Application arretee.
echo Pour arreter aussi la base de donnees : docker compose stop
echo.
pause

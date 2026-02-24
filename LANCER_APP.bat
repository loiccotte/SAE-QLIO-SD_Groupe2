@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title T'ELEFAN MES 4.0

echo.
echo ============================================================
echo    T'ELEFAN MES 4.0 - Demarrage de l'application
echo ============================================================
echo.

:: ----------------------------------------------------------------
:: INIT — Se placer dans le dossier du script (gere les chemins UNC)
:: ----------------------------------------------------------------
pushd "%~dp0"
if errorlevel 1 (
    echo [ERREUR] Impossible d'acceder au dossier du script.
    echo          Verifiez que le chemin est accessible.
    pause
    exit /b 1
)

:: Verifier que pushd n'a pas laisse un chemin UNC
set SCRIPT_PATH=%CD%
if "!SCRIPT_PATH:~0,2!"=="\\" (
    echo.
    echo [ERREUR] Impossible d'acceder au projet via le chemin reseau : %~dp0
    echo.
    echo          Docker ne peut pas monter des dossiers UNC comme volumes.
    echo          Copiez le projet sur un lecteur local ^(ex: C:\Projets\SAE-QLIO-SD^)
    echo          puis relancez ce fichier.
    echo.
    popd
    pause
    exit /b 1
)

:: Avertissement si le lecteur courant n'est pas local connu (C/D/E)
set DRIVE_LETTER=!SCRIPT_PATH:~0,2!
if /i not "!DRIVE_LETTER!"=="C:" (
if /i not "!DRIVE_LETTER!"=="D:" (
if /i not "!DRIVE_LETTER!"=="E:" (
    echo.
    echo [AVERTISSEMENT] Lecteur courant : !DRIVE_LETTER! ^(chemin reseau mappe^)
    echo                 Docker risque de ne pas pouvoir acceder aux fichiers.
    echo                 En cas d'erreur de volume, copiez le projet sur C:\ et relancez.
    echo.
)))

:: ----------------------------------------------------------------
:: ETAPE 1 — Verifier que Docker est installe
:: ----------------------------------------------------------------
echo [INFO] Verification de Docker...
docker --version >nul 2>&1
if errorlevel 1 goto docker_missing

for /f "tokens=3" %%v in ('docker --version 2^>^&1') do set DOCKER_VER=%%v
echo [OK] Docker !DOCKER_VER! detecte.
goto docker_found

:docker_missing
echo.
echo [INFO] Docker n'est pas installe sur cette machine.
echo.

:: Verifier si on a les droits administrateur
net session >nul 2>&1
if errorlevel 1 goto no_admin

:: Tenter une installation automatique via winget
where winget >nul 2>&1
if errorlevel 1 goto no_winget

echo [INFO] Installation automatique de Docker Desktop via winget...
echo        (peut prendre plusieurs minutes selon la connexion)
echo.
winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
if errorlevel 1 goto no_winget

echo.
echo [OK] Docker Desktop a ete installe.
echo.
echo      IMPORTANT : Vous devez maintenant :
echo        1. Redemarrer votre ordinateur
echo        2. Lancer Docker Desktop depuis le menu Demarrer
echo        3. Attendre que le logo baleine apparaisse dans la barre des taches
echo        4. Relancer ce fichier
echo.
popd
pause
exit /b 0

:no_admin
echo [AVERTISSEMENT] Droits administrateur non disponibles sur cette machine.
echo                 L'installation automatique de Docker est impossible.
echo.
echo          Solutions :
echo            - Demander a votre administrateur systeme d'installer Docker Desktop
echo            - Ou executer ce fichier en tant qu'administrateur
echo              (clic droit ^> Executer en tant qu'administrateur)
echo.

:no_winget
echo [INFO] Ouverture de la page de telechargement Docker Desktop...
start "" "https://www.docker.com/products/docker-desktop/"
echo.
echo        Pour installer Docker Desktop manuellement (droits admin requis) :
echo          1. Telecharger et executer l'installeur depuis la page qui vient de s'ouvrir
echo          2. Redemarrer l'ordinateur si demande
echo          3. Lancer Docker Desktop depuis le menu Demarrer
echo          4. Attendre que le logo baleine apparaisse dans la barre des taches
echo          5. Relancer ce fichier
echo.
popd
pause
exit /b 1

:docker_found

:: ----------------------------------------------------------------
:: ETAPE 2 — Verifier que le daemon Docker est demarre
:: ----------------------------------------------------------------
echo.
echo [INFO] Verification que Docker Desktop est demarre...
docker info >nul 2>&1
if not errorlevel 1 goto daemon_ready

echo [INFO] Docker Desktop est installe mais pas encore demarre.
echo        Tentative de lancement automatique...
echo.
start "" "Docker Desktop"

:: Attendre jusqu'a 90 secondes que le daemon reponde
set /a WAIT=0

:wait_daemon
set /a WAIT+=1
if !WAIT! gtr 30 (
    echo.
    echo [ERREUR] Docker Desktop n'a pas demarre apres 90 secondes.
    echo.
    echo          Solutions :
    echo            1. Ouvrir Docker Desktop manuellement depuis le menu Demarrer
    echo            2. Attendre que le logo baleine apparaisse dans la barre des taches
    echo            3. Relancer ce fichier
    echo.
    popd
    pause
    exit /b 1
)
set /p =. <nul
timeout /t 3 >nul
docker info >nul 2>&1
if errorlevel 1 goto wait_daemon

echo.
echo [OK] Docker Desktop est maintenant demarre.
goto daemon_done

:daemon_ready
echo [OK] Docker Desktop est demarre.

:daemon_done

:: ----------------------------------------------------------------
:: ETAPE 3 — Creer le fichier .env si absent
:: ----------------------------------------------------------------
if exist ".env" goto env_exists

echo.
echo [INFO] Fichier de configuration absent - creation automatique...
(
    echo # ============================================================
    echo # Variables d'environnement — T'ELEFAN MES 4.0
    echo # Genere automatiquement par LANCER_APP.bat
    echo # ============================================================
    echo.
    echo # Connexion a la base MariaDB dans Docker Compose
    echo DATABASE_URL=mysql+pymysql://example_user:example_password@db:3306/MES4
    echo.
    echo SECRET_KEY=exemple-secret-key-2025
    echo.
    echo FLASK_APP=app.run:app
    echo FLASK_DEBUG=1
) > .env
echo [OK] Fichier .env cree (mode Docker, DATABASE_URL pointe vers "db").

:env_exists

:: ----------------------------------------------------------------
:: ETAPE 4 — Demarrer tous les conteneurs (db + adminer + app)
:: ----------------------------------------------------------------
echo.
echo [INFO] Demarrage des conteneurs Docker...
echo        (premiere fois : telechargement des images ~600 Mo, peut prendre quelques minutes)
docker compose up -d
if errorlevel 1 (
    echo.
    echo [ERREUR] Impossible de demarrer les conteneurs Docker.
    echo.
    echo          Diagnostics utiles :
    echo            docker compose logs db
    echo            docker compose logs app
    echo.
    echo          Causes frequentes :
    echo            - Un port est deja utilise ^(3306, 5000 ou 8080^)
    echo            - Le dossier du projet n'est pas partage dans Docker Desktop
    echo              ^(Parametres Docker ^> Resources ^> File sharing^)
    echo.
    popd
    pause
    exit /b 1
)

:: ----------------------------------------------------------------
:: ETAPE 5 — Attendre que l'application Flask soit accessible (port 5000)
:: ----------------------------------------------------------------
echo.
echo [INFO] Attente du demarrage de l'application (peut prendre 30-60 secondes)...
set /a RETRY=0

:wait_app
set /a RETRY+=1
if !RETRY! gtr 60 (
    echo.
    echo [ERREUR] L'application n'a pas repondu apres 2 minutes.
    echo.
    echo          Verifiez les logs :
    echo            docker compose logs app
    echo            docker compose logs db
    echo.
    popd
    pause
    exit /b 1
)

curl -s -o nul http://localhost:5000 >nul 2>&1
if errorlevel 1 (
    set /p =. <nul
    timeout /t 2 >nul
    goto wait_app
)

echo.
echo [OK] Application accessible.

:: ----------------------------------------------------------------
:: ETAPE 6 — Ouvrir le navigateur automatiquement
:: ----------------------------------------------------------------
start "" "http://localhost:5000"

:: ----------------------------------------------------------------
:: ETAPE 7 — Afficher le resume
:: ----------------------------------------------------------------
echo.
echo ============================================================
echo   Application disponible sur : http://localhost:5000
echo   Adminer (BDD)  disponible sur  : http://localhost:8080
echo.
echo   Comptes de connexion :
echo     admin        /  admin123   (administrateur, acces export)
echo     responsable  /  resp123    (responsable,    acces export)
echo     operateur    /  oper123    (employe,         lecture seule)
echo.
echo   Commandes utiles :
echo     Arreter les conteneurs  : docker compose stop
echo     Voir les logs de l'app  : docker compose logs app
echo     Supprimer les conteneurs: docker compose down
echo.
echo   Le navigateur a ete ouvert automatiquement.
echo   Fermez cette fenetre quand vous avez fini.
echo ============================================================
echo.

popd
pause

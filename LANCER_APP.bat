@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title T'ELEFAN MES 4.0

:: Detecter mode CI (GitHub Actions definit CI=true) — desactive pause et navigateur
set INTERACTIVE=1
if defined CI set INTERACTIVE=0

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
    if "%INTERACTIVE%"=="1" pause
    exit /b 1
)

:: Verifications de chemin (ignorees en mode CI — environnement controle)
if "%INTERACTIVE%"=="0" goto skip_path_checks

:: Detecter un chemin UNC (\\serveur\partage) — Docker ne peut pas monter ces chemins
set SCRIPT_PATH=%~dp0
if "!SCRIPT_PATH:~0,2!"=="\\" (
    echo.
    echo [ERREUR] Ce projet est sur un chemin reseau UNC : !SCRIPT_PATH!
    echo.
    echo          Docker ne peut pas monter des dossiers UNC comme volumes.
    echo          Copiez le projet sur un lecteur local (ex: C:\Projets\SAE-QLIO-SD)
    echo          puis relancez ce fichier.
    echo.
    popd
    pause
    exit /b 1
)

:: Avertissement chemin reseau mappe (ex: Z:\...)
set DRIVE_LETTER=%~d0
if /i not "%DRIVE_LETTER%"=="C:" (
if /i not "%DRIVE_LETTER%"=="D:" (
if /i not "%DRIVE_LETTER%"=="E:" (
    echo.
    echo [AVERTISSEMENT] Le projet se trouve sur le lecteur %DRIVE_LETTER%
    echo                 Si c'est un lecteur reseau mappe, Docker risque de ne pas
    echo                 pouvoir acceder aux fichiers (partage de lecteur non configure).
    echo                 En cas d'erreur, copiez le projet sur C:\ et relancez.
    echo.
))))

:skip_path_checks

:: En mode CI, Docker est preinstalle sur le runner — passer directement a compose
if "%INTERACTIVE%"=="0" goto run_compose

:: ----------------------------------------------------------------
:: ETAPE 1 — Verifier que Docker est installe
:: ----------------------------------------------------------------
echo [INFO] Verification de Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [INFO] Docker n'est pas installe sur cette machine.
    echo.

    :: Verifier si on a les droits administrateur
    net session >nul 2>&1
    set IS_ADMIN=0
    if not errorlevel 1 set IS_ADMIN=1

    :: Tenter une installation automatique via winget (droits admin requis)
    if "%IS_ADMIN%"=="1" (
        where winget >nul 2>&1
        if not errorlevel 1 (
            echo [INFO] Installation automatique de Docker Desktop via winget...
            echo        (peut prendre plusieurs minutes selon la connexion)
            echo.
            winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
            if not errorlevel 1 (
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
                if "%INTERACTIVE%"=="1" pause
                exit /b 0
            ) else (
                echo.
                echo [AVERTISSEMENT] L'installation via winget a echoue.
            )
        )
    ) else (
        echo [AVERTISSEMENT] Droits administrateur non disponibles sur cette machine.
        echo                 L'installation automatique de Docker est impossible.
        echo.
        echo          Solutions :
        echo            - Demander a votre administrateur systeme d'installer Docker Desktop
        echo            - Ou executer ce fichier en tant qu'administrateur si vous avez
        echo              les identifiants (clic droit > Executer en tant qu'administrateur)
        echo.
    )

    :: Fallback : ouvrir la page de telechargement manuellement
    echo.
    if "%INTERACTIVE%"=="1" (
        echo [INFO] Ouverture de la page de telechargement Docker Desktop...
        start "" "https://www.docker.com/products/docker-desktop/"
    )
    echo        Pour installer Docker Desktop manuellement (droits admin requis) :
    echo          1. Telecharger et executer l'installeur depuis la page qui vient de s'ouvrir
    echo          2. Redemarrer l'ordinateur si demande
    echo          3. Lancer Docker Desktop depuis le menu Demarrer
    echo          4. Attendre que le logo baleine apparaisse dans la barre des taches
    echo          5. Relancer ce fichier
    echo.
    popd
    if "%INTERACTIVE%"=="1" pause
    exit /b 1
)

for /f "tokens=3" %%v in ('docker --version 2^>^&1') do set DOCKER_VER=%%v
echo [OK] Docker %DOCKER_VER% detecte.

:: ----------------------------------------------------------------
:: ETAPE 2 — Verifier que le daemon Docker est demarre
:: ----------------------------------------------------------------
echo.
echo [INFO] Verification que Docker Desktop est demarre...
docker info >nul 2>&1
if errorlevel 1 (
    echo [INFO] Docker Desktop est installe mais pas encore demarre.
    echo        Tentative de lancement automatique...
    echo.

    :: Tenter de lancer Docker Desktop (mode interactif seulement)
    if "%INTERACTIVE%"=="1" start "" "Docker Desktop"

    :: Attendre jusqu'a 90 secondes que le daemon reponde
    set /a WAIT=0
    :wait_daemon
    set /a WAIT+=1
    if %WAIT% gtr 30 (
        echo.
        echo [ERREUR] Docker Desktop n'a pas demarre apres 90 secondes.
        echo.
        echo          Solutions :
        echo            1. Ouvrir Docker Desktop manuellement depuis le menu Demarrer
        echo            2. Attendre que le logo baleine apparaisse dans la barre des taches
        echo            3. Relancer ce fichier
        echo.
        popd
        if "%INTERACTIVE%"=="1" pause
        exit /b 1
    )
    set /p =. <nul
    timeout /t 3 >nul
    docker info >nul 2>&1
    if errorlevel 1 goto wait_daemon

    echo.
    echo [OK] Docker Desktop est maintenant demarre.
) else (
    echo [OK] Docker Desktop est demarre.
)

:run_compose
:: ----------------------------------------------------------------
:: ETAPE 3 — Creer le fichier .env si absent
::           (avec DATABASE_URL pointant vers le service Docker "db")
:: ----------------------------------------------------------------
if not exist ".env" (
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
)

:: ----------------------------------------------------------------
:: ETAPE 4 — Demarrer tous les conteneurs (db + phpmyadmin + app)
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
    echo            - Un port est deja utilise (3306, 5000 ou 8080)
    echo            - Le dossier du projet n'est pas partage dans Docker Desktop
    echo              (Parametres Docker > Resources > File sharing)
    echo.
    popd
    if "%INTERACTIVE%"=="1" pause
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
if %RETRY% gtr 60 (
    echo.
    echo [ERREUR] L'application n'a pas repondu apres 2 minutes.
    echo.
    echo          Verifiez les logs :
    echo            docker compose logs app
    echo            docker compose logs db
    echo.
    popd
    if "%INTERACTIVE%"=="1" pause
    exit /b 1
)

powershell -Command "try { $t=New-Object Net.Sockets.TcpClient('localhost',5000); $t.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    set /p =. <nul
    timeout /t 2 >nul
    goto wait_app
)

echo.
echo [OK] Application accessible.

:: ----------------------------------------------------------------
:: ETAPE 6 — Ouvrir le navigateur automatiquement (mode interactif)
:: ----------------------------------------------------------------
if "%INTERACTIVE%"=="1" start "" "http://localhost:5000"

:: ----------------------------------------------------------------
:: ETAPE 7 — Afficher le resume
:: ----------------------------------------------------------------
echo.
echo ============================================================
echo   Application disponible sur : http://localhost:5000
echo   phpMyAdmin disponible sur  : http://localhost:8080
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
if "%INTERACTIVE%"=="1" pause

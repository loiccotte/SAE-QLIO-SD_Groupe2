#!/bin/bash
# T'ELEFAN MES 4.0 — Script de lancement Linux / macOS

set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
err()  { echo -e "${RED}[ERREUR]${NC} $1"; }

echo ""
echo "============================================================"
echo "   T'ELEFAN MES 4.0 - Demarrage de l'application"
echo "============================================================"
echo ""

# --- 1. Python ---
if ! command -v python3 &>/dev/null; then
    err "Python 3 n'est pas installe."
    echo ""
    echo "  Ubuntu/Debian : sudo apt install python3 python3-venv python3-pip"
    echo "  Fedora/RHEL   : sudo dnf install python3"
    echo "  macOS         : https://www.python.org/downloads/"
    echo ""
    read -p "Appuyer sur Entree pour quitter..."
    exit 1
fi
PYVER=$(python3 --version)
ok "$PYVER detecte."

# --- 2. Venv ---
if [ ! -f ".venv/bin/activate" ]; then
    info "Premiere execution : creation de l'environnement Python..."
    python3 -m venv .venv
    ok "Environnement virtuel cree."
fi

# --- 3. Activation venv ---
source .venv/bin/activate
ok "Environnement virtuel active."

# --- 4. Dependances ---
echo ""
info "Verification des dependances Python..."
pip install -r requirements.txt -q --disable-pip-version-check
ok "Toutes les dependances sont installees."

# --- 5. .env ---
if [ ! -f ".env" ]; then
    info "Fichier .env absent - creation automatique..."
    cp .env.example .env
    ok "Fichier .env cree."
fi

# --- 6. Docker ---
echo ""
info "Verification de Docker..."
if ! docker info &>/dev/null; then
    err "Docker n'est pas installe ou n'est pas demarre."
    echo ""
    echo "  Ubuntu/Debian : https://docs.docker.com/engine/install/ubuntu/"
    echo "  macOS         : https://www.docker.com/products/docker-desktop/"
    echo ""
    read -p "Appuyer sur Entree pour quitter..."
    exit 1
fi
ok "Docker est demarre."

# --- 7. Conteneurs BDD ---
echo ""
info "Demarrage de la base de donnees..."
echo "   (premiere fois : telechargement de l'image MariaDB ~500 Mo)"
docker compose up -d db phpmyadmin

# --- 8. Attente BDD ---
echo ""
info "Attente de la base de donnees..."
RETRY=0
while ! python3 -c "import socket; s=socket.create_connection(('localhost',3306),timeout=1); s.close()" &>/dev/null; do
    RETRY=$((RETRY+1))
    if [ $RETRY -gt 60 ]; then
        err "La base de donnees n'a pas repondu apres 2 minutes."
        echo "  Verifier les logs : docker compose logs db"
        read -p "Appuyer sur Entree pour quitter..."
        exit 1
    fi
    printf "."
    sleep 2
done
echo ""
ok "Base de donnees accessible."

# --- 9. Navigateur ---
(sleep 3 && (xdg-open http://localhost:5000 2>/dev/null || open http://localhost:5000 2>/dev/null)) &

# --- 10. Flask ---
echo ""
echo "============================================================"
echo "  Application disponible sur : http://localhost:5000"
echo "  phpMyAdmin disponible sur  : http://localhost:8080"
echo ""
echo "  Comptes de connexion :"
echo "    admin        /  admin123   (administrateur, acces export)"
echo "    responsable  /  resp123    (responsable,    acces export)"
echo "    operateur    /  oper123    (employe,         lecture seule)"
echo ""
echo "  Pour arreter l'application : CTRL+C"
echo "  Pour arreter la base de donnees : docker compose stop"
echo "============================================================"
echo ""

flask run

echo ""
echo "Application arretee."
echo "Pour arreter aussi la base de donnees : docker compose stop"

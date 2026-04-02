#!/bin/bash

# AWS DATG Analyzer - Script de setup
# Usage: ./scripts/setup.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🔧 Configuration de AWS DATG Analyzer pour l'environnement: $ENVIRONMENT"
echo "📁 Répertoire du projet: $PROJECT_DIR"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 n'est pas installé. Veuillez l'installer."
        exit 1
    fi
}

# Vérifier les prérequis
log_info "Vérification des prérequis..."

check_command python3
check_command pip3
check_command docker
check_command docker-compose

# Vérifier la version de Python
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
if [[ $(echo "$PYTHON_VERSION 3.9" | awk '{print ($1 < $2)}') -eq 1 ]]; then
    log_error "Python 3.9 ou supérieur est requis. Version actuelle: $PYTHON_VERSION"
    exit 1
fi

log_info "Python $PYTHON_VERSION détecté ✓"

# Créer l'environnement virtuel
if [ ! -d "$PROJECT_DIR/venv" ]; then
    log_info "Création de l'environnement virtuel..."
    python3 -m venv "$PROJECT_DIR/venv"
else
    log_info "Environnement virtuel déjà existant."
fi

# Activer l'environnement virtuel
log_info "Activation de l'environnement virtuel..."
source "$PROJECT_DIR/venv/bin/activate"

# Installer les dépendances
log_info "Installation des dépendances Python..."
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"

# Configurer l'environnement
log_info "Configuration de l'environnement..."

if [ ! -f "$PROJECT_DIR/.env" ]; then
    log_info "Création du fichier .env à partir du template..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    
    # Générer une clé secrète
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i.bak "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" "$PROJECT_DIR/.env"
    
    log_warn "⚠️  Le fichier .env a été créé avec des valeurs par défaut."
    log_warn "   Veuillez configurer vos clés API dans $PROJECT_DIR/.env"
else
    log_info "Fichier .env déjà existant."
fi

# Initialiser la base de données
log_info "Initialisation de la base de données..."
cd "$PROJECT_DIR"
python -c "
from database.database import init_db
init_db()
print('✅ Base de données initialisée')
"

# Construire les images Docker (optionnel)
if [ "$ENVIRONMENT" = "prod" ]; then
    log_info "Construction des images Docker pour la production..."
    cd "$PROJECT_DIR/deployment"
    docker-compose build
fi

# Lancer les tests
log_info "Exécution des tests..."
cd "$PROJECT_DIR"
if python -m pytest tests/ -v; then
    log_info "✅ Tous les tests passent!"
else
    log_warn "⚠️  Certains tests ont échoué. Vérifiez les problèmes."
fi

# Afficher les instructions
echo ""
echo "🎉 Configuration terminée!"
echo ""
echo "Pour démarrer l'application:"
echo ""
echo "1. Configurez vos clés API dans .env:"
echo "   - OPENAI_API_KEY ou ANTHROPIC_API_KEY"
echo "   - (Optionnel) AWS credentials pour la validation"
echo ""
echo "2. Démarrer le backend:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   uvicorn backend.main:app --reload"
echo ""
echo "3. Démarrer le frontend (dans un autre terminal):"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   streamlit run frontend/app.py"
echo ""
echo "4. Accéder à l'application:"
echo "   - Frontend: http://localhost:8501"
echo "   - Backend API: http://localhost:8000"
echo "   - Documentation API: http://localhost:8000/docs"
echo ""
echo "Pour le déploiement Docker:"
echo "   cd $PROJECT_DIR/deployment"
echo "   docker-compose up -d"
echo ""
echo "Pour le déploiement AWS, consultez deployment/README.md"
echo ""

# Vérifier les variables d'environnement critiques
if grep -q "CHANGE-ME" "$PROJECT_DIR/.env"; then
    log_warn "⚠️  Des variables critiques doivent être configurées dans .env"
fi
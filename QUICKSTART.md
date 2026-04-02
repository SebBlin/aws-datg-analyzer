# 🚀 Quick Start - AWS DATG Analyzer

Démarrage rapide pour tester l'application localement.

## Prérequis

- Python 3.9+
- pip
- Git

## Installation en 5 minutes

### 1. Cloner le repo
```bash
git clone https://github.com/SebBlin/aws-datg-analyzer.git
cd aws-datg-analyzer
```

### 2. Lancer le script de setup
```bash
./scripts/setup.sh
```

### 3. Configurer une clé API (optionnel pour test)
Si tu veux tester avec une vraie IA, ajoute une clé dans `.env`:
```bash
# Éditer le fichier .env
OPENAI_API_KEY=sk-...  # Ou ANTHROPIC_API_KEY
```

### 4. Démarrer l'application
**Terminal 1 - Backend:**
```bash
source venv/bin/activate
uvicorn backend.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
source venv/bin/activate
streamlit run frontend/app.py
```

### 5. Tester avec l'exemple
1. Accède à http://localhost:8501
2. Upload le fichier `examples/sample-datg.md`
3. Clique sur "Analyser le document"
4. Vois les résultats !

## Test sans clé API

Si tu n'as pas de clé API, l'application utilisera un mode mock pour la démo. Les résultats seront générés automatiquement.

## Déploiement rapide avec Docker

```bash
cd deployment
docker-compose up -d
```

Accède à:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- Documentation API: http://localhost:8000/docs

## Prochaines étapes

1. **Configurer pour la production:** Voir `deployment/README.md`
2. **Déployer sur AWS:** Utiliser le template CloudFormation
3. **Personnaliser:** Modifier les prompts dans `core/llm_analyzer.py`
4. **Ajouter des bonnes pratiques:** Éditer `database/models.py`

## Dépannage

**Problème:** `ModuleNotFoundError`
```bash
pip install -r requirements.txt
```

**Problème:** Port déjà utilisé
```bash
# Changer les ports
uvicorn backend.main:app --port 8001
streamlit run frontend/app.py --server.port 8502
```

**Problème:** Base de données
```bash
# Réinitialiser
python -c "from database.database import init_db; init_db()"
```

## Support

- Issues GitHub: https://github.com/SebBlin/aws-datg-analyzer/issues
- Documentation complète: `README.md`

---

✨ **Félicitations !** Tu as maintenant une application IA qui analyse les architectures AWS. 

Prochaine étape: On déploie sur AWS ensemble ?
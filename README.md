# AWS DATG Analyzer

Une application IA qui analyse un Document d'Architecture Technique Général (DATG) AWS et évalue la conformité aux bonnes pratiques du Well-Architected Framework.

## Fonctionnalités

- **Upload de documents** : PDF, DOCX, TXT, Markdown
- **Extraction et analyse** : Segmentation du texte, identification des sections
- **Évaluation IA** : Analyse par LLM (Claude/GPT/Ollama) selon les 5 piliers du Well-Architected Framework
- **Rapport détaillé** : Scores, risques, recommandations spécifiques
- **Export** : PDF, JSON, Markdown
- **Historique** : Stockage des analyses précédentes

## Architecture

```
Frontend (Streamlit) → Backend (FastAPI) → LLM (OpenAI/Anthropic/Ollama)
                            ↓
                    PostgreSQL (analyses)
```

## Installation locale

### Prérequis
- Python 3.9+
- PostgreSQL (optionnel pour développement)
- Clé API OpenAI ou Anthropic (ou Ollama local)

### Configuration

1. Cloner le repo :
```bash
git clone https://github.com/SebBlin/aws-datg-analyzer.git
cd aws-datg-analyzer
```

2. Créer l'environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # ou `venv\Scripts\activate` sur Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement :
```bash
cp .env.example .env
# Éditer .env avec tes clés API
```

5. Lancer l'application :
```bash
# Backend
uvicorn backend.main:app --reload

# Frontend (dans un autre terminal)
streamlit run frontend/app.py
```

## Déploiement AWS

Options :
1. **ECS Fargate** : Backend + Frontend conteneurisés
2. **Lambda + API Gateway** : Architecture serverless
3. **EC2** : Déploiement traditionnel

Voir `deployment/` pour les scripts CloudFormation/Terraform.

## Utilisation

1. Accéder à http://localhost:8501
2. Uploader un DATG
3. Configurer les options d'analyse
4. Visualiser le rapport
5. Exporter les résultats

## Bonnes pratiques évaluées

### 1. Excellence opérationnelle
- Monitoring (CloudWatch)
- Logging centralisé
- CI/CD automatisé
- Gestion des changements

### 2. Sécurité
- IAM (principle of least privilege)
- Chiffrement (at-rest, in-transit)
- Sécurité réseau (VPC, Security Groups)
- Détection d'intrusion

### 3. Fiabilité
- Haute disponibilité (multi-AZ)
- Backup et recovery
- Auto-scaling
- Gestion des erreurs

### 4. Performance
- Optimisation des ressources
- Latence et throughput
- Scaling horizontal/vertical
- Mise en cache

### 5. Optimisation des coûts
- Réservations d'instances
- Choix des types d'instances
- Monitoring des coûts
- Cleanup des ressources inutilisées

## Développement

### Structure du projet
```
aws-datg-analyzer/
├── backend/           # API FastAPI
├── frontend/          # Application Streamlit
├── core/              # Logique métier
├── database/          # Modèles et migrations
├── deployment/        # Scripts de déploiement
├── tests/             # Tests unitaires et d'intégration
└── docs/              # Documentation
```

### Tests
```bash
pytest tests/
```

### Contribution
1. Fork le projet
2. Créer une branche feature
3. Commiter les changements
4. Ouvrir une Pull Request

## Licence
MIT
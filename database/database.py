from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration de la base de données
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./datg_analyzer.db")

# Pour SQLite, activer le support des foreign keys
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()

def get_db() -> Session:
    """
    Fournit une session de base de données.
    À utiliser comme dépendance FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialise la base de données.
    Crée toutes les tables définies dans les modèles.
    """
    from .models import Base
    Base.metadata.create_all(bind=engine)
    
    # Créer des données de référence si nécessaire
    db = SessionLocal()
    try:
        # Vérifier si des bonnes pratiques existent déjà
        from .models import BestPractice
        count = db.query(BestPractice).count()
        
        if count == 0:
            # Insérer des bonnes pratiques de base
            best_practices = [
                # Excellence opérationnelle
                BestPractice(
                    pillar="operational_excellence",
                    category="monitoring",
                    practice="Implémenter un monitoring complet avec CloudWatch",
                    description="Configurer des métriques, logs, dashboards et alertes pour tous les services critiques.",
                    aws_services=["CloudWatch", "CloudTrail", "X-Ray"],
                    severity="high"
                ),
                BestPractice(
                    pillar="operational_excellence",
                    category="cicd",
                    practice="Automatiser le déploiement avec CI/CD",
                    description="Utiliser CodePipeline, CodeBuild et CodeDeploy pour des déploiements automatisés et reproductibles.",
                    aws_services=["CodePipeline", "CodeBuild", "CodeDeploy"],
                    severity="high"
                ),
                
                # Sécurité
                BestPractice(
                    pillar="security",
                    category="iam",
                    practice="Appliquer le principe du moindre privilège",
                    description="Accorder uniquement les permissions nécessaires aux rôles IAM et utilisateurs.",
                    aws_services=["IAM"],
                    severity="critical"
                ),
                BestPractice(
                    pillar="security",
                    category="encryption",
                    practice="Chiffrer les données au repos et en transit",
                    description="Utiliser KMS pour le chiffrement des données et TLS pour le transit.",
                    aws_services=["KMS", "Certificate Manager"],
                    severity="high"
                ),
                
                # Fiabilité
                BestPractice(
                    pillar="reliability",
                    category="high_availability",
                    practice="Déployer en multi-AZ pour la haute disponibilité",
                    description="Utiliser au moins deux zones de disponibilité pour les services critiques.",
                    aws_services=["EC2", "RDS", "ElastiCache"],
                    severity="high"
                ),
                BestPractice(
                    pillar="reliability",
                    category="backup",
                    practice="Implémenter une stratégie de backup et recovery",
                    description="Configurer des snapshots automatiques et tester les procédures de restauration.",
                    aws_services=["Backup", "S3", "EBS"],
                    severity="medium"
                ),
                
                # Performance
                BestPractice(
                    pillar="performance",
                    category="scaling",
                    practice="Utiliser l'auto-scaling pour adapter la capacité",
                    description="Configurer des politiques d'auto-scaling basées sur la charge.",
                    aws_services=["Auto Scaling", "EC2", "Application Load Balancer"],
                    severity="high"
                ),
                BestPractice(
                    pillar="performance",
                    category="caching",
                    practice="Mettre en cache les données fréquemment accédées",
                    description="Utiliser ElastiCache ou CloudFront pour réduire la latence.",
                    aws_services=["ElastiCache", "CloudFront", "API Gateway"],
                    severity="medium"
                ),
                
                # Optimisation des coûts
                BestPractice(
                    pillar="cost_optimization",
                    category="reservations",
                    practice="Utiliser des réservations d'instances pour les charges de travail stables",
                    description="Acheter des Reserved Instances ou Savings Plans pour réduire les coûts.",
                    aws_services=["EC2", "RDS", "Redshift"],
                    severity="medium"
                ),
                BestPractice(
                    pillar="cost_optimization",
                    category="monitoring",
                    practice="Surveiller les coûts avec Cost Explorer et Budgets",
                    description="Configurer des alertes de budget et analyser régulièrement les coûts.",
                    aws_services=["Cost Explorer", "Budgets"],
                    severity="low"
                )
            ]
            
            db.add_all(best_practices)
            db.commit()
            print("✅ Données de référence insérées")
        
        # Vérifier les templates
        from .models import Template
        template_count = db.query(Template).count()
        
        if template_count == 0:
            # Template de rapport par défaut
            default_template = Template(
                name="Rapport Standard",
                description="Template de rapport standard avec tous les piliers",
                content="""# Rapport d'Analyse AWS DATG

## Analyse: {analysis.filename}
**Date:** {analysis.created_at}
**Score Global:** {result.overall_score}/100

## Scores par Pilier

{for pillar in result.pillar_scores}
### {pillar.name}: {pillar.score}/100
**Description:** {pillar.description}

**Points forts:**
{for strength in pillar.strengths}
- {strength}
{endfor}

**Points à améliorer:**
{for weakness in pillar.weaknesses}
- {weakness}
{endfor}
{endfor}

## Risques Identifiés

{for risk in result.risks}
### {risk.severity|upper}: {risk.category}
**Description:** {risk.description}
**Impact:** {risk.impact}
**Recommandation:** {risk.recommendation}
**Services AWS concernés:** {risk.aws_service_affected|join:', '}
{endfor}

## Recommandations

{for rec in result.recommendations}
### {rec.priority|upper}: {rec.category}
**Description:** {rec.description}
**Actions:**
{for action in rec.action_items}
- {action}
{endfor}
**Effort estimé:** {rec.estimated_effort}
**Services AWS:** {rec.aws_services|join:', '}
{endfor}

---
*Généré par AWS DATG Analyzer*""",
                variables=["analysis", "result"],
                is_default=True
            )
            
            db.add(default_template)
            db.commit()
            print("✅ Template par défaut créé")
            
    except Exception as e:
        db.rollback()
        print(f"⚠️ Erreur lors de l'initialisation: {e}")
    finally:
        db.close()

def drop_db():
    """
    Supprime toutes les tables (pour le développement).
    Attention: destructive!
    """
    from .models import Base
    Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    # Initialiser la base de données
    init_db()
    print("✅ Base de données initialisée")
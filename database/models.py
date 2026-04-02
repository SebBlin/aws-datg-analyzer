from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class Analysis(Base):
    """Modèle pour stocker les métadonnées d'une analyse."""
    __tablename__ = "analyses"
    
    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    llm_provider = Column(String, nullable=False)  # openai, anthropic, ollama
    llm_model = Column(String, nullable=False)
    include_aws_validation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relation avec les résultats
    result = relationship("AnalysisResult", back_populates="analysis", uselist=False, cascade="all, delete-orphan")

class AnalysisResult(Base):
    """Modèle pour stocker les résultats d'une analyse."""
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String, ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Scores
    overall_score = Column(Float, nullable=False)
    security_score = Column(Float, nullable=False)
    reliability_score = Column(Float, nullable=False)
    performance_score = Column(Float, nullable=False)
    cost_optimization_score = Column(Float, nullable=False)
    operational_excellence_score = Column(Float, nullable=False)
    
    # Données structurées
    risks = Column(JSON, nullable=False, default=list)  # Liste de risques
    recommendations = Column(JSON, nullable=False, default=list)  # Liste de recommandations
    
    # Réponse brute du LLM (pour debug/audit)
    raw_response = Column(Text, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relation
    analysis = relationship("Analysis", back_populates="result")

class User(Base):
    """Modèle pour les utilisateurs (optionnel, pour multi-utilisateurs)."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relations
    analyses = relationship("Analysis", backref="user")

class AuditLog(Base):
    """Journal d'audit pour tracer les actions."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)  # upload, analyze, export, delete
    resource_type = Column(String, nullable=False)  # analysis, document, user
    resource_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

# Tables supplémentaires pour des fonctionnalités avancées

class BestPractice(Base):
    """Référentiel des bonnes pratiques AWS."""
    __tablename__ = "best_practices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pillar = Column(String, nullable=False)  # security, reliability, etc.
    category = Column(String, nullable=False)
    practice = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    aws_services = Column(JSON, default=list)
    severity = Column(String, nullable=False)  # low, medium, high, critical
    reference_url = Column(String, nullable=True)
    
    # Index
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

class Template(Base):
    """Templates de rapports personnalisables."""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Template en markdown/HTML
    variables = Column(JSON, default=list)  # Variables disponibles dans le template
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Export(Base):
    """Historique des exports."""
    __tablename__ = "exports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String, ForeignKey("analyses.id"), nullable=False, index=True)
    format = Column(String, nullable=False)  # pdf, json, html, markdown
    file_path = Column(String, nullable=True)  Chemin local si stocké
    file_url = Column(String, nullable=True)  # URL si uploadé
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relation
    analysis = relationship("Analysis")
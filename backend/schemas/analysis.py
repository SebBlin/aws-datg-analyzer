from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PillarScore(BaseModel):
    """Score pour un pilier du Well-Architected Framework."""
    name: str
    score: float = Field(..., ge=0, le=100)
    description: str
    strengths: List[str] = []
    weaknesses: List[str] = []

class Risk(BaseModel):
    """Risque identifié dans l'architecture."""
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    category: str
    description: str
    impact: str
    recommendation: str
    aws_service_affected: Optional[List[str]] = []

class Recommendation(BaseModel):
    """Recommandation d'amélioration."""
    priority: str = Field(..., pattern="^(low|medium|high|critical)$")
    category: str
    description: str
    action_items: List[str]
    estimated_effort: Optional[str] = None  # e.g., "1-2 days", "2 weeks"
    aws_services: Optional[List[str]] = []

class AnalysisResult(BaseModel):
    """Résultat complet d'une analyse."""
    overall_score: float = Field(..., ge=0, le=100)
    
    # Scores par pilier
    security_score: float = Field(..., ge=0, le=100)
    reliability_score: float = Field(..., ge=0, le=100)
    performance_score: float = Field(..., ge=0, le=100)
    cost_optimization_score: float = Field(..., ge=0, le=100)
    operational_excellence_score: float = Field(..., ge=0, le=100)
    
    # Détails par pilier
    pillar_scores: List[PillarScore]
    
    # Risques et recommandations
    risks: List[Risk]
    recommendations: List[Recommendation]
    
    # Validation AWS (si activée)
    aws_validation_results: Optional[Dict[str, Any]] = None
    
    # Métadonnées
    analysis_duration_seconds: float
    llm_model_used: str
    raw_response: Optional[str] = None  # Réponse brute du LLM

class AnalysisRequest(BaseModel):
    """Requête pour une nouvelle analyse."""
    llm_provider: str = Field(default="openai", pattern="^(openai|anthropic|ollama)$")
    llm_model: Optional[str] = None
    include_aws_validation: bool = False
    custom_prompt: Optional[str] = None

class AnalysisResponse(BaseModel):
    """Réponse d'une analyse."""
    analysis_id: str
    filename: str
    timestamp: datetime
    
    # Résultats
    overall_score: float
    security_score: float
    reliability_score: float
    performance_score: float
    cost_optimization_score: float
    operational_excellence_score: float
    
    pillar_scores: List[PillarScore]
    risks: List[Risk]
    recommendations: List[Recommendation]
    
    # Métadonnées
    llm_model_used: str
    analysis_duration_seconds: float
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
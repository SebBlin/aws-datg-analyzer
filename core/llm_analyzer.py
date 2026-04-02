import os
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import openai
import anthropic
import requests

from schemas.analysis import AnalysisResult, PillarScore, Risk, Recommendation

load_dotenv()

@dataclass
class LLMConfig:
    """Configuration pour un fournisseur LLM."""
    provider: str
    api_key: str
    base_url: Optional[str] = None
    default_model: str = "gpt-4-turbo-preview"

class LLMAnalyzer:
    """Analyseur utilisant LLM pour évaluer les architectures AWS."""
    
    def __init__(self):
        self.configs = self._load_configs()
        self.prompt_templates = self._load_prompt_templates()
    
    def _load_configs(self) -> Dict[str, LLMConfig]:
        """Charge les configurations LLM depuis les variables d'environnement."""
        configs = {}
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            configs["openai"] = LLMConfig(
                provider="openai",
                api_key=openai_key,
                default_model="gpt-4-turbo-preview"
            )
        
        # Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            configs["anthropic"] = LLMConfig(
                provider="anthropic",
                api_key=anthropic_key,
                default_model="claude-3-opus-20240229"
            )
        
        # Ollama
        ollama_url = os.getenv("OLLAMA_BASE_URL")
        if ollama_url:
            configs["ollama"] = LLMConfig(
                provider="ollama",
                api_key="",  # Pas d'API key pour Ollama
                base_url=ollama_url,
                default_model=os.getenv("OLLAMA_MODEL", "llama2")
            )
        
        return configs
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Charge les templates de prompts."""
        return {
            "main_analysis": """Tu es un expert en architecture AWS et en Well-Architected Framework.
            
            Analyse le document d'architecture technique suivant et évalue sa conformité aux bonnes pratiques AWS.
            
            DOCUMENT:
            {document_text}
            
            INSTRUCTIONS:
            1. Évalue l'architecture sur les 5 piliers du Well-Architected Framework:
               - Excellence opérationnelle
               - Sécurité
               - Fiabilité
               - Performance
               - Optimisation des coûts
            
            2. Pour chaque pilier, donne un score de 0 à 100 et justifie.
            
            3. Identifie les risques (low, medium, high, critical) avec:
               - Catégorie
               - Description
               - Impact
               - Recommandation
               - Services AWS concernés
            
            4. Propose des recommandations d'amélioration avec:
               - Priorité (low, medium, high, critical)
               - Catégorie
               - Description
               - Actions concrètes
               - Effort estimé
               - Services AWS à utiliser
            
            FORMAT DE RÉPONSE ATTENDU (JSON):
            {{
                "overall_score": 0-100,
                "pillar_scores": [
                    {{
                        "name": "Excellence opérationnelle",
                        "score": 0-100,
                        "description": "...",
                        "strengths": ["..."],
                        "weaknesses": ["..."]
                    }},
                    // ... autres piliers
                ],
                "risks": [
                    {{
                        "severity": "low|medium|high|critical",
                        "category": "...",
                        "description": "...",
                        "impact": "...",
                        "recommendation": "...",
                        "aws_service_affected": ["..."]
                    }}
                ],
                "recommendations": [
                    {{
                        "priority": "low|medium|high|critical",
                        "category": "...",
                        "description": "...",
                        "action_items": ["..."],
                        "estimated_effort": "...",
                        "aws_services": ["..."]
                    }}
                ]
            }}
            
            Réponds UNIQUEMENT avec le JSON valide, sans texte supplémentaire.""",
            
            "aws_validation": """Valide les aspects techniques suivants de l'architecture:
            
            {architecture_summary}
            
            Vérifie la cohérence avec les services AWS et identifie les incompatibilités potentielles.
            Réponds en JSON avec la structure:
            {{
                "service_compatibility": [
                    {{
                        "service": "...",
                        "status": "compatible|incompatible|requires_configuration",
                        "issues": ["..."],
                        "recommendations": ["..."]
                    }}
                ],
                "best_practice_violations": [
                    {{
                        "practice": "...",
                        "violation": "...",
                        "severity": "low|medium|high",
                        "fix": "..."
                    }}
                ]
            }}"""
        }
    
    def get_default_model(self, provider: str) -> str:
        """Retourne le modèle par défaut pour un fournisseur."""
        if provider in self.configs:
            return self.configs[provider].default_model
        raise ValueError(f"Fournisseur non configuré: {provider}")
    
    def analyze(
        self,
        document_text: str,
        llm_provider: str = "openai",
        llm_model: Optional[str] = None,
        include_aws_validation: bool = False
    ) -> AnalysisResult:
        """
        Analyse un document avec un LLM.
        
        Args:
            document_text: Texte du document à analyser
            llm_provider: Fournisseur LLM (openai, anthropic, ollama)
            llm_model: Modèle spécifique (optionnel)
            include_aws_validation: Inclure une validation technique AWS
            
        Returns:
            AnalysisResult: Résultats de l'analyse
        """
        if llm_provider not in self.configs:
            raise ValueError(f"Fournisseur LLM non supporté: {llm_provider}")
        
        config = self.configs[llm_provider]
        model = llm_model or config.default_model
        
        start_time = time.time()
        
        try:
            # Analyse principale
            main_result = self._call_llm(
                provider=llm_provider,
                model=model,
                prompt_template=self.prompt_templates["main_analysis"],
                prompt_vars={"document_text": document_text[:15000]}  # Limiter la taille
            )
            
            # Parser la réponse JSON
            analysis_data = json.loads(main_result)
            
            # Validation AWS optionnelle
            aws_validation = None
            if include_aws_validation:
                # Extraire un résumé pour la validation
                architecture_summary = self._extract_architecture_summary(document_text)
                validation_result = self._call_llm(
                    provider=llm_provider,
                    model=model,
                    prompt_template=self.prompt_templates["aws_validation"],
                    prompt_vars={"architecture_summary": architecture_summary}
                )
                aws_validation = json.loads(validation_result)
            
            # Calculer le score global (moyenne des piliers)
            pillar_scores = analysis_data.get("pillar_scores", [])
            overall_score = sum(p["score"] for p in pillar_scores) / len(pillar_scores) if pillar_scores else 0
            
            # Extraire les scores par pilier
            scores_by_pillar = {p["name"]: p["score"] for p in pillar_scores}
            
            # Convertir en objets Pydantic
            pillar_objects = [
                PillarScore(
                    name=p["name"],
                    score=p["score"],
                    description=p.get("description", ""),
                    strengths=p.get("strengths", []),
                    weaknesses=p.get("weaknesses", [])
                )
                for p in pillar_scores
            ]
            
            risk_objects = [
                Risk(
                    severity=r["severity"],
                    category=r["category"],
                    description=r["description"],
                    impact=r["impact"],
                    recommendation=r["recommendation"],
                    aws_service_affected=r.get("aws_service_affected", [])
                )
                for r in analysis_data.get("risks", [])
            ]
            
            recommendation_objects = [
                Recommendation(
                    priority=r["priority"],
                    category=r["category"],
                    description=r["description"],
                    action_items=r.get("action_items", []),
                    estimated_effort=r.get("estimated_effort"),
                    aws_services=r.get("aws_services", [])
                )
                for r in analysis_data.get("recommendations", [])
            ]
            
            analysis_duration = time.time() - start_time
            
            return AnalysisResult(
                overall_score=overall_score,
                security_score=scores_by_pillar.get("Sécurité", 0),
                reliability_score=scores_by_pillar.get("Fiabilité", 0),
                performance_score=scores_by_pillar.get("Performance", 0),
                cost_optimization_score=scores_by_pillar.get("Optimisation des coûts", 0),
                operational_excellence_score=scores_by_pillar.get("Excellence opérationnelle", 0),
                pillar_scores=pillar_objects,
                risks=risk_objects,
                recommendations=recommendation_objects,
                aws_validation_results=aws_validation,
                analysis_duration_seconds=analysis_duration,
                llm_model_used=model,
                raw_response=main_result
            )
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Erreur de parsing JSON de la réponse LLM: {e}")
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'analyse LLM: {e}")
    
    def _call_llm(
        self,
        provider: str,
        model: str,
        prompt_template: str,
        prompt_vars: Dict[str, str]
    ) -> str:
        """Appelle l'API du fournisseur LLM."""
        # Remplir le template
        prompt = prompt_template.format(**prompt_vars)
        
        if provider == "openai":
            return self._call_openai(model, prompt)
        elif provider == "anthropic":
            return self._call_anthropic(model, prompt)
        elif provider == "ollama":
            return self._call_ollama(model, prompt)
        else:
            raise ValueError(f"Fournisseur non implémenté: {provider}")
    
    def _call_openai(self, model: str, prompt: str) -> str:
        """Appelle l'API OpenAI."""
        client = openai.OpenAI(api_key=self.configs["openai"].api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Tu es un expert en architecture AWS."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Faible température pour des réponses cohérentes
            max_tokens=4000
        )
        
        return response.choices[0].message.content.strip()
    
    def _call_anthropic(self, model: str, prompt: str) -> str:
        """Appelle l'API Anthropic."""
        client = anthropic.Anthropic(api_key=self.configs["anthropic"].api_key)
        
        response = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0.1,
            system="Tu es un expert en architecture AWS.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text.strip()
    
    def _call_ollama(self, model: str, prompt: str) -> str:
        """Appelle l'API Ollama locale."""
        config = self.configs["ollama"]
        url = f"{config.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "system": "Tu es un expert en architecture AWS.",
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "").strip()
    
    def _extract_architecture_summary(self, document_text: str, max_length: int = 2000) -> str:
        """Extrait un résumé de l'architecture pour la validation."""
        # Recherche de sections clés
        keywords = [
            "architecture", "AWS", "services", "EC2", "S3", "RDS", "Lambda",
            "VPC", "IAM", "CloudFront", "API Gateway", "DynamoDB"
        ]
        
        lines = document_text.split('\n')
        relevant_lines = []
        
        for line in lines:
            if any(keyword.lower() in line.lower() for keyword in keywords):
                relevant_lines.append(line.strip())
                if len('\n'.join(relevant_lines)) > max_length:
                    break
        
        summary = '\n'.join(relevant_lines)
        
        # Si trop court, prendre le début du document
        if len(summary) < 500:
            summary = document_text[:max_length]
        
        return summary
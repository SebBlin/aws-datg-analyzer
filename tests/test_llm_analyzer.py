import pytest
import json
from unittest.mock import Mock, patch
from core.llm_analyzer import LLMAnalyzer, AnalysisResult
from schemas.analysis import PillarScore, Risk, Recommendation

class TestLLMAnalyzer:
    """Tests pour l'analyseur LLM."""
    
    @pytest.fixture
    def analyzer(self):
        """Fixture avec configuration mockée."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-openai-key',
            'ANTHROPIC_API_KEY': 'test-anthropic-key',
            'OLLAMA_BASE_URL': 'http://localhost:11434'
        }):
            return LLMAnalyzer()
    
    def test_load_configs(self, analyzer):
        """Teste le chargement des configurations."""
        assert 'openai' in analyzer.configs
        assert 'anthropic' in analyzer.configs
        assert 'ollama' in analyzer.configs
        
        openai_config = analyzer.configs['openai']
        assert openai_config.provider == 'openai'
        assert openai_config.api_key == 'test-openai-key'
        assert openai_config.default_model == 'gpt-4-turbo-preview'
    
    def test_get_default_model(self, analyzer):
        """Teste la récupération du modèle par défaut."""
        assert analyzer.get_default_model('openai') == 'gpt-4-turbo-preview'
        assert analyzer.get_default_model('anthropic') == 'claude-3-opus-20240229'
        assert analyzer.get_default_model('ollama') == 'llama2'
        
        with pytest.raises(ValueError, match="Fournisseur non configuré"):
            analyzer.get_default_model('unknown')
    
    def test_load_prompt_templates(self, analyzer):
        """Teste le chargement des templates de prompts."""
        templates = analyzer.prompt_templates
        assert 'main_analysis' in templates
        assert 'aws_validation' in templates
        
        # Vérifie que les templates contiennent des placeholders
        assert '{document_text}' in templates['main_analysis']
        assert '{architecture_summary}' in templates['aws_validation']
    
    @patch('core.llm_analyzer.openai.OpenAI')
    def test_call_openai(self, mock_openai, analyzer):
        """Teste l'appel à l'API OpenAI."""
        # Mock de la réponse
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"test": "response"}'))]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Appel de la méthode
        result = analyzer._call_openai('gpt-4', 'Test prompt')
        
        # Vérifications
        assert result == '{"test": "response"}'
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('core.llm_analyzer.anthropic.Anthropic')
    def test_call_anthropic(self, mock_anthropic, analyzer):
        """Teste l'appel à l'API Anthropic."""
        # Mock de la réponse
        mock_response = Mock()
        mock_response.content = [Mock(text='{"test": "response"}')]
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Appel de la méthode
        result = analyzer._call_anthropic('claude-3', 'Test prompt')
        
        # Vérifications
        assert result == '{"test": "response"}'
        mock_client.messages.create.assert_called_once()
    
    @patch('core.llm_analyzer.requests.post')
    def test_call_ollama(self, mock_post, analyzer):
        """Teste l'appel à l'API Ollama."""
        # Mock de la réponse
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {'response': '{"test": "response"}'}
        mock_post.return_value = mock_response
        
        # Appel de la méthode
        result = analyzer._call_ollama('llama2', 'Test prompt')
        
        # Vérifications
        assert result == '{"test": "response"}'
        mock_post.assert_called_once()
    
    def test_extract_architecture_summary(self, analyzer):
        """Teste l'extraction du résumé d'architecture."""
        document_text = """Ce document décrit une architecture AWS.
        
        Nous utilisons EC2 pour les instances de calcul.
        RDS est utilisé pour la base de données.
        S3 stocke les fichiers statiques.
        
        D'autres détails techniques suivent...
        """
        
        summary = analyzer._extract_architecture_summary(document_text, max_length=100)
        
        # Vérifie que le résumé contient les mots-clés AWS
        assert 'EC2' in summary or 'RDS' in summary or 'S3' in summary
        assert len(summary) <= 100
    
    def test_extract_architecture_summary_short(self, analyzer):
        """Teste l'extraction avec texte trop court."""
        document_text = "Texte court sans mots-clés AWS."
        
        summary = analyzer._extract_architecture_summary(document_text, max_length=100)
        
        # Quand le texte est trop court, doit prendre le début du document
        assert summary == document_text[:100]
    
    @patch.object(LLMAnalyzer, '_call_llm')
    def test_analyze_success(self, mock_call_llm, analyzer):
        """Teste une analyse réussie."""
        # Mock de la réponse LLM
        mock_response = json.dumps({
            "overall_score": 75.5,
            "pillar_scores": [
                {
                    "name": "Sécurité",
                    "score": 80.0,
                    "description": "Bonnes pratiques de sécurité",
                    "strengths": ["IAM bien configuré"],
                    "weaknesses": ["Chiffrement manquant"]
                },
                {
                    "name": "Fiabilité",
                    "score": 70.0,
                    "description": "Architecture fiable",
                    "strengths": ["Multi-AZ"],
                    "weaknesses": ["Backup non testé"]
                }
            ],
            "risks": [
                {
                    "severity": "high",
                    "category": "Sécurité",
                    "description": "Pas de chiffrement des données",
                    "impact": "Exposition des données sensibles",
                    "recommendation": "Activer le chiffrement KMS",
                    "aws_service_affected": ["S3", "RDS"]
                }
            ],
            "recommendations": [
                {
                    "priority": "high",
                    "category": "Sécurité",
                    "description": "Améliorer le chiffrement",
                    "action_items": ["Activer KMS", "Configurer TLS"],
                    "estimated_effort": "2 jours",
                    "aws_services": ["KMS", "Certificate Manager"]
                }
            ]
        })
        
        mock_call_llm.return_value = mock_response
        
        # Exécution de l'analyse
        document_text = "Architecture AWS avec EC2 et RDS."
        result = analyzer.analyze(
            document_text=document_text,
            llm_provider="openai",
            llm_model="gpt-4",
            include_aws_validation=False
        )
        
        # Vérifications
        assert isinstance(result, AnalysisResult)
        assert result.overall_score == 75.0  # Moyenne de 80 et 70
        assert result.security_score == 80.0
        assert result.reliability_score == 70.0
        
        # Vérifie les piliers
        assert len(result.pillar_scores) == 2
        assert isinstance(result.pillar_scores[0], PillarScore)
        
        # Vérifie les risques
        assert len(result.risks) == 1
        assert isinstance(result.risks[0], Risk)
        assert result.risks[0].severity == "high"
        
        # Vérifie les recommandations
        assert len(result.recommendations) == 1
        assert isinstance(result.recommendations[0], Recommendation)
        assert result.recommendations[0].priority == "high"
        
        # Vérifie les métadonnées
        assert result.llm_model_used == "gpt-4"
        assert result.analysis_duration_seconds > 0
    
    @patch.object(LLMAnalyzer, '_call_llm')
    def test_analyze_with_aws_validation(self, mock_call_llm, analyzer):
        """Teste une analyse avec validation AWS."""
        # Mock des réponses LLM
        mock_call_llm.side_effect = [
            # Première réponse (analyse principale)
            json.dumps({
                "overall_score": 80.0,
                "pillar_scores": [
                    {
                        "name": "Sécurité",
                        "score": 80.0,
                        "description": "Test",
                        "strengths": [],
                        "weaknesses": []
                    }
                ],
                "risks": [],
                "recommendations": []
            }),
            # Deuxième réponse (validation AWS)
            json.dumps({
                "service_compatibility": [
                    {
                        "service": "EC2",
                        "status": "compatible",
                        "issues": [],
                        "recommendations": []
                    }
                ],
                "best_practice_violations": []
            })
        ]
        
        # Exécution de l'analyse
        result = analyzer.analyze(
            document_text="Test",
            llm_provider="openai",
            include_aws_validation=True
        )
        
        # Vérifications
        assert result.aws_validation_results is not None
        assert 'service_compatibility' in result.aws_validation_results
    
    @patch.object(LLMAnalyzer, '_call_llm')
    def test_analyze_json_error(self, mock_call_llm, analyzer):
        """Teste une erreur de parsing JSON."""
        mock_call_llm.return_value = "Not a JSON response"
        
        with pytest.raises(ValueError, match="Erreur de parsing JSON"):
            analyzer.analyze("Test", "openai")
    
    @patch.object(LLMAnalyzer, '_call_llm')
    def test_analyze_empty_pillar_scores(self, mock_call_llm, analyzer):
        """Teste avec des scores de piliers vides."""
        mock_call_llm.return_value = json.dumps({
            "overall_score": 0,
            "pillar_scores": [],
            "risks": [],
            "recommendations": []
        })
        
        result = analyzer.analyze("Test", "openai")
        
        assert result.overall_score == 0
        assert len(result.pillar_scores) == 0
    
    def test_analyze_unsupported_provider(self, analyzer):
        """Teste avec un fournisseur non supporté."""
        with pytest.raises(ValueError, match="Fournisseur LLM non supporté"):
            analyzer.analyze("Test", "unknown")
    
    def test_call_llm_unsupported_provider(self, analyzer):
        """Teste l'appel à un fournisseur non implémenté."""
        with pytest.raises(ValueError, match="Fournisseur non implémenté"):
            analyzer._call_llm("unknown", "model", "prompt", {})
    
    def test_prompt_template_formatting(self, analyzer):
        """Teste le formatage des templates de prompts."""
        prompt_vars = {
            "document_text": "Test document",
            "architecture_summary": "Test summary"
        }
        
        main_prompt = analyzer.prompt_templates["main_analysis"].format(**prompt_vars)
        validation_prompt = analyzer.prompt_templates["aws_validation"].format(**prompt_vars)
        
        assert "Test document" in main_prompt
        assert "Test summary" in validation_prompt
        assert "{document_text}" not in main_prompt
        assert "{architecture_summary}" not in validation_prompt
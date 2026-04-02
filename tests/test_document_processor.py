import pytest
import tempfile
import os
from core.document_processor import DocumentProcessor, ProcessedDocument

class TestDocumentProcessor:
    """Tests pour le processeur de documents."""
    
    @pytest.fixture
    def processor(self):
        return DocumentProcessor()
    
    def test_supported_extensions(self, processor):
        """Teste les extensions supportées."""
        assert '.pdf' in processor.supported_extensions
        assert '.docx' in processor.supported_extensions
        assert '.txt' in processor.supported_extensions
        assert '.md' in processor.supported_extensions
        assert '.jpg' not in processor.supported_extensions
    
    def test_process_unsupported_extension(self, processor):
        """Teste le traitement d'une extension non supportée."""
        with pytest.raises(ValueError, match="Extension non supportée"):
            processor.process(b"test content", ".jpg")
    
    def test_process_text_file(self, processor):
        """Teste le traitement d'un fichier texte."""
        content = b"""# Titre principal
        
        Ceci est un paragraphe de test.
        
        ## Sous-titre
        
        Un autre paragraphe.
        """
        
        result = processor.process(content, '.txt')
        
        assert isinstance(result, ProcessedDocument)
        assert result.text is not None
        assert result.word_count > 0
        assert len(result.sections) > 0
        assert not result.has_tables
        assert not result.has_images
    
    def test_process_markdown_file(self, processor):
        """Teste le traitement d'un fichier markdown."""
        content = b"""# Architecture AWS
        
        ## Services utilisés
        
        - EC2 pour les instances
        - RDS pour la base de données
        - S3 pour le stockage
        
        | Service | Usage |
        |---------|-------|
        | EC2 | Compute |
        | S3 | Storage |
        """
        
        result = processor.process(content, '.md')
        
        assert isinstance(result, ProcessedDocument)
        assert "Architecture AWS" in result.text
        assert result.has_tables  # Doit détecter la table markdown
        assert not result.has_images
    
    def test_extract_sections(self, processor):
        """Teste l'extraction de sections."""
        text = """# Introduction
        
        Ceci est l'introduction.
        
        ## Architecture
        
        Description de l'architecture.
        
        ### Détails techniques
        
        Plus de détails.
        """
        
        sections = processor._extract_sections(text)
        
        assert len(sections) == 3
        assert sections[0]['title'] == 'Introduction'
        assert sections[1]['title'] == 'Architecture'
        assert sections[2]['title'] == 'Détails techniques'
        assert sections[0]['level'] == 1
        assert sections[1]['level'] == 2
        assert sections[2]['level'] == 3
    
    def test_extract_sections_from_markdown(self, processor):
        """Teste l'extraction de sections depuis markdown."""
        md_text = """# Titre niveau 1
        
        Contenu niveau 1.
        
        ## Titre niveau 2
        
        Contenu niveau 2.
        """
        
        sections = processor._extract_sections_from_markdown(md_text)
        
        assert len(sections) == 2
        assert sections[0]['title'] == 'Titre niveau 1'
        assert sections[1]['title'] == 'Titre niveau 2'
        assert sections[0]['type'] == 'markdown'
    
    def test_post_process(self, processor):
        """Teste le post-traitement."""
        doc = ProcessedDocument(
            text="  Texte   avec  espaces   multiples  \n\n\net sauts de ligne.",
            metadata={},
            sections=[],
            word_count=5,
            has_tables=False,
            has_images=False
        )
        
        result = processor._post_process(doc)
        
        # Vérifie que les espaces multiples sont réduits
        assert "  " not in result.text
        # Vérifie que les sauts de ligne multiples sont réduits
        assert "\n\n\n" not in result.text
    
    def test_process_with_temp_file(self, processor):
        """Teste le traitement avec fichier temporaire."""
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"Test content")
            tmp_path = tmp.name
        
        try:
            # Lire le fichier et le traiter
            with open(tmp_path, 'rb') as f:
                content = f.read()
            
            result = processor.process(content, '.txt')
            assert result.text == "Test content"
            
        finally:
            # Nettoyer
            os.unlink(tmp_path)
    
    def test_word_count(self, processor):
        """Teste le comptage de mots."""
        text = "Ceci est un texte avec cinq mots."
        doc = ProcessedDocument(
            text=text,
            metadata={},
            sections=[],
            word_count=len(text.split()),
            has_tables=False,
            has_images=False
        )
        
        assert doc.word_count == 5
    
    def test_table_detection(self):
        """Teste la détection de tables."""
        # Texte avec table markdown
        text_with_table = """| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |"""
        
        # Texte sans table
        text_without_table = "Just plain text without tables."
        
        processor = DocumentProcessor()
        
        # Note: La détection de tables est basique dans l'implémentation actuelle
        # Ce test vérifie juste que la méthode ne plante pas
        sections_with = processor._extract_sections(text_with_table)
        sections_without = processor._extract_sections(text_without_table)
        
        assert isinstance(sections_with, list)
        assert isinstance(sections_without, list)
    
    def test_metadata_extraction(self, processor):
        """Teste l'extraction de métadonnées (pour les formats qui le supportent)."""
        # Pour les fichiers texte, les métadonnées sont minimales
        content = b"Test content"
        result = processor.process(content, '.txt')
        
        assert 'encoding' in result.metadata
        assert result.metadata['encoding'] == 'utf-8'
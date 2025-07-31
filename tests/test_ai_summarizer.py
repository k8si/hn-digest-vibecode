"""Unit tests for AI summarizer."""
import pytest
from unittest.mock import Mock, patch
from src.hn_digest.ai_summarizer import AISummarizer

class TestAISummarizer:
    """Test cases for AISummarizer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('src.hn_digest.ai_summarizer.anthropic.Anthropic'):
            self.summarizer = AISummarizer()
    
    def test_create_summary_prompt(self):
        """Test summary prompt creation."""
        title = "Test AI Article"
        content = "This article discusses artificial intelligence and machine learning."
        url = "https://example.com/ai-article"
        
        prompt = self.summarizer._create_summary_prompt(title, content, url)
        
        assert title in prompt
        assert content in prompt
        assert url in prompt
        assert "1-2 paragraphs" in prompt
        assert "factual" in prompt
    
    @patch('anthropic.Anthropic')
    def test_summarize_article_success(self, mock_anthropic_class):
        """Test successful article summarization."""
        # Mock the Anthropic client and response
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is a generated summary of the AI article discussing key concepts."
        mock_client.messages.create.return_value = mock_response
        
        # Recreate summarizer with mocked client
        summarizer = AISummarizer()
        
        title = "AI Breakthrough Article"
        content = "Long article content about artificial intelligence breakthroughs and new research findings."
        url = "https://example.com/ai-breakthrough"
        
        summary = summarizer.summarize_article(title, content, url)
        
        assert summary == "This is a generated summary of the AI article discussing key concepts."
        mock_client.messages.create.assert_called_once()
        
        # Check that the call used correct parameters
        call_args = mock_client.messages.create.call_args
        assert call_args[1]['model'] == 'claude-3-haiku-20240307'  # Default model
        assert call_args[1]['max_tokens'] == 300
        assert call_args[1]['temperature'] == 0.3
    
    @patch('src.hn_digest.ai_summarizer.anthropic.Anthropic')
    def test_summarize_article_api_error(self, mock_anthropic_class):
        """Test article summarization with API error."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        # Simulate API error
        mock_client.messages.create.side_effect = Exception("API error")
        
        summarizer = AISummarizer()
        
        summary = summarizer.summarize_article("Title", "Content that is long enough to pass validation", "https://example.com")
        
        assert summary is None
    
    @patch('anthropic.Anthropic')
    def test_summarize_article_empty_response(self, mock_anthropic_class):
        """Test handling of empty API response."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = ""  # Empty response
        mock_client.messages.create.return_value = mock_response
        
        summarizer = AISummarizer()
        
        summary = summarizer.summarize_article("Title", "Content", "https://example.com")
        
        assert summary is None
    
    def test_summarize_article_short_content(self):
        """Test rejection of very short content."""
        summary = self.summarizer.summarize_article("Title", "Short", "https://example.com")
        
        assert summary is None
    
    def test_create_fallback_summary(self):
        """Test fallback summary creation."""
        title = "Test Article"
        url = "https://example.com/test"
        reason = "scraping failed"
        
        fallback = self.summarizer.create_fallback_summary(title, url, reason)
        
        assert title in fallback
        assert url in fallback
        assert reason in fallback
        assert "Summary not available" in fallback
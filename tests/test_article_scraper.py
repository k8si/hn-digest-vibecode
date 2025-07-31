"""Unit tests for article scraper."""
import pytest
from unittest.mock import Mock, patch
from src.hn_digest.article_scraper import ArticleScraper

class TestArticleScraper:
    """Test cases for ArticleScraper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = ArticleScraper()
    
    def test_is_scrapeable_url_valid(self):
        """Test URL validation for scrapeable URLs."""
        valid_urls = [
            'https://example.com/article',
            'http://blog.company.com/post/123',
            'https://github.com/user/repo',
            'https://arxiv.org/abs/2301.12345'
        ]
        
        for url in valid_urls:
            assert self.scraper._is_scrapeable_url(url)
    
    def test_is_scrapeable_url_invalid(self):
        """Test URL validation rejects invalid URLs."""
        invalid_urls = [
            '',
            'ftp://example.com/file.txt',
            'https://example.com/document.pdf',
            'https://github.com/user/repo/blob/main/file.py',
            'mailto:test@example.com'
        ]
        
        for url in invalid_urls:
            assert not self.scraper._is_scrapeable_url(url)
    
    @patch('src.hn_digest.article_scraper.time.sleep')
    @patch('requests.Session.get')
    def test_scrape_article_success(self, mock_get, mock_sleep):
        """Test successful article scraping."""
        # Mock HTML content
        html_content = """
        <html>
        <head>
            <title>Test Article Title</title>
            <meta name="description" content="Test description">
            <meta property="og:title" content="OG Test Title">
        </head>
        <body>
            <article>
                <h1>Main Article Title</h1>
                <p>This is the main content of the article. It contains important information about AI and machine learning.</p>
                <p>Second paragraph with more details and technical information that should be extracted.</p>
            </article>
        </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.content = html_content.encode('utf-8')
        mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        content, metadata = self.scraper.scrape_article('https://example.com/article')
        
        assert content is not None
        assert 'main content of the article' in content
        assert 'AI and machine learning' in content
        assert metadata is not None
        assert metadata.get('title') == 'Test Article Title'
        assert metadata.get('og_title') == 'OG Test Title'
    
    @patch('src.hn_digest.article_scraper.time.sleep')
    def test_scrape_article_network_failure(self, mock_sleep):
        """Test article scraping with network failure."""
        with patch.object(self.scraper.session, 'get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            content, metadata = self.scraper.scrape_article('https://example.com/article')
            
            assert content is None
            assert metadata is None
    
    @patch('src.hn_digest.article_scraper.time.sleep')
    @patch('requests.Session.get')
    def test_scrape_article_non_html_content(self, mock_get, mock_sleep):
        """Test scraping non-HTML content."""
        mock_response = Mock()
        mock_response.headers = {'content-type': 'application/json'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        content, metadata = self.scraper.scrape_article('https://api.example.com/data')
        
        assert content is None
        assert metadata is None
    
    def test_clean_content(self):
        """Test content cleaning functionality."""
        dirty_content = """
        
        Short line
        
        This is a longer line that should be kept because it contains substantial content.
        
        Another substantial line with meaningful information that should be preserved.
        
        x
        
        Final paragraph with good content that should remain in the cleaned version.
        """
        
        cleaned = self.scraper._clean_content(dirty_content)
        
        # Should remove very short lines but keep substantial content
        assert 'Short line' not in cleaned
        assert 'x' not in cleaned
        assert 'longer line that should be kept' in cleaned
        assert 'Another substantial line' in cleaned
        assert 'Final paragraph' in cleaned
    
    def test_clean_content_truncation(self):
        """Test content truncation for very long articles."""
        # Create content longer than the max limit
        long_content = "A" * 10000  # Much longer than 8000 char limit
        
        cleaned = self.scraper._clean_content(long_content)
        
        # Should be truncated and end with "..."
        assert len(cleaned) <= 8003  # 8000 + "..."
        assert cleaned.endswith("...")
    
    def test_extract_content_heuristics(self):
        """Test content extraction heuristics with various HTML structures."""
        from bs4 import BeautifulSoup
        
        # Test with article tag - make content long enough to meet minimum length requirement
        html_with_article = """
        <html>
        <body>
            <nav>Navigation content</nav>
            <article>
                <p>This is the main article content that should be extracted because it's in an article tag. This paragraph contains enough text to meet the minimum length requirement of 200 characters that the content extraction heuristics use to determine if this is substantial content worth extracting from the HTML document structure.</p>
            </article>
            <footer>Footer content</footer>
        </body>
        </html>
        """
        
        soup = BeautifulSoup(html_with_article, 'html.parser')
        content = self.scraper._extract_content_heuristics(soup, 'https://example.com')
        
        assert content is not None
        assert 'main article content' in content
        assert 'Navigation content' not in content
        assert 'Footer content' not in content
    
    def test_extract_metadata(self):
        """Test metadata extraction from HTML."""
        from bs4 import BeautifulSoup
        
        html_with_metadata = """
        <html>
        <head>
            <title>Article Title</title>
            <meta name="description" content="Article description">
            <meta property="og:title" content="Open Graph Title">
            <meta name="author" content="John Doe">
            <meta property="article:published_time" content="2024-01-15T10:00:00Z">
        </head>
        <body>Content</body>
        </html>
        """
        
        soup = BeautifulSoup(html_with_metadata, 'html.parser')
        metadata = self.scraper._extract_metadata(soup)
        
        assert metadata['title'] == 'Article Title'
        assert metadata['description'] == 'Article description'
        assert metadata['og_title'] == 'Open Graph Title'
        assert metadata['author'] == 'John Doe'
        assert metadata['publication_date'] == '2024-01-15T10:00:00Z'
"""Unit tests for HackerNews client."""
import pytest
from unittest.mock import Mock, patch
from src.hn_digest.hn_client import HNClient

class TestHNClient:
    """Test cases for HNClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = HNClient()
    
    @patch('src.hn_digest.hn_client.time.sleep')
    @patch('requests.Session.get')
    def test_make_api_request_success(self, mock_get, mock_sleep):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {'test': 'data'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.client._make_api_request('https://test.com')
        
        assert result == {'test': 'data'}
        mock_sleep.assert_called_once()
        mock_get.assert_called_once()
    
    @patch('src.hn_digest.hn_client.time.sleep')  
    def test_make_api_request_failure(self, mock_sleep):
        """Test API request failure handling."""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            result = self.client._make_api_request('https://test.com')
            
            assert result is None
    
    @patch('src.hn_digest.hn_client.time.sleep')
    @patch('requests.Session.get')
    def test_fetch_article_content_success(self, mock_get, mock_sleep):
        """Test successful article content fetching."""
        mock_response = Mock()
        mock_response.text = "Article content here"
        mock_response.headers = {'content-type': 'text/html; charset=utf-8'}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        content, mime_type = self.client.fetch_article_content('https://example.com')
        
        assert content == "Article content here"
        assert mime_type == "text/html"
    
    @patch('src.hn_digest.hn_client.time.sleep')
    def test_fetch_article_content_failure(self, mock_sleep):
        """Test article content fetching failure."""
        with patch.object(self.client.session, 'get') as mock_get:
            mock_get.side_effect = Exception("Failed to fetch")
            
            content, mime_type = self.client.fetch_article_content('https://example.com')
            
            assert content is None
            assert mime_type is None
    
    def test_get_story_details_valid_story(self):
        """Test story details parsing for valid story."""
        with patch.object(self.client, '_make_api_request') as mock_request:
            mock_request.return_value = {
                'id': 12345,
                'type': 'story',
                'title': 'Test Story',
                'url': 'https://example.com',
                'score': 100,
                'by': 'testuser',
                'time': 1234567890,
                'descendants': 25
            }
            
            result = self.client.get_story_details(12345)
            
            assert result['id'] == 12345
            assert result['title'] == 'Test Story'
            assert result['score'] == 100
    
    def test_get_story_details_non_story_type(self):
        """Test that non-story types are filtered out."""
        with patch.object(self.client, '_make_api_request') as mock_request:
            mock_request.return_value = {
                'id': 12345,
                'type': 'job',  # Not a story
                'title': 'Job Posting'
            }
            
            result = self.client.get_story_details(12345)
            
            assert result is None
    
    def test_get_stories_batch(self):
        """Test batch story fetching."""
        story_ids = [1, 2, 3]
        
        with patch.object(self.client, 'get_story_details') as mock_details:
            mock_details.side_effect = [
                {'id': 1, 'title': 'Story 1'},
                None,  # Failed story
                {'id': 3, 'title': 'Story 3'}
            ]
            
            results = self.client.get_stories_batch(story_ids)
            
            assert len(results) == 2  # Only successful stories
            assert results[0]['id'] == 1
            assert results[1]['id'] == 3
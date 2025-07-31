"""Integration tests for HackerNews flow."""
import pytest
from unittest.mock import Mock, patch
from src.hn_digest.main import HNDigestApp

class TestIntegration:
    """Integration test cases for complete HN digest flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = HNDigestApp()
    
    @patch('src.hn_digest.hn_client.time.sleep')
    def test_full_scan_and_filter_flow(self, mock_sleep):
        """Test complete flow from HN API to filtered results."""
        # Mock HN API responses
        mock_story_ids = [1, 2, 3, 4, 5]
        mock_stories_data = {
            1: {'id': 1, 'type': 'story', 'title': 'OpenAI releases new GPT model', 'url': 'https://openai.com/gpt', 'score': 200, 'by': 'user1', 'time': 1234567890, 'descendants': 50},
            2: {'id': 2, 'type': 'story', 'title': 'JavaScript framework update', 'url': 'https://js.com', 'score': 150, 'by': 'user2', 'time': 1234567891, 'descendants': 25},
            3: {'id': 3, 'type': 'story', 'title': 'Machine learning breakthrough in healthcare', 'url': 'https://med.com/ml', 'score': 180, 'by': 'user3', 'time': 1234567892, 'descendants': 40},
            4: {'id': 4, 'type': 'job', 'title': 'AI Engineer Position', 'url': 'https://jobs.com', 'score': 10, 'by': 'company', 'time': 1234567893, 'descendants': 0},
            5: {'id': 5, 'type': 'story', 'title': 'New Python library for web development', 'url': 'https://python.org', 'score': 100, 'by': 'user5', 'time': 1234567894, 'descendants': 15}
        }
        
        # Mock the API calls
        with patch.object(self.app.hn_client, '_make_api_request') as mock_api:
            def mock_api_side_effect(url):
                if 'topstories' in url:
                    return mock_story_ids
                elif '/item/' in url:
                    story_id = int(url.split('/')[-1].replace('.json', ''))
                    return mock_stories_data.get(story_id)
                return None
            
            mock_api.side_effect = mock_api_side_effect
            
            # Run the scan and filter
            result_stories = self.app.fetch_and_filter_stories()
            
            # Verify results
            assert len(result_stories) == 2  # Only AI-related stories (1 and 3)
            
            # Check that stories are properly scored and filtered
            story_titles = [story['title'] for story in result_stories]
            assert 'OpenAI releases new GPT model' in story_titles
            assert 'Machine learning breakthrough in healthcare' in story_titles
            assert 'JavaScript framework update' not in story_titles
            
            # Check that AI scoring metadata is added
            for story in result_stories:
                assert 'ai_score' in story
                assert 'matched_keywords' in story
                assert 'combined_score' in story
                assert story['ai_score'] > 0
            
            # Check sorting by combined score
            assert result_stories[0]['combined_score'] >= result_stories[1]['combined_score']
    
    def test_empty_hn_response_handling(self):
        """Test handling of empty or failed HN API responses."""
        with patch.object(self.app.hn_client, 'get_top_stories') as mock_top_stories:
            mock_top_stories.return_value = []
            
            result_stories = self.app.fetch_and_filter_stories()
            
            assert result_stories == []
    
    def test_no_ai_stories_found(self):
        """Test behavior when no AI-related stories are found."""
        non_ai_stories = [
            {'id': 1, 'title': 'New JavaScript framework', 'url': 'https://js.com', 'score': 100, 'by': 'user1', 'time': 1234567890, 'descendants': 10},
            {'id': 2, 'title': 'Database optimization tips', 'url': 'https://db.com', 'score': 80, 'by': 'user2', 'time': 1234567891, 'descendants': 20}
        ]
        
        with patch.object(self.app.hn_client, 'get_top_stories') as mock_top_stories:
            with patch.object(self.app.hn_client, 'get_stories_batch') as mock_stories:
                mock_top_stories.return_value = [1, 2]
                mock_stories.return_value = non_ai_stories
                
                result_stories = self.app.fetch_and_filter_stories()
                
                assert result_stories == []
    
    def test_api_failure_resilience(self):
        """Test that the system handles API failures gracefully."""
        # Test story IDs fetch failure
        with patch.object(self.app.hn_client, 'get_top_stories') as mock_top_stories:
            mock_top_stories.return_value = []
            
            result_stories = self.app.fetch_and_filter_stories()
            assert result_stories == []
        
        # Test story details fetch failure  
        with patch.object(self.app.hn_client, 'get_top_stories') as mock_top_stories:
            with patch.object(self.app.hn_client, 'get_stories_batch') as mock_stories:
                mock_top_stories.return_value = [1, 2, 3]
                mock_stories.return_value = []  # All story detail fetches failed
                
                result_stories = self.app.fetch_and_filter_stories()
                assert result_stories == []
    
    def test_mixed_success_failure_scenarios(self):
        """Test scenarios with partial API failures."""
        with patch.object(self.app.hn_client, 'get_top_stories') as mock_top_stories:
            with patch.object(self.app.hn_client, 'get_story_details') as mock_story_details:
                mock_top_stories.return_value = [1, 2, 3]
                
                # Mock some successful and some failed story fetches
                def mock_story_side_effect(story_id):
                    if story_id == 1:
                        return {'id': 1, 'title': 'AI breakthrough announced', 'url': 'https://ai.com', 'score': 150, 'by': 'user1', 'time': 1234567890, 'descendants': 30}
                    elif story_id == 2:
                        return None  # Failed to fetch
                    elif story_id == 3:
                        return {'id': 3, 'title': 'New database technology', 'url': 'https://db.com', 'score': 100, 'by': 'user3', 'time': 1234567892, 'descendants': 20}
                    return None
                
                mock_story_details.side_effect = mock_story_side_effect
                
                result_stories = self.app.fetch_and_filter_stories()
                
                # Should only include the AI story that was successfully fetched
                assert len(result_stories) == 1
                assert result_stories[0]['title'] == 'AI breakthrough announced'
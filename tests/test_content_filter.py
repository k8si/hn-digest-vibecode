"""Unit tests for content filtering logic."""
import pytest
from src.hn_digest.content_filter import ContentFilter

class TestContentFilter:
    """Test cases for ContentFilter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.filter = ContentFilter()
    
    def test_ai_keyword_matching(self):
        """Test basic AI keyword matching in titles."""
        # Test obvious AI keywords
        ai_story = {
            'title': 'New GPT-4 model shows impressive results',
            'url': 'https://example.com/article',
            'score': 100
        }
        assert self.filter.is_ai_related(ai_story)
        
        # Test machine learning keywords
        ml_story = {
            'title': 'Machine Learning breakthrough in computer vision',
            'url': 'https://example.com/ml',
            'score': 50
        }
        assert self.filter.is_ai_related(ml_story)
        
        # Test non-AI story
        non_ai_story = {
            'title': 'New JavaScript framework released',
            'url': 'https://example.com/js',
            'score': 75
        }
        assert not self.filter.is_ai_related(non_ai_story)
    
    def test_case_insensitive_matching(self):
        """Test that keyword matching is case insensitive."""
        stories = [
            {'title': 'AI breakthrough', 'url': '', 'score': 10},
            {'title': 'ai breakthrough', 'url': '', 'score': 10},
            {'title': 'Ai breakthrough', 'url': '', 'score': 10},
            {'title': 'ARTIFICIAL INTELLIGENCE news', 'url': '', 'score': 10},
        ]
        
        for story in stories:
            assert self.filter.is_ai_related(story)
    
    def test_url_domain_bonus(self):
        """Test that AI-related domains get bonus points."""
        openai_story = {
            'title': 'Company update',  # No AI keywords in title
            'url': 'https://openai.com/blog/update',
            'score': 50
        }
        
        score, keywords = self.filter._calculate_ai_score(
            openai_story['title'], 
            openai_story['url']
        )
        
        assert score > 0  # Should get points for openai.com domain
        assert any('openai.com' in kw for kw in keywords)
    
    def test_scoring_system(self):
        """Test that scoring system works correctly."""
        # High-value keyword
        gpt_story = {
            'title': 'ChatGPT new features',
            'url': 'https://example.com',
            'score': 100
        }
        
        # Lower-value keyword  
        algorithm_story = {
            'title': 'New algorithm for sorting',
            'url': 'https://example.com',
            'score': 100
        }
        
        gpt_score, _ = self.filter._calculate_ai_score(gpt_story['title'], gpt_story['url'])
        algo_score, _ = self.filter._calculate_ai_score(algorithm_story['title'], algorithm_story['url'])
        
        assert gpt_score > algo_score  # GPT should score higher than algorithm
    
    def test_filter_and_score_stories(self):
        """Test filtering and scoring of story batches."""
        stories = [
            {'title': 'OpenAI releases GPT-5', 'url': 'https://openai.com', 'score': 200, 'id': 1},
            {'title': 'JavaScript framework update', 'url': 'https://js.com', 'score': 150, 'id': 2},
            {'title': 'Machine learning in healthcare', 'url': 'https://med.com', 'score': 100, 'id': 3},
            {'title': 'New Python library', 'url': 'https://python.org', 'score': 80, 'id': 4},
            {'title': 'AI research breakthrough', 'url': 'https://arxiv.org', 'score': 120, 'id': 5},
        ]
        
        filtered_stories = self.filter.filter_and_score_stories(stories)
        
        # Should only include AI-related stories
        assert len(filtered_stories) == 3  # stories 1, 3, 5
        
        # Should be sorted by combined score (HN score + AI score)
        assert filtered_stories[0]['id'] == 1  # OpenAI story should be first
        
        # Each story should have AI scoring metadata
        for story in filtered_stories:
            assert 'ai_score' in story
            assert 'matched_keywords' in story
            assert 'combined_score' in story
            assert story['ai_score'] > 0
    
    def test_empty_and_edge_cases(self):
        """Test edge cases like empty titles and special characters."""
        edge_cases = [
            {'title': '', 'url': '', 'score': 100},  # Empty title
            {'title': 'AI: The Future!', 'url': '', 'score': 50},  # Special characters
            {'title': 'A.I. and machine-learning', 'url': '', 'score': 75},  # Punctuation
            {'title': "OpenAI's GPT-4", 'url': '', 'score': 90},  # Apostrophes
        ]
        
        # Empty title should not match
        assert not self.filter.is_ai_related(edge_cases[0])
        
        # Others should match despite special characters
        for story in edge_cases[1:]:
            assert self.filter.is_ai_related(story)
    
    def test_max_articles_limit(self):
        """Test that filtering respects the maximum articles limit."""
        # Create more AI stories than the limit
        many_stories = []
        for i in range(150):  # More than MAX_ARTICLES (100)
            story = {
                'title': f'AI breakthrough number {i}',
                'url': f'https://example{i}.com',
                'score': 100 - i,  # Decreasing scores
                'id': i
            }
            many_stories.append(story)
        
        filtered_stories = self.filter.filter_and_score_stories(many_stories)
        
        # Should be limited to MAX_ARTICLES
        from src.hn_digest.config import Config
        assert len(filtered_stories) <= Config.MAX_ARTICLES
    
    def test_get_filter_summary(self):
        """Test filter summary generation."""
        summary = self.filter.get_filter_summary(100, 25)
        assert "100" in summary
        assert "25" in summary
        assert "AI-related" in summary
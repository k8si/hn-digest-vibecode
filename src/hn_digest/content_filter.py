"""AI content filtering system with keyword matching and scoring."""
import logging
import re
from typing import List, Dict, Tuple
from .config import Config

logger = logging.getLogger(__name__)

class ContentFilter:
    """Filter and score HackerNews posts for AI-related content."""
    
    def __init__(self):
        # Compile regex patterns for better performance
        # Handle variations like "A.I." for "ai" and "machine-learning" for "machine learning"
        self.keyword_patterns = []
        for keyword in Config.AI_KEYWORDS:
            if keyword == 'ai':
                # Match "ai", "A.I.", "A I", etc.
                pattern = re.compile(r'\b(?:ai|a\.?i\.?|a\s+i)\b', re.IGNORECASE)
            elif keyword == 'machine learning':
                # Match "machine learning", "machine-learning", etc.
                pattern = re.compile(r'\bmachine[\s\-_]?learning\b', re.IGNORECASE)
            else:
                # Standard word boundary matching with flexibility for hyphens/underscores
                escaped = re.escape(keyword).replace(r'\ ', r'[\s\-_]?')
                pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
            self.keyword_patterns.append(pattern)
    
    def _calculate_ai_score(self, title: str, url: str = '') -> Tuple[int, List[str]]:
        """Calculate AI relevance score and return matched keywords."""
        matched_keywords = []
        score = 0
        
        # Check title for keywords
        title_lower = title.lower()
        for i, pattern in enumerate(self.keyword_patterns):
            keyword = Config.AI_KEYWORDS[i]
            if pattern.search(title):
                matched_keywords.append(keyword)
                # Weight keywords differently based on specificity
                if keyword in ['ai', 'artificial intelligence', 'machine learning', 'ml']:
                    score += 3  # High value keywords
                elif keyword in ['gpt', 'llm', 'openai', 'anthropic', 'claude', 'chatgpt']:
                    score += 4  # Specific AI company/product keywords
                else:
                    score += 2  # General AI-related keywords
        
        # Bonus points for URL patterns that suggest AI content
        url_lower = url.lower()
        ai_domains = ['openai.com', 'anthropic.com', 'deepmind.com', 'research.google', 'arxiv.org']
        for domain in ai_domains:
            if domain in url_lower:
                score += 2
                matched_keywords.append(f"domain:{domain}")
                break
        
        return score, matched_keywords
    
    def is_ai_related(self, story: Dict) -> bool:
        """Check if a story is AI-related based on title and URL."""
        title = story.get('title', '')
        url = story.get('url', '')
        
        ai_score, matched_keywords = self._calculate_ai_score(title, url)
        
        # Be overly inclusive - any positive score means it's AI-related
        is_relevant = ai_score > 0
        
        if is_relevant:
            logger.debug(f"AI story found: '{title[:50]}...' (score: {ai_score}, keywords: {matched_keywords})")
        
        return is_relevant
    
    def filter_and_score_stories(self, stories: List[Dict]) -> List[Dict]:
        """Filter stories for AI content and add scoring information."""
        ai_stories = []
        
        for story in stories:
            if self.is_ai_related(story):
                title = story.get('title', '')
                url = story.get('url', '')
                ai_score, matched_keywords = self._calculate_ai_score(title, url)
                
                # Add filtering metadata to story
                story_with_score = story.copy()
                story_with_score.update({
                    'ai_score': ai_score,
                    'matched_keywords': matched_keywords,
                    'combined_score': story.get('score', 0) + ai_score  # HN score + AI relevance
                })
                
                ai_stories.append(story_with_score)
        
        # Sort by combined score (HN score + AI relevance) descending
        ai_stories.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Limit to maximum articles
        ai_stories = ai_stories[:Config.MAX_ARTICLES]
        
        logger.info(f"Filtered {len(stories)} stories down to {len(ai_stories)} AI-related stories")
        
        return ai_stories
    
    def get_filter_summary(self, original_count: int, filtered_count: int) -> str:
        """Generate a summary of the filtering process."""
        return f"Processed {original_count} HackerNews stories, found {filtered_count} AI-related articles"
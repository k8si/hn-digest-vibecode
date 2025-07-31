"""HackerNews API client with rate limiting and error handling."""
import requests
import time
import logging
from typing import List, Dict, Optional, Tuple
from .config import Config

logger = logging.getLogger(__name__)

class HNClient:
    """Client for interacting with HackerNews Firebase API."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HN-Digest/1.0 (ksilverstein@mozilla.com)'
        })
    
    def _make_api_request(self, url: str) -> Optional[Dict]:
        """Make a rate-limited request to HackerNews API (expects JSON)."""
        try:
            time.sleep(Config.REQUEST_DELAY)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {url}: {e}")
            return None
        except ValueError as e:
            logger.error(f"JSON parsing failed for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {e}")
            return None
    
    def fetch_article_content(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Fetch article content as plaintext with MIME type."""
        try:
            time.sleep(Config.REQUEST_DELAY)
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            mime_type = content_type.split(';')[0].strip()
            
            # Get text content with proper encoding
            text_content = response.text
            
            logger.debug(f"Fetched article {url}: {mime_type}, {len(text_content)} chars")
            return text_content, mime_type
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch article {url}: {e}")
            return None, None
        except Exception as e:
            logger.warning(f"Unexpected error fetching article {url}: {e}")
            return None, None
    
    def get_top_stories(self) -> List[int]:
        """Get list of top story IDs from HackerNews."""
        logger.info("Fetching top stories from HackerNews")
        data = self._make_api_request(Config.HN_TOP_STORIES_URL)
        if data is None:
            logger.error("Failed to fetch top stories")
            return []
        
        # Return first 2 pages worth of stories (60 stories)
        total_stories = Config.PAGES_TO_SCAN * Config.STORIES_PER_PAGE
        return data[:total_stories]
    
    def get_story_details(self, story_id: int) -> Optional[Dict]:
        """Get details for a specific story ID."""
        url = f"{Config.HN_ITEM_URL}/{story_id}.json"
        data = self._make_api_request(url)
        
        if data is None:
            logger.warning(f"Failed to fetch story {story_id}")
            return None
        
        # Only return stories (not jobs, polls, etc.)
        if data.get('type') != 'story':
            return None
            
        return {
            'id': data.get('id'),
            'title': data.get('title', ''),
            'url': data.get('url', ''),
            'score': data.get('score', 0),
            'by': data.get('by', ''),
            'time': data.get('time', 0),
            'descendants': data.get('descendants', 0)  # comment count
        }
    
    def get_stories_batch(self, story_ids: List[int]) -> List[Dict]:
        """Get details for multiple stories with rate limiting."""
        logger.info(f"Fetching details for {len(story_ids)} stories")
        stories = []
        
        for story_id in story_ids:
            story = self.get_story_details(story_id)
            if story:
                stories.append(story)
                logger.debug(f"Fetched story: {story['title'][:50]}...")
        
        logger.info(f"Successfully fetched {len(stories)} stories")
        return stories
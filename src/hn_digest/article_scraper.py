"""Article content scraping system with BeautifulSoup."""
import requests
import time
import logging
from typing import Optional, Dict, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from .config import Config

logger = logging.getLogger(__name__)

class ArticleScraper:
    """Scrapes article content from various websites."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HN-Digest/1.0 (ksilverstein@mozilla.com)'
        })
    
    def _is_scrapeable_url(self, url: str) -> bool:
        """Check if URL is likely to be scrapeable."""
        if not url:
            return False
        
        parsed = urlparse(url)
        
        # Skip non-HTTP URLs
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Skip PDF files and other binary content
        if url.lower().endswith(('.pdf', '.doc', '.docx', '.zip', '.exe')):
            return False
        
        # Skip GitHub file URLs (but allow repository pages)
        if 'github.com' in parsed.netloc and '/blob/' in url:
            return False
        
        return True
    
    def _extract_content_heuristics(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract main article content using various heuristics."""
        content_candidates = []
        
        # Try common article selectors in order of preference
        selectors = [
            'article',
            '[role="main"]',
            '.content',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.story-body',
            '#content',
            'main',
            '.main-content'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                # Take the first matching element
                element = elements[0]
                text = element.get_text(strip=True)
                if len(text) > 200:  # Reasonable minimum length
                    content_candidates.append((len(text), text))
        
        # Fallback: Try to find the largest text block
        if not content_candidates:
            # Look for divs with substantial text content
            for div in soup.find_all(['div', 'section']):
                text = div.get_text(strip=True)
                if len(text) > 500:  # Higher threshold for generic divs
                    content_candidates.append((len(text), text))
        
        # Return the longest text block found
        if content_candidates:
            content_candidates.sort(key=lambda x: x[0], reverse=True)
            return content_candidates[0][1]
        
        return None
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize extracted content."""
        if not content:
            return ""
        
        # Basic cleaning
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # Skip very short lines (likely navigation)
                cleaned_lines.append(line)
        
        cleaned_content = '\n\n'.join(cleaned_lines)
        
        # Truncate if too long (for AI processing efficiency)
        max_length = 8000  # Reasonable limit for summarization
        if len(cleaned_content) > max_length:
            cleaned_content = cleaned_content[:max_length] + "..."
        
        return cleaned_content
    
    def scrape_article(self, url: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Scrape article content and metadata.
        
        Returns:
            Tuple of (content, metadata) where metadata contains title, 
            publication_date, author, etc. if available.
        """
        if not self._is_scrapeable_url(url):
            logger.debug(f"URL not scrapeable: {url}")
            return None, None
        
        try:
            # Respectful delay
            time.sleep(Config.REQUEST_DELAY)
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.debug(f"Non-HTML content type for {url}: {content_type}")
                return None, None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract main content
            content = self._extract_content_heuristics(soup, url)
            if not content:
                logger.warning(f"Could not extract content from {url}")
                return None, None
            
            # Clean content
            cleaned_content = self._clean_content(content)
            if len(cleaned_content) < 100:
                logger.warning(f"Extracted content too short for {url}")
                return None, None
            
            # Extract metadata
            metadata = self._extract_metadata(soup)
            
            logger.debug(f"Successfully scraped {url}: {len(cleaned_content)} chars")
            return cleaned_content, metadata
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to scrape {url}: {e}")
            return None, None
        except Exception as e:
            logger.warning(f"Unexpected error scraping {url}: {e}")
            return None, None
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract article metadata from HTML."""
        metadata = {}
        
        # Try to get title
        title_elem = soup.find('title')
        if title_elem:
            metadata['title'] = title_elem.get_text(strip=True)
        
        # Try to get meta description
        description = soup.find('meta', attrs={'name': 'description'})
        if description:
            metadata['description'] = description.get('content', '').strip()
        
        # Try to get Open Graph title (often cleaner than <title>)
        og_title = soup.find('meta', property='og:title')
        if og_title:
            metadata['og_title'] = og_title.get('content', '').strip()
        
        # Try to get publication date
        date_selectors = [
            'meta[property="article:published_time"]',
            'meta[name="date"]',
            'meta[name="publish_date"]',
            'time[datetime]',
            '.published',
            '.date'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date_value = date_elem.get('content') or date_elem.get('datetime') or date_elem.get_text(strip=True)
                if date_value:
                    metadata['publication_date'] = date_value
                    break
        
        # Try to get author
        author_selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            '.author',
            '.byline'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                author_value = author_elem.get('content') or author_elem.get_text(strip=True)
                if author_value:
                    metadata['author'] = author_value
                    break
        
        return metadata
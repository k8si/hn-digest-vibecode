"""AI-powered article summarization using Anthropic Claude API."""
import logging
import anthropic
from typing import Optional, Dict
from .config import Config

logger = logging.getLogger(__name__)

class AISummarizer:
    """Generates article summaries using Anthropic Claude API."""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    
    def _create_summary_prompt(self, title: str, content: str, url: str) -> str:
        """Create a prompt for article summarization."""
        prompt = f"""Please provide a concise, factual summary of this article in 1-2 paragraphs. Focus on the main points and key findings. Be objective and avoid speculation.

Article Title: {title}
Article URL: {url}

Article Content:
{content}

Instructions:
- Write 1-2 clear, informative paragraphs
- Focus on facts and key points, not opinions
- Include specific details when relevant (numbers, names, dates)
- Write in third person
- Don't add information not present in the article
- If the article is primarily technical, explain key concepts briefly

Summary:"""
        return prompt
    
    def summarize_article(self, title: str, content: str, url: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Generate a summary for an article using Anthropic Claude API.
        
        Args:
            title: Article title from HackerNews or scraped content
            content: Full article text content
            url: Original article URL
            metadata: Optional metadata dict with author, date, etc.
        
        Returns:
            Generated summary text or None if summarization fails
        """
        if not content or len(content.strip()) < 50:
            logger.warning(f"Content too short for summarization: {url}")
            return None
        
        try:
            prompt = self._create_summary_prompt(title, content, url)
            
            response = self.client.messages.create(
                model=Config.ANTHROPIC_MODEL,
                max_tokens=300,  # ~1-2 paragraphs
                temperature=0.3,  # Lower temperature for more factual output
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            summary = response.content[0].text.strip()
            
            if not summary:
                logger.warning(f"Empty summary generated for {url}")
                return None
            
            logger.debug(f"Generated summary for {url}: {len(summary)} chars")
            return summary
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error summarizing {url}: {e}")
            return None
    
    def create_fallback_summary(self, title: str, url: str, reason: str = "content unavailable") -> str:
        """Create a fallback summary when scraping or AI summarization fails."""
        return f"**{title}**\n\nSummary not available ({reason}). Please visit the original article for full details.\n\nSource: {url}"
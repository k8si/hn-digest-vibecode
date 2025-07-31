"""Main application entry point with CLI interface."""
import argparse
import logging
import sys
from typing import List, Dict
from datetime import datetime

from .config import Config, setup_logging
from .hn_client import HNClient
from .content_filter import ContentFilter
from .article_scraper import ArticleScraper
from .ai_summarizer import AISummarizer
from .summary_formatter import SummaryFormatter

logger = logging.getLogger(__name__)

class HNDigestApp:
    """Main application class for HackerNews AI Digest."""
    
    def __init__(self):
        self.hn_client = HNClient()
        self.content_filter = ContentFilter()
        self.article_scraper = ArticleScraper()
        self.ai_summarizer = AISummarizer()
        self.summary_formatter = SummaryFormatter()
    
    def fetch_and_filter_stories(self) -> List[Dict]:
        """Fetch stories from HackerNews and filter for AI content."""
        logger.info("Starting HackerNews AI content scan")
        
        # Get top story IDs
        story_ids = self.hn_client.get_top_stories()
        if not story_ids:
            logger.error("Failed to fetch top stories from HackerNews")
            return []
        
        logger.debug(f"Fetched {len(story_ids)} story IDs from HackerNews")
        
        # Get story details
        stories = self.hn_client.get_stories_batch(story_ids)
        if not stories:
            logger.error(f"Failed to fetch story details for {len(story_ids)} story IDs")
            return []
        
        logger.debug(f"Successfully fetched details for {len(stories)} stories")
        
        # Filter for AI content
        ai_stories = self.content_filter.filter_and_score_stories(stories)
        
        # Log summary
        summary = self.content_filter.get_filter_summary(len(stories), len(ai_stories))
        logger.info(summary)
        
        if not ai_stories:
            logger.warning(f"No AI-related stories found among {len(stories)} total stories")
            logger.debug("Consider checking AI keyword list or filtering criteria if this seems unexpected")
        
        return ai_stories
    
    def run_scan_only(self) -> List[Dict]:
        """Run scan and filtering only (for testing)."""
        return self.fetch_and_filter_stories()
    
    def scrape_and_summarize_stories(self, stories: List[Dict]) -> Dict[str, str]:
        """Scrape article content and generate AI summaries."""
        summaries = {}
        scraping_stats = {
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'summaries_generated': 0,
            'failure_reasons': {}
        }
        
        logger.info(f"Scraping and summarizing {len(stories)} articles")
        
        for story in stories:
            url = story.get('url', '')
            title = story.get('title', '')
            
            if not url:
                logger.debug(f"No URL for story: {title}")
                scraping_stats['failed_scrapes'] += 1
                reason = 'no_url'
                scraping_stats['failure_reasons'][reason] = scraping_stats['failure_reasons'].get(reason, 0) + 1
                continue
            
            # Scrape article content
            content, metadata = self.article_scraper.scrape_article(url)
            
            if content:
                scraping_stats['successful_scrapes'] += 1
                
                # Generate AI summary
                summary = self.ai_summarizer.summarize_article(title, content, url, metadata)
                
                if summary:
                    summaries[url] = summary
                    scraping_stats['summaries_generated'] += 1
                    logger.debug(f"Generated summary for: {title[:50]}...")
                else:
                    # Use fallback summary
                    fallback = self.ai_summarizer.create_fallback_summary(title, url, "AI summarization failed")
                    summaries[url] = fallback
                    reason = 'ai_failed'
                    scraping_stats['failure_reasons'][reason] = scraping_stats['failure_reasons'].get(reason, 0) + 1
            else:
                scraping_stats['failed_scrapes'] += 1
                # Create fallback summary for scraping failures
                fallback = self.ai_summarizer.create_fallback_summary(title, url, "content scraping failed")
                summaries[url] = fallback
                reason = 'scraping_failed'
                scraping_stats['failure_reasons'][reason] = scraping_stats['failure_reasons'].get(reason, 0) + 1
        
        logger.info(f"Scraping complete: {scraping_stats['successful_scrapes']}/{len(stories)} successful, {scraping_stats['summaries_generated']} AI summaries generated")
        
        return summaries
    
    def run_full_digest(self):
        """Run full digest process (scan, summarize, format)."""
        stories = self.fetch_and_filter_stories()
        
        if not stories:
            logger.warning("No AI stories found to process")
            return
        
        logger.info(f"Found {len(stories)} AI stories to process")
        
        # Scrape and summarize articles
        summaries = self.scrape_and_summarize_stories(stories)
        
        # Format the digest
        digest_text = self.summary_formatter.format_digest(stories, summaries, datetime.now())
        
        # For now, just print the digest (email sending will be in Phase 3)
        print("\n" + "="*60)
        print("GENERATED DIGEST")
        print("="*60)
        print(digest_text)
        print("="*60)

def create_cli_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description='HackerNews AI Digest - Scan HN for AI content and generate email digest'
    )
    
    parser.add_argument(
        '--mode',
        choices=['scan', 'full'],
        default='scan',
        help='Run mode: scan (filter only), full (complete digest)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without sending emails (future use)'
    )
    
    return parser

def main():
    """Main entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate configuration
    if not Config.EMAIL_RECIPIENT:
        logger.error("EMAIL_RECIPIENT not configured")
        sys.exit(1)
    
    if args.mode == 'full' and not Config.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not configured but required for full mode")
        sys.exit(1)
    
    # Create and run application
    app = HNDigestApp()
    
    try:
        if args.mode == 'scan':
            stories = app.run_scan_only()
            print(f"\nFound {len(stories)} AI-related stories:")
            for i, story in enumerate(stories[:10], 1):  # Show top 10
                print(f"{i:2d}. {story['title']} (HN:{story['score']}, AI:{story['ai_score']})")
                print(f"    Keywords: {', '.join(story['matched_keywords'])}")
                if story['url']:
                    print(f"    URL: {story['url']}")
                print()
        
        elif args.mode == 'full':
            app.run_full_digest()
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
"""Main application entry point with CLI interface."""
import argparse
import logging
import sys
from typing import List, Dict

from .config import Config, setup_logging
from .hn_client import HNClient
from .content_filter import ContentFilter

logger = logging.getLogger(__name__)

class HNDigestApp:
    """Main application class for HackerNews AI Digest."""
    
    def __init__(self):
        self.hn_client = HNClient()
        self.content_filter = ContentFilter()
    
    def fetch_and_filter_stories(self) -> List[Dict]:
        """Fetch stories from HackerNews and filter for AI content."""
        logger.info("Starting HackerNews AI content scan")
        
        # Get top story IDs
        story_ids = self.hn_client.get_top_stories()
        if not story_ids:
            logger.error("Failed to fetch top stories from HackerNews")
            return []
        
        # Get story details
        stories = self.hn_client.get_stories_batch(story_ids)
        if not stories:
            logger.error("Failed to fetch story details")
            return []
        
        # Filter for AI content
        ai_stories = self.content_filter.filter_and_score_stories(stories)
        
        # Log summary
        summary = self.content_filter.get_filter_summary(len(stories), len(ai_stories))
        logger.info(summary)
        
        return ai_stories
    
    def run_scan_only(self) -> List[Dict]:
        """Run scan and filtering only (for testing)."""
        return self.fetch_and_filter_stories()
    
    def run_full_digest(self):
        """Run full digest process (scan, summarize, email)."""
        # This will be implemented in later phases
        stories = self.fetch_and_filter_stories()
        
        if not stories:
            logger.warning("No AI stories found to process")
            return
        
        logger.info(f"Found {len(stories)} AI stories to process")
        for story in stories[:5]:  # Show top 5 for now
            logger.info(f"- {story['title']} (score: {story['combined_score']})")

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
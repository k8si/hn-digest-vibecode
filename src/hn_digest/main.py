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
from .email_formatter import EmailFormatter
from .email_sender import EmailSender
from .podcast_generator import PodcastGenerator

logger = logging.getLogger(__name__)

class HNDigestApp:
    """Main application class for HackerNews AI Digest."""
    
    def __init__(self):
        self.hn_client = HNClient()
        self.content_filter = ContentFilter()
        self.article_scraper = ArticleScraper()
        self.ai_summarizer = AISummarizer()
        self.summary_formatter = SummaryFormatter()
        self.email_formatter = EmailFormatter()
        self.email_sender = None  # Initialized when needed
        self.podcast_generator = None  # Initialized when needed
    
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
    
    def _get_email_sender(self) -> EmailSender:
        """Get email sender instance, initializing if needed."""
        if self.email_sender is None:
            self.email_sender = EmailSender()
        return self.email_sender
    
    def _get_podcast_generator(self) -> PodcastGenerator:
        """Get podcast generator instance, initializing if needed."""
        if self.podcast_generator is None:
            self.podcast_generator = PodcastGenerator(
                api_key=Config.OPENAI_API_KEY,
                voice=Config.TTS_VOICE
            )
        return self.podcast_generator
    
    def generate_podcast(self, digest_text: str, output_filename: str) -> bool:
        """
        Generate podcast from digest text.
        
        Args:
            digest_text: The formatted digest text to convert to speech
            output_filename: Full path for the output MP3 file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info("Starting podcast generation...")
            podcast_generator = self._get_podcast_generator()
            success = podcast_generator.generate_podcast(digest_text, output_filename)
            
            if success:
                logger.info(f"Podcast generation completed successfully: {output_filename}")
            else:
                logger.error("Podcast generation failed")
                
            return success
            
        except Exception as e:
            logger.error(f"Podcast generation error: {e}")
            return False
    
    def _handle_email_failure(self, email_content: str, error_message: str, generate_podcast: bool = False):
        """Handle email sending failure by saving content locally."""
        logger.error(f"Email sending failed: {error_message}")
        
        # Save digest to local file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"digest_backup_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"FAILED TO SEND EMAIL: {error_message}\n")
                f.write("=" * 60 + "\n")
                f.write(email_content)
            
            logger.warning(f"Digest saved to {filename} for manual review")
            
            # Generate podcast if requested (even if email failed)
            if generate_podcast:
                podcast_filename = PodcastGenerator.get_podcast_filename(filename)
                logger.info(f"Generating podcast from backup digest: {podcast_filename}")
                
                # Extract just the digest content (skip the error header)
                digest_content = email_content
                success = self.generate_podcast(digest_content, podcast_filename)
                
                if success:
                    logger.info(f"Podcast generated successfully: {podcast_filename}")
                else:
                    logger.error("Podcast generation failed for backup digest")
                    
        except Exception as e:
            logger.error(f"Failed to save digest backup: {e}")
    
    def _handle_critical_failure(self, error_message: str):
        """Handle critical failure by attempting fallback email."""
        logger.error(f"Critical digest generation failure: {error_message}")
        
        try:
            email_sender = self._get_email_sender()
            success = email_sender.send_fallback_email(error_message)
            
            if success:
                logger.info("Fallback email sent successfully")
            else:
                logger.error("Fallback email also failed to send")
                self._save_error_log(error_message)
                
        except Exception as e:
            logger.error(f"Could not send fallback email: {e}")
            self._save_error_log(error_message)
    
    def _save_error_log(self, error_message: str):
        """Save error information to local file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"digest_error_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"HN-Digest Critical Error - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n")
                f.write(f"Error: {error_message}\n")
                f.write("\nThis error prevented the daily digest from being generated or sent.\n")
                f.write("Please check the application logs for more details.\n")
            
            logger.warning(f"Error log saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save error log: {e}")
    
    def run_full_digest(self, generate_podcast: bool = False):
        """Run full digest process (scan, summarize, format) - print only."""
        stories = self.fetch_and_filter_stories()
        
        if not stories:
            logger.warning("No AI stories found to process")
            return
        
        logger.info(f"Found {len(stories)} AI stories to process")
        
        # Scrape and summarize articles
        summaries = self.scrape_and_summarize_stories(stories)
        
        # Format the digest
        digest_text = self.summary_formatter.format_digest(stories, summaries, datetime.now())
        
        # Save digest to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        digest_filename = f"digest_{timestamp}.txt"
        
        try:
            with open(digest_filename, 'w', encoding='utf-8') as f:
                f.write(digest_text)
            logger.info(f"Digest saved to {digest_filename}")
        except Exception as e:
            logger.error(f"Failed to save digest file: {e}")
            
        # Print the digest
        print("\n" + "="*60)
        print("GENERATED DIGEST")
        print("="*60)
        print(digest_text)
        print("="*60)
        print(f"\nDigest saved to: {digest_filename}")
        
        # Generate podcast if requested
        if generate_podcast:
            podcast_filename = PodcastGenerator.get_podcast_filename(digest_filename)
            
            logger.info(f"Generating podcast: {podcast_filename}")
            success = self.generate_podcast(digest_text, podcast_filename)
            
            if success:
                print(f"✓ Podcast generated: {podcast_filename}")
            else:
                print(f"✗ Podcast generation failed - check logs for details")
    
    def run_full_digest_with_email(self, dry_run: bool = False, generate_podcast: bool = False):
        """Run full digest process and send via email."""
        logger.info("Starting full digest generation with email delivery")
        
        try:
            # Generate digest content
            stories = self.fetch_and_filter_stories()
            
            if not stories:
                logger.warning("No AI stories found - sending empty digest notification")
                # Still send an email to notify that no stories were found
                email_content = self.email_formatter.format_email([], {})
                subject = self.email_formatter.create_subject_line(story_count=0)
            else:
                logger.info(f"Found {len(stories)} AI stories to process")
                
                # Scrape and summarize articles
                summaries = self.scrape_and_summarize_stories(stories)
                
                # Get scraping stats for the email
                scraping_stats = {
                    'successful_scrapes': sum(1 for url in summaries.keys() if summaries[url] and 'Summary not available' not in summaries[url]),
                    'failed_scrapes': len(stories) - len([s for s in summaries.values() if s and 'Summary not available' not in s]),
                    'summaries_generated': len([s for s in summaries.values() if s and 'Summary not available' not in s])
                }
                
                # Format email content
                email_content = self.email_formatter.format_email(stories, summaries, datetime.now(), scraping_stats)
                subject = self.email_formatter.create_subject_line(story_count=len(stories))
            
            # Attempt to send email
            if dry_run:
                logger.info("DRY RUN - Email content would be:")
                print("\n" + "="*60)
                print(f"Subject: {subject}")
                print("="*60)
                print(email_content)
                print("="*60)
                return
            
            try:
                email_sender = self._get_email_sender()
                
                # Validate configuration before attempting to send
                if not email_sender.validate_configuration():
                    raise ValueError("Email configuration validation failed")
                
                success = email_sender.send_digest_email(subject, email_content)
                
                if success:
                    logger.info("Digest email sent successfully")
                    
                    # Generate podcast if requested and email was successful
                    if generate_podcast:
                        # Save digest content to file for podcast generation
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        digest_filename = f"digest_{timestamp}.txt"
                        
                        try:
                            with open(digest_filename, 'w', encoding='utf-8') as f:
                                f.write(email_content)
                            logger.info(f"Digest saved to {digest_filename}")
                            
                            podcast_filename = PodcastGenerator.get_podcast_filename(digest_filename)
                            logger.info(f"Generating podcast: {podcast_filename}")
                            
                            podcast_success = self.generate_podcast(email_content, podcast_filename)
                            if podcast_success:
                                logger.info(f"Podcast generated successfully: {podcast_filename}")
                            else:
                                logger.error("Podcast generation failed after successful email")
                                
                        except Exception as e:
                            logger.error(f"Failed to save digest or generate podcast: {e}")
                else:
                    self._handle_email_failure(email_content, "Email sending failed after retries", generate_podcast)
                    
            except ValueError as e:
                self._handle_email_failure(email_content, f"Email setup failed: {e}", generate_podcast)
            except Exception as e:
                self._handle_email_failure(email_content, f"Unexpected email error: {e}", generate_podcast)
                
        except Exception as e:
            # Critical failure in digest generation
            self._handle_critical_failure(str(e))

def create_cli_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description='HackerNews AI Digest - Scan HN for AI content and generate email digest'
    )
    
    parser.add_argument(
        '--mode',
        choices=['scan', 'full', 'email'],
        default='scan',
        help='Run mode: scan (filter only), full (complete digest), email (digest + send email)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without sending emails (shows what would be sent)'
    )
    
    parser.add_argument(
        '--podcast',
        action='store_true',
        help='Generate podcast audio file from digest content'
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
    
    if args.mode in ['full', 'email'] and not Config.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not configured but required for full/email mode")
        sys.exit(1)
    
    if args.mode == 'email' and not args.dry_run and (not Config.GMAIL_USERNAME or not Config.GMAIL_PASSWORD):
        logger.error("GMAIL_USERNAME and GMAIL_PASSWORD not configured but required for email mode")
        sys.exit(1)
    
    if args.podcast and not Config.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not configured but required for podcast generation")
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
            
            if args.podcast:
                print("Note: --podcast flag is ignored in scan mode. Use --mode=full or --mode=email to generate podcasts.")
        
        elif args.mode == 'full':
            app.run_full_digest(generate_podcast=args.podcast)
            
        elif args.mode == 'email':
            app.run_full_digest_with_email(dry_run=args.dry_run, generate_podcast=args.podcast)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
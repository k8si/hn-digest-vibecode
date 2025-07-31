"""Email sending functionality using SendGrid."""
import logging
import time
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from .config import Config

logger = logging.getLogger(__name__)

class EmailSender:
    """Handles email sending via SendGrid with retry logic."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the email sender.
        
        Args:
            api_key: SendGrid API key (defaults to Config.SENDGRID_API_KEY)
        """
        self.api_key = api_key or Config.SENDGRID_API_KEY
        if not self.api_key:
            raise ValueError("SendGrid API key is required")
        
        self.client = SendGridAPIClient(api_key=self.api_key)
        self.from_email = Email("noreply@hackernews-digest.com", "HN AI Digest")
        self.to_email = To(Config.EMAIL_RECIPIENT, Config.USERNAME)
    
    def send_digest_email(
        self, 
        subject: str, 
        content: str, 
        max_retries: int = 3,
        retry_delay: float = 5.0
    ) -> bool:
        """
        Send digest email with retry logic.
        
        Args:
            subject: Email subject line
            content: Plain text email content
            max_retries: Maximum number of retry attempts
            retry_delay: Seconds to wait between retries
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        logger.info(f"Attempting to send email: {subject}")
        
        # Create email message
        mail = Mail(
            from_email=self.from_email,
            to_emails=self.to_email,
            subject=subject,
            plain_text_content=Content("text/plain", content)
        )
        
        # Attempt to send with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.client.send(mail)
                
                # SendGrid returns 202 for successful acceptance
                if response.status_code == 202:
                    logger.info(f"Email sent successfully on attempt {attempt + 1}")
                    return True
                else:
                    logger.warning(f"SendGrid returned unexpected status code: {response.status_code}")
                    last_error = f"Unexpected status code: {response.status_code}"
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Email send attempt {attempt + 1} failed: {last_error}")
                
                # If this isn't the last attempt, wait before retrying
                if attempt < max_retries - 1:
                    logger.info(f"Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    # Exponential backoff for subsequent retries
                    retry_delay *= 2
        
        logger.error(f"Failed to send email after {max_retries} attempts. Last error: {last_error}")
        return False
    
    def send_fallback_email(self, error_message: str) -> bool:
        """
        Send a fallback email when digest generation fails.
        
        Args:
            error_message: Description of what went wrong
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        from .email_formatter import EmailFormatter
        
        formatter = EmailFormatter()
        subject = formatter.create_subject_line(story_count=0)
        content = formatter.create_fallback_email(error_message)
        
        logger.warning(f"Sending fallback email due to: {error_message}")
        return self.send_digest_email(subject, content)
    
    def test_connection(self) -> bool:
        """
        Test SendGrid API connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            # Try to get API key info (this doesn't send an email)
            response = self.client.client.user.profile.get()
            logger.info("SendGrid API connection test successful")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"SendGrid API connection test failed: {e}")
            return False
    
    def validate_configuration(self) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        issues = []
        
        if not self.api_key:
            issues.append("SENDGRID_API_KEY is not set")
        
        if not Config.EMAIL_RECIPIENT:
            issues.append("EMAIL_RECIPIENT is not set")
        
        if issues:
            logger.error(f"Email configuration issues: {', '.join(issues)}")
            return False
        
        logger.info("Email configuration validation passed")
        return True
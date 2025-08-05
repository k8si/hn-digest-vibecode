"""Email sending functionality using Gmail SMTP."""
import logging
import smtplib
import time
from email.mime.text import MIMEText
from typing import Optional
from .config import Config

logger = logging.getLogger(__name__)

class EmailSender:
    """Handles email sending via Gmail SMTP with retry logic."""
    
    def __init__(self, gmail_username: Optional[str] = None, gmail_password: Optional[str] = None):
        """
        Initialize the email sender.
        
        Args:
            gmail_username: Gmail username (defaults to Config.GMAIL_USERNAME)
            gmail_password: Gmail App Password (defaults to Config.GMAIL_PASSWORD)
        """
        self.gmail_username = gmail_username or Config.GMAIL_USERNAME
        self.gmail_password = gmail_password or Config.GMAIL_PASSWORD
        
        if not self.gmail_username:
            raise ValueError("Gmail username is required")
        if not self.gmail_password:
            raise ValueError("Gmail App Password is required")
        
        self.from_email = self.gmail_username
        self.to_email = Config.EMAIL_RECIPIENT
    
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
        msg = MIMEText(content)
        msg['Subject'] = subject
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        
        # Attempt to send with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(self.gmail_username, self.gmail_password)
                    server.sendmail(self.from_email, [self.to_email], msg.as_string())
                
                logger.info(f"Email sent successfully on attempt {attempt + 1}")
                return True
                    
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
        Test Gmail SMTP connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_username, self.gmail_password)
            logger.info("Gmail SMTP connection test successful")
            return True
        except Exception as e:
            logger.error(f"Gmail SMTP connection test failed: {e}")
            return False
    
    def validate_configuration(self) -> bool:
        """
        Validate that all required configuration is present.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        issues = []
        
        if not self.gmail_username:
            issues.append("GMAIL_USERNAME is not set")
        
        if not self.gmail_password:
            issues.append("GMAIL_PASSWORD is not set")
        
        if not Config.EMAIL_RECIPIENT:
            issues.append("EMAIL_RECIPIENT is not set")
        
        if issues:
            logger.error(f"Email configuration issues: {', '.join(issues)}")
            return False
        
        logger.info("Email configuration validation passed")
        return True
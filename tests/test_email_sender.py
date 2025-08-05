"""Unit tests for email sender."""
import pytest
import smtplib
from unittest.mock import Mock, patch, MagicMock
from src.hn_digest.email_sender import EmailSender

class TestEmailSender:
    """Test cases for EmailSender class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('src.hn_digest.email_sender.Config.GMAIL_USERNAME', 'test@gmail.com'):
            with patch('src.hn_digest.email_sender.Config.GMAIL_PASSWORD', 'test_password'):
                with patch('src.hn_digest.email_sender.Config.EMAIL_RECIPIENT', 'recipient@example.com'):
                    self.sender = EmailSender()
    
    def test_init_with_credentials(self):
        """Test EmailSender initialization with custom credentials."""
        sender = EmailSender(gmail_username='custom@gmail.com', gmail_password='custom_password')
        assert sender.gmail_username == 'custom@gmail.com'
        assert sender.gmail_password == 'custom_password'
        assert sender.from_email == 'custom@gmail.com'
    
    def test_init_no_username_raises_error(self):
        """Test EmailSender initialization without username raises error."""
        with patch('src.hn_digest.email_sender.Config.GMAIL_USERNAME', None):
            with patch('src.hn_digest.email_sender.Config.GMAIL_PASSWORD', 'password'):
                with pytest.raises(ValueError, match="Gmail username is required"):
                    EmailSender()
    
    def test_init_no_password_raises_error(self):
        """Test EmailSender initialization without password raises error."""
        with patch('src.hn_digest.email_sender.Config.GMAIL_USERNAME', 'user@gmail.com'):
            with patch('src.hn_digest.email_sender.Config.GMAIL_PASSWORD', None):
                with pytest.raises(ValueError, match="Gmail App Password is required"):
                    EmailSender()
    
    @patch('src.hn_digest.email_sender.Config.GMAIL_USERNAME', 'sender@gmail.com')
    @patch('src.hn_digest.email_sender.Config.GMAIL_PASSWORD', 'app_password')
    @patch('src.hn_digest.email_sender.Config.EMAIL_RECIPIENT', 'user@example.com')
    def test_email_addresses_configuration(self):
        """Test that email addresses are configured correctly."""
        sender = EmailSender()
        
        assert sender.gmail_username == "sender@gmail.com"
        assert sender.from_email == "sender@gmail.com"
        assert sender.to_email == "user@example.com"
    
    @patch('src.hn_digest.email_sender.smtplib.SMTP_SSL')
    def test_send_digest_email_success(self, mock_smtp_ssl):
        """Test successful email sending."""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
        
        # Test successful send
        result = self.sender.send_digest_email("Test Subject", "Test Content")
        
        assert result is True
        mock_smtp_ssl.assert_called_once_with('smtp.gmail.com', 465)
        mock_server.login.assert_called_once_with(self.sender.gmail_username, self.sender.gmail_password)
        mock_server.sendmail.assert_called_once()
    
    @patch('src.hn_digest.email_sender.smtplib.SMTP_SSL')
    @patch('src.hn_digest.email_sender.time.sleep')
    def test_send_digest_email_failure_with_retries(self, mock_sleep, mock_smtp_ssl):
        """Test email sending with retries on failure."""
        # Mock SMTP server to always fail
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPException("Connection failed")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
        
        # Test failed send with retries
        result = self.sender.send_digest_email("Test Subject", "Test Content", max_retries=2, retry_delay=0.1)
        
        assert result is False
        assert mock_smtp_ssl.call_count == 2  # Should retry once
        assert mock_sleep.call_count == 1  # Should sleep between retries
    
    @patch('src.hn_digest.email_sender.smtplib.SMTP_SSL')
    def test_send_digest_email_partial_failure_then_success(self, mock_smtp_ssl):
        """Test email sending that fails once then succeeds."""
        # Mock SMTP server to fail first, then succeed
        mock_server = Mock()
        mock_server.login.side_effect = [smtplib.SMTPException("Temporary failure"), None]
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
        
        # Test successful send after one failure
        result = self.sender.send_digest_email("Test Subject", "Test Content", max_retries=3, retry_delay=0.01)
        
        assert result is True
        assert mock_smtp_ssl.call_count == 2  # First failure, then success
    
    @patch('src.hn_digest.email_formatter.EmailFormatter')
    @patch.object(EmailSender, 'send_digest_email')
    def test_send_fallback_email(self, mock_send_digest, mock_formatter_class):
        """Test sending fallback email."""
        # Mock formatter
        mock_formatter = Mock()
        mock_formatter_class.return_value = mock_formatter
        mock_formatter.create_subject_line.return_value = "Test Subject"
        mock_formatter.create_fallback_email.return_value = "Fallback content"
        
        # Mock successful digest send
        mock_send_digest.return_value = True
        
        # Test fallback email
        result = self.sender.send_fallback_email("Test error")
        
        assert result is True
        mock_formatter.create_subject_line.assert_called_once_with(story_count=0)
        mock_formatter.create_fallback_email.assert_called_once_with("Test error")
        mock_send_digest.assert_called_once_with("Test Subject", "Fallback content")
    
    @patch('src.hn_digest.email_sender.smtplib.SMTP_SSL')
    def test_test_connection_success(self, mock_smtp_ssl):
        """Test successful connection test."""
        # Mock successful connection
        mock_server = Mock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
        
        result = self.sender.test_connection()
        
        assert result is True
        mock_smtp_ssl.assert_called_once_with('smtp.gmail.com', 465)
        mock_server.login.assert_called_once_with(self.sender.gmail_username, self.sender.gmail_password)
    
    @patch('src.hn_digest.email_sender.smtplib.SMTP_SSL')
    def test_test_connection_failure(self, mock_smtp_ssl):
        """Test connection test failure."""
        # Mock connection failure
        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPException("Auth failed")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
        
        result = self.sender.test_connection()
        
        assert result is False
    
    @patch('src.hn_digest.email_sender.Config.GMAIL_USERNAME', 'user@gmail.com')
    @patch('src.hn_digest.email_sender.Config.GMAIL_PASSWORD', 'password')
    @patch('src.hn_digest.email_sender.Config.EMAIL_RECIPIENT', 'recipient@example.com')
    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        sender = EmailSender()
        result = sender.validate_configuration()
        
        assert result is True
    
    def test_validate_configuration_missing_username(self):
        """Test configuration validation with missing username."""
        with patch('src.hn_digest.email_sender.Config.GMAIL_USERNAME', None):
            with patch('src.hn_digest.email_sender.Config.GMAIL_PASSWORD', 'password'):
                with patch('src.hn_digest.email_sender.Config.EMAIL_RECIPIENT', 'recipient@example.com'):
                    with pytest.raises(ValueError, match="Gmail username is required"):
                        EmailSender()
    
    def test_validate_configuration_missing_password(self):
        """Test configuration validation with missing password."""
        with patch('src.hn_digest.email_sender.Config.GMAIL_USERNAME', 'user@gmail.com'):
            with patch('src.hn_digest.email_sender.Config.GMAIL_PASSWORD', None):
                with patch('src.hn_digest.email_sender.Config.EMAIL_RECIPIENT', 'recipient@example.com'):
                    with pytest.raises(ValueError, match="Gmail App Password is required"):
                        EmailSender()
    
    @patch('src.hn_digest.email_sender.Config.GMAIL_USERNAME', 'user@gmail.com')
    @patch('src.hn_digest.email_sender.Config.GMAIL_PASSWORD', 'password')
    @patch('src.hn_digest.email_sender.Config.EMAIL_RECIPIENT', None)
    def test_validate_configuration_missing_recipient(self):
        """Test configuration validation with missing recipient."""
        sender = EmailSender()
        result = sender.validate_configuration()
        
        assert result is False
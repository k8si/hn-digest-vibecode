"""Unit tests for email sender."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.hn_digest.email_sender import EmailSender

class TestEmailSender:
    """Test cases for EmailSender class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', 'test_api_key'):
            with patch('src.hn_digest.email_sender.Config.EMAIL_RECIPIENT', 'test@example.com'):
                with patch('src.hn_digest.email_sender.Config.USERNAME', 'TestUser'):
                    with patch('src.hn_digest.email_sender.SendGridAPIClient'):
                        self.sender = EmailSender()
    
    def test_init_with_api_key(self):
        """Test EmailSender initialization with API key."""
        with patch('src.hn_digest.email_sender.SendGridAPIClient') as mock_sg:
            sender = EmailSender(api_key='custom_key')
            assert sender.api_key == 'custom_key'
            mock_sg.assert_called_once_with(api_key='custom_key')
    
    def test_init_no_api_key_raises_error(self):
        """Test EmailSender initialization without API key raises error."""
        with patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', None):
            with pytest.raises(ValueError, match="SendGrid API key is required"):
                EmailSender()
    
    @patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', 'test_key')
    @patch('src.hn_digest.email_sender.Config.EMAIL_RECIPIENT', 'user@example.com')
    @patch('src.hn_digest.email_sender.Config.USERNAME', 'Alice')
    def test_email_addresses_configuration(self):
        """Test that email addresses are configured correctly."""
        with patch('src.hn_digest.email_sender.SendGridAPIClient'):
            sender = EmailSender()
            
            assert sender.from_email.email == "noreply@hackernews-digest.com"
            assert sender.from_email.name == "HN AI Digest"
            assert sender.to_email.email == "user@example.com"
            assert sender.to_email.name == "Alice"
    
    @patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', 'test_key')
    def test_send_digest_email_success(self):
        """Test successful email sending."""
        with patch('src.hn_digest.email_sender.SendGridAPIClient') as mock_sg_class:
            mock_client = Mock()
            mock_sg_class.return_value = mock_client
            
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 202
            mock_client.send.return_value = mock_response
            
            sender = EmailSender()
            
            result = sender.send_digest_email("Test Subject", "Test Content")
            
            assert result is True
            mock_client.send.assert_called_once()
    
    @patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', 'test_key')
    def test_send_digest_email_failure_with_retries(self):
        """Test email sending failure with retry logic."""
        with patch('src.hn_digest.email_sender.SendGridAPIClient') as mock_sg_class:
            with patch('time.sleep') as mock_sleep:  # Speed up test
                mock_client = Mock()
                mock_sg_class.return_value = mock_client
                
                # Mock failure
                mock_client.send.side_effect = Exception("SendGrid error")
                
                sender = EmailSender()
                
                result = sender.send_digest_email("Test Subject", "Test Content", max_retries=2)
                
                assert result is False
                assert mock_client.send.call_count == 2  # Should retry
                mock_sleep.assert_called()  # Should sleep between retries
    
    @patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', 'test_key')
    def test_send_digest_email_unexpected_status_code(self):
        """Test handling of unexpected status codes."""
        with patch('src.hn_digest.email_sender.SendGridAPIClient') as mock_sg_class:
            with patch('time.sleep'):
                mock_client = Mock()
                mock_sg_class.return_value = mock_client
                
                # Mock unexpected status code
                mock_response = Mock()
                mock_response.status_code = 400
                mock_client.send.return_value = mock_response
                
                sender = EmailSender()
                
                result = sender.send_digest_email("Test Subject", "Test Content", max_retries=1)
                
                assert result is False
    
    @patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', 'test_key')
    def test_send_fallback_email(self):
        """Test sending fallback email."""
        with patch('src.hn_digest.email_sender.SendGridAPIClient') as mock_sg_class:
            mock_client = Mock()
            mock_sg_class.return_value = mock_client
            
            mock_response = Mock()
            mock_response.status_code = 202
            mock_client.send.return_value = mock_response
            
            sender = EmailSender()
            
            result = sender.send_fallback_email("Test error message")
            
            assert result is True
            mock_client.send.assert_called_once()
            
            # Check that the email content includes the error message
            call_args = mock_client.send.call_args[0][0]  # Get the Mail object
            assert "Test error message" in call_args.contents[0].content
    
    @patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', 'test_key')
    def test_test_connection_success(self):
        """Test successful connection test."""
        with patch('src.hn_digest.email_sender.SendGridAPIClient') as mock_sg_class:
            mock_client = Mock()
            mock_sg_class.return_value = mock_client
            
            # Mock successful profile response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.client.user.profile.get.return_value = mock_response
            
            sender = EmailSender()
            
            result = sender.test_connection()
            
            assert result is True
    
    @patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', 'test_key')
    def test_test_connection_failure(self):
        """Test connection test failure."""
        with patch('src.hn_digest.email_sender.SendGridAPIClient') as mock_sg_class:
            mock_client = Mock()
            mock_sg_class.return_value = mock_client
            
            # Mock connection failure
            mock_client.client.user.profile.get.side_effect = Exception("Connection error")
            
            sender = EmailSender()
            
            result = sender.test_connection()
            
            assert result is False
    
    @patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', 'test_key')
    @patch('src.hn_digest.email_sender.Config.EMAIL_RECIPIENT', 'user@example.com')
    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        with patch('src.hn_digest.email_sender.SendGridAPIClient'):
            sender = EmailSender()
            
            result = sender.validate_configuration()
            
            assert result is True
    
    @patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', None)
    @patch('src.hn_digest.email_sender.Config.EMAIL_RECIPIENT', 'user@example.com')
    def test_validate_configuration_missing_api_key(self):
        """Test configuration validation with missing API key."""
        # This test checks the validation logic, but we need to create sender differently
        # since __init__ will fail without API key
        with patch('src.hn_digest.email_sender.SendGridAPIClient'):
            sender = EmailSender.__new__(EmailSender)  # Create without calling __init__
            sender.api_key = None
            
            result = sender.validate_configuration()
            
            assert result is False
    
    @patch('src.hn_digest.email_sender.Config.SENDGRID_API_KEY', 'test_key')
    @patch('src.hn_digest.email_sender.Config.EMAIL_RECIPIENT', None)
    def test_validate_configuration_missing_recipient(self):
        """Test configuration validation with missing recipient."""
        with patch('src.hn_digest.email_sender.SendGridAPIClient'):
            sender = EmailSender()
            
            result = sender.validate_configuration()
            
            assert result is False
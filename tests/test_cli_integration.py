"""
Tests for CLI integration and podcast workflow.
"""

import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.hn_digest.main import create_cli_parser, HNDigestApp
from src.hn_digest.podcast_generator import PodcastGenerator


class TestCLIIntegration:
    """Test CLI argument parsing for podcast functionality."""
    
    def test_cli_parser_includes_podcast_flag(self):
        """Test that CLI parser includes --podcast flag."""
        parser = create_cli_parser()
        
        # Test without podcast flag
        args = parser.parse_args(['--mode', 'full'])
        assert args.podcast is False
        
        # Test with podcast flag
        args = parser.parse_args(['--mode', 'full', '--podcast'])
        assert args.podcast is True
        
    def test_cli_parser_podcast_help(self):
        """Test that podcast flag has help text."""
        parser = create_cli_parser()
        
        # Check help text includes podcast option
        help_text = parser.format_help()
        assert '--podcast' in help_text
        assert 'Generate podcast audio file' in help_text
        
    def test_cli_parser_podcast_with_all_modes(self):
        """Test podcast flag works with all modes."""
        parser = create_cli_parser()
        
        # Test with scan mode
        args = parser.parse_args(['--mode', 'scan', '--podcast'])
        assert args.mode == 'scan'
        assert args.podcast is True
        
        # Test with full mode
        args = parser.parse_args(['--mode', 'full', '--podcast'])
        assert args.mode == 'full'
        assert args.podcast is True
        
        # Test with email mode
        args = parser.parse_args(['--mode', 'email', '--podcast'])
        assert args.mode == 'email'
        assert args.podcast is True


class TestWorkflowIntegration:
    """Test podcast generation integration in workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = HNDigestApp()
        
    @patch('src.hn_digest.main.Config.OPENAI_API_KEY', 'test-key')
    @patch('src.hn_digest.main.Config.TTS_VOICE', 'fable')
    def test_podcast_generator_initialization(self):
        """Test that podcast generator is initialized correctly."""
        with patch('src.hn_digest.main.PodcastGenerator') as mock_pg_class:
            mock_generator = Mock()
            mock_pg_class.return_value = mock_generator
            
            # Get podcast generator
            generator = self.app._get_podcast_generator()
            
            # Verify initialization
            mock_pg_class.assert_called_once_with(
                api_key='test-key',
                voice='fable'
            )
            assert self.app.podcast_generator == mock_generator
            
            # Verify cached instance
            generator2 = self.app._get_podcast_generator()
            assert generator2 == mock_generator
            mock_pg_class.assert_called_once()  # Should not be called again
    
    def test_generate_podcast_method(self):
        """Test the generate_podcast method."""
        with patch.object(self.app, '_get_podcast_generator') as mock_get_pg:
            mock_generator = Mock()
            mock_get_pg.return_value = mock_generator
            mock_generator.generate_podcast.return_value = True
            
            # Test successful generation
            result = self.app.generate_podcast("Test content", "test.mp3")
            
            assert result is True
            mock_generator.generate_podcast.assert_called_once_with("Test content", "test.mp3")
    
    def test_generate_podcast_method_failure(self):
        """Test generate_podcast method handles failures."""
        with patch.object(self.app, '_get_podcast_generator') as mock_get_pg:
            mock_generator = Mock()
            mock_get_pg.return_value = mock_generator
            mock_generator.generate_podcast.return_value = False
            
            # Test failed generation
            result = self.app.generate_podcast("Test content", "test.mp3")
            
            assert result is False
    
    def test_generate_podcast_method_exception(self):
        """Test generate_podcast method handles exceptions."""
        with patch.object(self.app, '_get_podcast_generator') as mock_get_pg:
            mock_get_pg.side_effect = Exception("Test error")
            
            # Test exception handling
            result = self.app.generate_podcast("Test content", "test.mp3")
            
            assert result is False

    @patch('src.hn_digest.main.datetime')
    def test_run_full_digest_with_podcast(self, mock_datetime):
        """Test run_full_digest with podcast generation."""
        # Mock datetime for consistent timestamps
        mock_now = Mock()
        mock_now.strftime.return_value = "20250805_120000"
        mock_datetime.now.return_value = mock_now
        
        # Mock the workflow components
        mock_stories = [{'title': 'AI Story', 'url': 'http://example.com', 'score': 100}]
        mock_summaries = {'http://example.com': 'Test summary'}
        mock_digest_text = "Test digest content"
        
        with patch.object(self.app, 'fetch_and_filter_stories', return_value=mock_stories):
            with patch.object(self.app, 'scrape_and_summarize_stories', return_value=mock_summaries):
                with patch.object(self.app.summary_formatter, 'format_digest', return_value=mock_digest_text):
                    with patch('builtins.open', create=True) as mock_open:
                        with patch.object(self.app, 'generate_podcast', return_value=True) as mock_gen_podcast:
                            with patch('src.hn_digest.main.PodcastGenerator.get_podcast_filename', return_value='digest_20250805_120000.mp3'):
                                
                                # Run with podcast generation
                                self.app.run_full_digest(generate_podcast=True)
                                
                                # Verify file was written
                                mock_open.assert_called_once_with('digest_20250805_120000.txt', 'w', encoding='utf-8')
                                mock_open.return_value.__enter__.return_value.write.assert_called_once_with(mock_digest_text)
                                
                                # Verify podcast generation was called
                                mock_gen_podcast.assert_called_once_with(mock_digest_text, 'digest_20250805_120000.mp3')

    def test_run_full_digest_without_podcast(self):
        """Test run_full_digest without podcast generation."""
        # Mock the workflow components
        mock_stories = [{'title': 'AI Story', 'url': 'http://example.com', 'score': 100}]
        mock_summaries = {'http://example.com': 'Test summary'}
        mock_digest_text = "Test digest content"
        
        with patch.object(self.app, 'fetch_and_filter_stories', return_value=mock_stories):
            with patch.object(self.app, 'scrape_and_summarize_stories', return_value=mock_summaries):
                with patch.object(self.app.summary_formatter, 'format_digest', return_value=mock_digest_text):
                    with patch('builtins.open', create=True):
                        with patch.object(self.app, 'generate_podcast') as mock_gen_podcast:
                            
                            # Run without podcast generation
                            self.app.run_full_digest(generate_podcast=False)
                            
                            # Verify podcast generation was not called
                            mock_gen_podcast.assert_not_called()

    def test_handle_email_failure_with_podcast(self):
        """Test _handle_email_failure with podcast generation."""
        mock_email_content = "Test email content"
        error_message = "Email failed"
        
        with patch('builtins.open', create=True) as mock_open:
            with patch.object(self.app, 'generate_podcast', return_value=True) as mock_gen_podcast:
                with patch('src.hn_digest.main.PodcastGenerator.get_podcast_filename', return_value='digest_backup_20250805_120000.mp3'):
                    with patch('src.hn_digest.main.datetime') as mock_datetime:
                        mock_datetime.now.return_value.strftime.return_value = "20250805_120000"
                        
                        # Call with podcast generation
                        self.app._handle_email_failure(mock_email_content, error_message, generate_podcast=True)
                        
                        # Verify file was written
                        expected_filename = 'digest_backup_20250805_120000.txt'
                        mock_open.assert_called_once()
                        call_args = mock_open.call_args[0]
                        assert call_args[0] == expected_filename
                        
                        # Verify podcast generation was called
                        mock_gen_podcast.assert_called_once_with(mock_email_content, 'digest_backup_20250805_120000.mp3')

    def test_handle_email_failure_without_podcast(self):
        """Test _handle_email_failure without podcast generation."""
        mock_email_content = "Test email content"
        error_message = "Email failed"
        
        with patch('builtins.open', create=True):
            with patch.object(self.app, 'generate_podcast') as mock_gen_podcast:
                with patch('src.hn_digest.main.datetime') as mock_datetime:
                    mock_datetime.now.return_value.strftime.return_value = "20250805_120000"
                    
                    # Call without podcast generation
                    self.app._handle_email_failure(mock_email_content, error_message, generate_podcast=False)
                    
                    # Verify podcast generation was not called
                    mock_gen_podcast.assert_not_called()


class TestFilenameGeneration:
    """Test filename generation and file handling."""
    
    def test_podcast_filename_generation_integration(self):
        """Test that podcast filename generation works in workflow context."""
        # Test typical digest filename
        digest_filename = "digest_20250805_120000.txt"
        podcast_filename = PodcastGenerator.get_podcast_filename(digest_filename)
        assert podcast_filename == "digest_20250805_120000.mp3"
        
        # Test backup filename
        backup_filename = "digest_backup_20250805_120000.txt"
        podcast_filename = PodcastGenerator.get_podcast_filename(backup_filename)
        assert podcast_filename == "digest_backup_20250805_120000.mp3"
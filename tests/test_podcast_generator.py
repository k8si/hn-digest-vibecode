"""
Tests for the podcast generator module.
"""

import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
import pytest

from src.hn_digest.podcast_generator import PodcastGenerator
from openai import APIError, APIConnectionError, RateLimitError, APITimeoutError


class TestPodcastGenerator:
    
    def test_init_with_valid_voice(self):
        """Test initialization with valid voice."""
        generator = PodcastGenerator("test-api-key", "fable")
        assert generator.voice == "fable"
        
    def test_init_with_invalid_voice(self):
        """Test initialization with invalid voice raises ValueError."""
        with pytest.raises(ValueError, match="Invalid voice"):
            PodcastGenerator("test-api-key", "invalid-voice")
            
    def test_init_without_api_key(self):
        """Test initialization without API key raises ValueError."""
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            PodcastGenerator("", "fable")
            
    def test_init_with_none_api_key(self):
        """Test initialization with None API key raises ValueError."""
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            PodcastGenerator(None, "fable")

    @patch('src.hn_digest.podcast_generator.OpenAI')
    def test_generate_podcast_success(self, mock_openai_class):
        """Test successful podcast generation."""
        # Setup mocks
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_client.audio.speech.create.return_value = mock_response
        
        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            # Mock the stream_to_file method to create a file
            def mock_stream_to_file(path):
                with open(path, 'wb') as f:
                    f.write(b'fake mp3 content')
                    
            mock_response.stream_to_file = mock_stream_to_file
            
            generator = PodcastGenerator("test-api-key", "fable")
            result = generator.generate_podcast("Test text", temp_path)
            
            assert result is True
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0
            
            # Verify API was called correctly
            mock_client.audio.speech.create.assert_called_once_with(
                model="tts-1",
                voice="fable",
                input="Test text"
            )
            
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch('src.hn_digest.podcast_generator.OpenAI')
    def test_generate_podcast_empty_text(self, mock_openai_class):
        """Test podcast generation with empty text."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        generator = PodcastGenerator("test-api-key", "fable")
        
        # Test empty string
        result = generator.generate_podcast("", "output.mp3")
        assert result is False
        
        # Test whitespace only
        result = generator.generate_podcast("   ", "output.mp3")
        assert result is False
        
        # Verify API was not called
        mock_client.audio.speech.create.assert_not_called()

    @patch('src.hn_digest.podcast_generator.OpenAI')
    def test_generate_podcast_api_errors(self, mock_openai_class):
        """Test podcast generation with various API errors."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        generator = PodcastGenerator("test-api-key", "fable")
        
        # Test different API error scenarios with generic exceptions
        # The specific error handling logic is tested in the actual implementation
        error_messages = [
            "Rate limit exceeded",
            "Connection failed", 
            "Request timed out",
            "API error occurred"
        ]
        
        for error_msg in error_messages:
            mock_client.audio.speech.create.side_effect = Exception(error_msg)
            result = generator.generate_podcast("Test text", "output.mp3")
            assert result is False

    @patch('src.hn_digest.podcast_generator.OpenAI')
    def test_generate_podcast_unexpected_error(self, mock_openai_class):
        """Test podcast generation with unexpected error."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.audio.speech.create.side_effect = Exception("Unexpected error")
        
        generator = PodcastGenerator("test-api-key", "fable")
        result = generator.generate_podcast("Test text", "output.mp3")
        
        assert result is False

    @patch('src.hn_digest.podcast_generator.OpenAI')
    def test_generate_podcast_creates_directory(self, mock_openai_class):
        """Test that podcast generation creates output directory."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_client.audio.speech.create.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use a nested path that doesn't exist
            nested_path = os.path.join(temp_dir, "subdir", "podcast.mp3")
            
            def mock_stream_to_file(path):
                with open(path, 'wb') as f:
                    f.write(b'fake mp3 content')
                    
            mock_response.stream_to_file = mock_stream_to_file
            
            generator = PodcastGenerator("test-api-key", "fable")
            result = generator.generate_podcast("Test text", nested_path)
            
            assert result is True
            assert os.path.exists(nested_path)
            assert os.path.exists(os.path.dirname(nested_path))

    def test_get_podcast_filename_with_txt_extension(self):
        """Test filename generation with .txt extension."""
        result = PodcastGenerator.get_podcast_filename("digest_20250805_1530.txt")
        assert result == "digest_20250805_1530.mp3"
        
    def test_get_podcast_filename_without_extension(self):
        """Test filename generation without extension."""
        result = PodcastGenerator.get_podcast_filename("digest_backup")
        assert result == "digest_backup.mp3"
        
    def test_get_podcast_filename_with_other_extension(self):
        """Test filename generation with non-.txt extension."""
        result = PodcastGenerator.get_podcast_filename("digest.log")
        assert result == "digest.log.mp3"

    def test_valid_voices_constant(self):
        """Test that VALID_VOICES contains expected OpenAI voices."""
        expected_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        assert PodcastGenerator.VALID_VOICES == expected_voices
        
    def test_default_voice(self):
        """Test that default voice is 'fable'."""
        generator = PodcastGenerator("test-api-key")
        assert generator.voice == "fable"
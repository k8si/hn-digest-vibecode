"""
Podcast generation module for converting text digests to audio using OpenAI TTS.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError, APITimeoutError

logger = logging.getLogger(__name__)


class PodcastGenerator:
    """Handles text-to-speech conversion using OpenAI TTS API."""
    
    # Valid OpenAI TTS voices
    VALID_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    def __init__(self, api_key: str, voice: str = "fable"):
        """
        Initialize the podcast generator.
        
        Args:
            api_key: OpenAI API key
            voice: TTS voice to use (default: "fable")
            
        Raises:
            ValueError: If voice is not valid
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")
            
        if voice not in self.VALID_VOICES:
            raise ValueError(f"Invalid voice '{voice}'. Must be one of: {', '.join(self.VALID_VOICES)}")
            
        self.client = OpenAI(api_key=api_key)
        self.voice = voice
        
    def generate_podcast(self, text: str, output_path: str) -> bool:
        """
        Generate a podcast MP3 file from text.
        
        Args:
            text: Text content to convert to speech
            output_path: Path where MP3 file should be saved
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not text or not text.strip():
            logger.error("Cannot generate podcast from empty text")
            return False
            
        logger.info(f"Starting podcast generation using voice '{self.voice}' to {output_path}")
        
        try:
            # Create directory if it doesn't exist
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Make TTS API call
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=text
            )
            
            # Write MP3 data to file
            response.stream_to_file(output_path)
            
            # Verify file was created and get size
            if not os.path.exists(output_path):
                logger.error(f"Podcast file was not created at {output_path}")
                return False
                
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                logger.error(f"Generated podcast file is empty: {output_path}")
                return False
                
            logger.info(f"Podcast generation completed. File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            return True
            
        except RateLimitError as e:
            logger.error(f"OpenAI API rate limit exceeded: {e}")
            return False
        except APIConnectionError as e:
            logger.error(f"Failed to connect to OpenAI API: {e}")
            return False
        except APITimeoutError as e:
            logger.error(f"OpenAI API request timed out: {e}")
            return False
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during podcast generation: {e}")
            return False
            
    @staticmethod
    def get_podcast_filename(digest_filename: str) -> str:
        """
        Generate podcast filename based on digest filename.
        
        Args:
            digest_filename: The filename of the text digest
            
        Returns:
            str: Podcast filename with .mp3 extension
        """
        # Replace .txt extension with .mp3, or add .mp3 if no extension
        if digest_filename.endswith('.txt'):
            return digest_filename.replace('.txt', '.mp3')
        else:
            return f"{digest_filename}.mp3"
"""
Podcast generation module for converting text digests to audio using OpenAI TTS.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, List
import re

from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError, APITimeoutError

logger = logging.getLogger(__name__)


class PodcastGenerator:
    """Handles text-to-speech conversion using OpenAI TTS API."""
    
    # Valid OpenAI TTS voices
    VALID_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    # OpenAI TTS API character limit
    MAX_CHUNK_SIZE = 4000  # Leave some buffer below the 4096 limit
    
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
        
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """
        Split text into chunks that fit within OpenAI TTS character limit.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks, each under MAX_CHUNK_SIZE characters
        """
        if len(text) <= self.MAX_CHUNK_SIZE:
            return [text]
        
        chunks = []
        remaining_text = text
        
        while remaining_text:
            if len(remaining_text) <= self.MAX_CHUNK_SIZE:
                chunks.append(remaining_text)
                break
                
            # Find a good breaking point within the limit
            chunk = remaining_text[:self.MAX_CHUNK_SIZE]
            
            # Try to break at sentence boundaries first
            sentence_break = max(
                chunk.rfind('. '),
                chunk.rfind('! '),
                chunk.rfind('? ')
            )
            
            if sentence_break > self.MAX_CHUNK_SIZE * 0.7:  # If we found a good sentence break
                chunk = remaining_text[:sentence_break + 2]  # Include the punctuation and space
            else:
                # Try to break at paragraph boundaries
                paragraph_break = chunk.rfind('\n\n')
                if paragraph_break > self.MAX_CHUNK_SIZE * 0.7:
                    chunk = remaining_text[:paragraph_break + 2]
                else:
                    # Try to break at word boundaries
                    word_break = chunk.rfind(' ')
                    if word_break > self.MAX_CHUNK_SIZE * 0.8:
                        chunk = remaining_text[:word_break]
                    # Otherwise use the full chunk (will be cut at character boundary)
            
            chunks.append(chunk)
            remaining_text = remaining_text[len(chunk):].lstrip()
        
        logger.info(f"Split text ({len(text):,} chars) into {len(chunks)} chunks")
        return chunks
    
    def _combine_audio_files(self, audio_files: List[str], output_path: str) -> bool:
        """
        Combine multiple audio files into a single MP3 file.
        
        Args:
            audio_files: List of temporary audio file paths
            output_path: Final output path for combined audio
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Simple concatenation - read all files and write sequentially
            with open(output_path, 'wb') as output_file:
                for audio_file in audio_files:
                    with open(audio_file, 'rb') as input_file:
                        output_file.write(input_file.read())
                        
            logger.info(f"Combined {len(audio_files)} audio files into {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to combine audio files: {e}")
            return False
    
    def generate_podcast(self, text: str, output_path: str) -> bool:
        """
        Generate a podcast MP3 file from text.
        Handles long text by splitting into chunks and combining audio files.
        
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
        logger.info(f"Input text length: {len(text):,} characters")
        
        try:
            # Create directory if it doesn't exist
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Split text into chunks if needed
            text_chunks = self._split_text_into_chunks(text)
            
            if len(text_chunks) == 1:
                # Single chunk - use original simple approach
                return self._generate_single_chunk(text, output_path)
            else:
                # Multiple chunks - generate each chunk and combine
                return self._generate_multiple_chunks(text_chunks, output_path)
                
        except Exception as e:
            logger.error(f"Unexpected error during podcast generation: {e}")
            return False
    
    def _generate_single_chunk(self, text: str, output_path: str) -> bool:
        """Generate podcast from a single text chunk."""
        try:
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
    
    def _generate_multiple_chunks(self, text_chunks: List[str], output_path: str) -> bool:
        """Generate podcast from multiple text chunks and combine them."""
        temp_files = []
        
        try:
            # Generate audio for each chunk
            for i, chunk in enumerate(text_chunks):
                logger.info(f"Processing chunk {i+1}/{len(text_chunks)} ({len(chunk)} chars)")
                
                # Create temporary file for this chunk
                temp_fd, temp_path = tempfile.mkstemp(suffix='.mp3', prefix=f'podcast_chunk_{i}_')
                os.close(temp_fd)  # Close the file descriptor, we'll use the path
                temp_files.append(temp_path)
                
                try:
                    # Make TTS API call for this chunk
                    response = self.client.audio.speech.create(
                        model="tts-1",
                        voice=self.voice,
                        input=chunk
                    )
                    
                    # Write MP3 data to temporary file
                    response.stream_to_file(temp_path)
                    
                    # Verify chunk file was created
                    if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                        logger.error(f"Failed to generate audio for chunk {i+1}")
                        return False
                        
                except (RateLimitError, APIConnectionError, APITimeoutError, APIError) as e:
                    logger.error(f"OpenAI API error processing chunk {i+1}: {e}")
                    return False
            
            # Combine all temporary files into the final output
            success = self._combine_audio_files(temp_files, output_path)
            
            if success:
                # Verify final file
                if not os.path.exists(output_path):
                    logger.error(f"Final podcast file was not created at {output_path}")
                    return False
                    
                file_size = os.path.getsize(output_path)
                if file_size == 0:
                    logger.error(f"Final podcast file is empty: {output_path}")
                    return False
                    
                logger.info(f"Multi-chunk podcast generation completed. File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
                return True
            else:
                return False
                
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {temp_file}: {e}")
            
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
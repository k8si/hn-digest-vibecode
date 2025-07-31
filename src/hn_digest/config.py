"""Configuration management for HN Digest."""
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging configuration
def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('hn-digest.log'),
            logging.StreamHandler()
        ]
    )

# Configuration settings
class Config:
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT', 'ksilverstein@mozilla.com')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # HackerNews API settings
    HN_API_BASE_URL = 'https://hacker-news.firebaseio.com/v0'
    HN_TOP_STORIES_URL = f'{HN_API_BASE_URL}/topstories.json'
    HN_ITEM_URL = f'{HN_API_BASE_URL}/item'
    
    # Content filtering settings
    MAX_ARTICLES = 100
    PAGES_TO_SCAN = 2
    STORIES_PER_PAGE = 30
    
    # Rate limiting
    REQUEST_DELAY = 0.1  # seconds between requests
    
    # AI keywords for filtering
    AI_KEYWORDS = [
        'ai', 'artificial intelligence', 'machine learning', 'ml', 'neural', 
        'deep learning', 'gpt', 'llm', 'large language model', 'openai', 
        'anthropic', 'claude', 'chatgpt', 'transformer', 'bert', 'nlp',
        'natural language processing', 'computer vision', 'reinforcement learning',
        'supervised learning', 'unsupervised learning', 'automation', 'robot',
        'algorithm', 'data science', 'tensorflow', 'pytorch', 'keras',
        'generative', 'diffusion', 'stable diffusion', 'midjourney', 'dall-e'
    ]
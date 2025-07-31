"""Data models for HN Digest application."""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class HNStory:
    """HackerNews story data model."""
    id: int
    title: str
    url: str
    score: int
    by: str
    time: int
    descendants: int
    ai_score: Optional[int] = None
    matched_keywords: Optional[List[str]] = None
    combined_score: Optional[int] = None

@dataclass  
class ArticleContent:
    """Article content after scraping."""
    url: str
    content: Optional[str]
    mime_type: Optional[str]
    title: Optional[str] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class DigestEmail:
    """Email digest data model."""
    recipient: str
    subject: str
    text_content: str
    story_count: int
    generation_time: str
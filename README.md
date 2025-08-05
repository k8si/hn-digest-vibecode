# HackerNews AI Digest

My first vibe-coded project. I used Claude Code with Sonnet 4 for everything.

A Python application that scans HackerNews for AI-related content, scrapes article details, generates AI-powered summaries, and ~~delivers them via email as a daily digest~~. (Email delivery does not work at the moment.)

## Overview

This application automates the process of staying up-to-date with AI-related content on HackerNews by:

1. **Fetching and Filtering**: Retrieves top stories from HackerNews API and filters for AI-related content based on keywords and scoring
2. **Content Scraping**: Extracts full article content from linked URLs using web scraping techniques
3. **AI Summarization**: Generates concise summaries of articles using Anthropic's Claude API
4. **Email Delivery**: Formats and sends daily digest emails with summaries and links

## Features

- Smart AI content detection using keyword matching and scoring algorithms
- Robust web scraping with fallback handling for inaccessible content
- AI-powered article summarization with fallback for failures
- Email delivery with HTML formatting and detailed statistics
- Multiple operation modes (scan-only, full digest, email delivery)
- Comprehensive logging and error handling
- Dry-run mode for testing email content without sending

## Installation

### Prerequisites

- Python 3.11 or higher
- pip or uv package manager

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd hn-digest
   ```

2. Install dependencies:
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Or using uv (recommended)
   uv sync
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

### Environment Configuration

Create a `.env` file in the root directory with the following variables:

```env

# Required for AI summarization (full and email modes)
ANTHROPIC_API_KEY=your_anthropic_api_key

```

## Usage

The application supports three operation modes:

### Scan Mode (Default)
Scans HackerNews and shows AI-related stories without processing them:
```bash
python -m src.hn_digest.main --mode scan
```

### Full Digest Mode
Generates complete digest with AI summaries and prints to console:
```bash
python -m src.hn_digest.main --mode full
```

### Email Mode

NOTE: EMAIL MODE DOES NOT YET WORK

Generates digest and sends via email:
```bash
python -m src.hn_digest.main --mode email
```

### Additional Options

- `--debug`: Enable debug logging
- `--dry-run`: Show email content without sending (email mode only)

Example with options:
```bash
python -m src.hn_digest.main --mode email --dry-run --debug
```

## Running Tests

The project uses pytest for testing. Run tests with:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_integration.py

# Run with coverage
pytest --cov=src/hn_digest
```

### Test Structure

- `tests/test_*.py`: Unit tests for individual components
- `tests/test_integration.py`: Integration tests for complete workflows
- Tests use mocking to avoid external API calls during testing

## Project Structure

```
hn-digest/
├── src/hn_digest/           # Main application package
│   ├── main.py              # CLI interface and main application logic
│   ├── config.py            # Configuration and environment handling
│   ├── hn_client.py         # HackerNews API client
│   ├── content_filter.py    # AI content filtering and scoring
│   ├── article_scraper.py   # Web scraping for article content
│   ├── ai_summarizer.py     # AI-powered article summarization
│   ├── email_formatter.py   # HTML email formatting
│   └── email_sender.py      # Email delivery via SendGrid
├── tests/                   # Test suite
├── scripts/                 # Deployment and automation scripts
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## Dependencies

- **requests**: HTTP client for API calls and web scraping
- **beautifulsoup4**: HTML parsing for content extraction
- **anthropic**: Claude API client for AI summarization
- **sendgrid**: Email delivery service
- **python-dotenv**: Environment variable management
- **pytest**: Testing framework
- **pytest-mock**: Mocking utilities for tests

## License

This project is licensed under the MIT License.
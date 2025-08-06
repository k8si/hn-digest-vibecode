# HackerNews AI Digest

My first vibe-coded project. I used Claude Code with Sonnet 4 for everything.

A Python application that scans HackerNews for AI-related content, scrapes article details, generates AI-powered summaries, then sends the digest to OpenAI TTS to create a podcast. 

I tried to also have the system deliver a daily digest email but I haven't been able to get email to work yet.

## Quickstart

```bash
   git clone <repository-url>
   cd hn-digest
   uv sync
   export ANTHROPIC_API_KEY=your_anthropic_api_key
   export OPENAI_API_KEY=your_openai_api_key # for podcast generation
   uv run python -m src.hn_digest.main --mode full --podcast
```

This should create two files: `digest_<timestamp>.txt` and `digest_<timestamp>.mp3` in the current directory, containing the digest text and audio podcast respectively.

## Overview

This application automates the process of staying up-to-date with AI-related content on HackerNews by:

1. **Fetching and Filtering**: Retrieves top stories from HackerNews API and filters for AI-related content based on keywords and scoring
2. **Content Scraping**: Extracts full article content from linked URLs using web scraping techniques
3. **AI Summarization**: Generates concise summaries of articles using Anthropic's Claude API
4. **Podcast Generation**: Converts digest text to audio using OpenAI's Text-to-Speech API
5. ~~**Email Delivery**: Formats and sends daily digest emails with summaries and links~~ (DOES NOT WORK YET) 

Initial prompt: "I would like to build an app that combs through the first few pages of HackerNews, selects links and articles related to AI, summarizes the content of each, then compiles them into a concise digest. Then, I would like the app to email this digest. I would like to run this process every afternoon so I can read a summary of all the AI-related highlights that happened during the day."

## Features

- Smart AI content detection using keyword matching and scoring algorithms
- Robust web scraping with fallback handling for inaccessible content
- AI-powered article summarization with fallback for failures
- Text-to-speech podcast generation with configurable voices
- ~~Email delivery with HTML formatting and detailed statistics~~ (DOES NOT WORK YET)
- Multiple operation modes (scan-only, full digest, email delivery)
- Comprehensive logging and error handling
- Dry-run mode for testing email content without sending

## Installation

### Prerequisites

- Python 3.11 or higher
- uv package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd hn-digest
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

### Environment Configuration

Create a `.env` file in the root directory with the following variables:

```env

# Required for AI summarization (full and email modes)
ANTHROPIC_API_KEY=your_anthropic_api_key

# Required for podcast generation (when using --podcast flag)
OPENAI_API_KEY=your_openai_api_key

```

## Usage

The application supports three operation modes:

### Scan Mode (Default)
Scans HackerNews and shows AI-related stories without processing them:
```bash
uv run python -m src.hn_digest.main --mode scan
```

### Full Digest Mode
Generates complete digest with AI summaries and prints to console:
```bash
uv run python -m src.hn_digest.main --mode full
```

Add `--podcast` to also generate an audio version:
```bash
uv run python -m src.hn_digest.main --mode full --podcast
```

### Additional Options

- `--debug`: Enable debug logging
- `--dry-run`: Show email content without sending (email mode only)
- `--podcast`: Generate audio podcast from digest content (full and email modes)

Example with options:
```bash
uv run python -m src.hn_digest.main --mode email --dry-run --debug --podcast
```

## Running Tests

The project uses pytest for testing. Run tests with:

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_integration.py

# Run with coverage
uv run pytest --cov=src/hn_digest
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
│   ├── podcast_generator.py # Text-to-speech podcast generation
│   ├── email_formatter.py   # HTML email formatting
│   └── email_sender.py      # Email delivery via Google SMTP (DOES NOT WORK ATM)
├── tests/                   # Test suite
├── scripts/                 # Deployment and automation scripts
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## License

This project is licensed under the MIT License.
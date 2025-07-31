# HackerNews AI Digest App Specification

## Overview
A Python application that automatically scans HackerNews for AI-related content, generates summaries, and emails a daily digest.

## Core Functionality

### Content Discovery
- Scan the first 2 pages of HackerNews
- Filter posts for AI-related content using:
  - Keyword matching in titles
  - Content analysis of linked articles
  - Err on the side of being overly inclusive
- Prioritize articles by HackerNews score
- Include maximum of 100 articles per digest

### Content Processing
- Generate 1-2 paragraph summaries for each article
- Provide balanced, factual overview of content
- Include supporting quotes from source material where appropriate
- Include source link at the end of each summary

### Email Delivery
- Recipient: ksilverstein@mozilla.com
- Subject: "Kate's Daily AI Digest - [Date]"
- Email service: SendGrid integration
- Delivery time: 4 PM EST daily via cron job

## Error Handling
- **HackerNews down**: Send digest with message "Oh no! HackerNews is down"
- **Article scraping fails**: Include "Article could not be scraped: [article link]" instead of summary
- **Email send fails**: Log error and continue

## Technical Requirements

### Language & Framework
- Python
- Libraries: requests, BeautifulSoup (or similar for web scraping)
- SendGrid API for email delivery

### Scheduling
- Cron job for daily execution at 4 PM EST

### Production Readiness
- Prototype-level code quality
- Basic error handling as specified above
- Simple logging for debugging

## Testing Requirements
- Basic unit tests for core functions:
  - AI content filtering logic
  - Article summarization
  - Email formatting
- Integration tests:
  - End-to-end flow from HackerNews scraping to email delivery
  - Error scenarios (network failures, parsing errors)

## Success Criteria
- Successfully identifies AI-related content from HackerNews
- Generates readable, informative summaries
- Delivers daily digest email reliably
- Handles common failure scenarios gracefully
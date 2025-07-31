# HackerNews AI Digest App - Development Plan

## Project Summary

This project builds a Python application that automatically scans HackerNews for AI-related content, generates summaries using AI, and emails a daily digest to ksilverstein@mozilla.com at 4 PM EST. See `spec.md` for complete requirements.

### Key Goals
- Scan first 2 pages of HackerNews for AI-related posts
- Generate 1-2 paragraph summaries for up to 100 articles
- Send daily digest via SendGrid at 4 PM EST
- Handle common failure scenarios gracefully

### Keep in Mind
- Be overly inclusive when filtering AI content - false positives are better than false negatives
- Article scraping may fail frequently due to paywalls, different site structures, or anti-scraping measures
- Need to handle rate limiting from both HackerNews API and article sources
- Email delivery must be reliable - consider retry mechanisms
- Cron job timing needs to account for EST timezone regardless of server location

---

## Phase 1: Core Infrastructure and HackerNews Integration

### Summary
Establish the foundational application structure, implement HackerNews data fetching, and create AI content filtering logic.

### Phase Relationships
- **Builds on**: Nothing (initial phase)
- **Enables**: Phase 2 (content processing) by providing filtered HackerNews posts

### Success Criteria
- Application can fetch first 2 pages of HackerNews posts
- AI content filtering accurately identifies relevant posts (tested manually)
- Basic application structure supports configuration and logging
- Unit tests pass for filtering logic

### Keep in Mind
- HackerNews API has rate limits - implement respectful request patterns
- Filtering should be generous to avoid missing relevant content
- Consider using HackerNews Firebase API for better reliability than screen scraping
- Store intermediate results to enable debugging and manual verification

### Steps

1. **Set up project structure**
   - Create Python project with standard directory layout (`src/`, `tests/`, `requirements.txt`)
   - Initialize virtual environment and basic dependencies
   - Set up logging configuration for debugging

2. **Implement HackerNews API client**
   - Create `hn_client.py` to interface with HackerNews Firebase API
   - Implement functions to fetch top stories and story details
   - Add rate limiting and error handling for API requests
   - Focus on first 2 pages (roughly first 60 stories)

3. **Create AI content filtering system**
   - Implement `content_filter.py` with keyword-based filtering
   - Define comprehensive AI-related keywords list (AI, machine learning, neural, GPT, etc.)
   - Add scoring system that prioritizes HackerNews score
   - Include title and URL analysis for filtering decisions

4. **Build core application framework**
   - Create `main.py` with basic application structure
   - Implement configuration management for API keys and settings
   - Add command-line interface for testing different modes
   - Create data models for posts and filtered results

5. **Write unit tests for filtering logic**
   - Test keyword matching with various AI-related titles
   - Test scoring and prioritization logic
   - Test edge cases (empty titles, special characters, etc.)
   - Verify maximum 100 articles limit is enforced

6. **Integration testing of HackerNews flow**
   - Test complete flow from API fetch to filtered results
   - Verify handling of API failures and malformed data
   - Test with live HackerNews data and manually verify AI relevance
   - Document any filtering adjustments needed

---

## Phase 2: Article Content Scraping and Summarization

### Summary
Implement web scraping for article content and AI-powered summarization to create digestible summaries of each filtered post.

### Phase Relationships
- **Builds on**: Phase 1 (filtered HackerNews posts)
- **Enables**: Phase 3 (email delivery) by providing formatted summaries

### Success Criteria
- Can scrape article content from variety of news sites and blogs
- Generates coherent 1-2 paragraph summaries
- Handles scraping failures gracefully with fallback messages
- Integration tests validate end-to-end content processing

### Keep in Mind
- Many sites have anti-scraping measures or require JavaScript rendering
- Paywalls and login requirements will block content access
- Rate limiting is crucial to avoid being blocked by target sites
- AI summarization needs to be factual and balanced, avoiding hallucination
- Some HackerNews posts link to PDFs, GitHub repos, or other non-article content

### Steps

1. **Implement article scraping system**
   - Create `article_scraper.py` using requests and BeautifulSoup
   - Handle common article formats (news sites, blogs, GitHub readmes)
   - Implement user-agent rotation and respectful delays
   - Add timeout and retry logic for unreliable sites

2. **Build content extraction logic**
   - Create heuristics to identify main article content vs navigation/ads
   - Handle different HTML structures across various sites
   - Extract key metadata (title, publication date, author if available)
   - Implement fallback to HackerNews post title/description when scraping fails

3. **Integrate AI summarization**
   - Set up OpenAI API or similar for text summarization
   - Create prompts that generate 1-2 paragraph factual summaries
   - Include instruction to incorporate supporting quotes where appropriate
   - Add fallback handling when AI service is unavailable

4. **Create summary formatting system**
   - Format summaries with consistent structure
   - Include source links at end of each summary
   - Handle edge cases (very short articles, non-English content)
   - Add "Article could not be scraped" messages for failures

5. **Write comprehensive tests**
   - Unit tests for content extraction from sample HTML
   - Mock tests for AI summarization functionality
   - Integration tests with real article URLs (small sample)
   - Test error handling for various failure scenarios

6. **End-to-end validation**
   - Test complete pipeline from HackerNews posts to final summaries
   - Manually review summary quality and accuracy
   - Verify error messages appear correctly for failed scrapes
   - Confirm 100-article limit still enforced after processing

---

## Phase 3: Email Delivery and Scheduling

### Summary
Implement email formatting, SendGrid integration, and cron job scheduling to deliver the daily digest reliably at 4 PM EST.

### Phase Relationships
- **Builds on**: Phase 2 (article summaries)
- **Enables**: Production deployment with automated daily execution

### Success Criteria
- Emails are properly formatted with all summaries
- SendGrid integration sends emails reliably
- Cron job executes at correct time in EST timezone
- Error scenarios produce appropriate fallback emails

### Keep in Mind
- Email formatting must be readable in various email clients
- SendGrid API keys need secure storage and rotation capability
- Cron job timezone handling is critical - server may be in different timezone
- Large emails may hit size limits or spam filters
- Need monitoring to detect when daily emails fail to send

### Steps

1. **Create email formatting system**
   - Build `email_formatter.py` to create HTML and plain text versions
   - Design clean, readable layout for multiple article summaries
   - Include proper subject line with date: "Kate's Daily AI Digest - [Date]"
   - Add header/footer with summary count and generation timestamp

2. **Implement SendGrid integration**
   - Set up SendGrid API client with proper authentication
   - Create `email_sender.py` with retry logic for failed sends
   - Handle SendGrid-specific errors (rate limits, authentication, etc.)
   - Add email validation and recipient management

3. **Build error handling email scenarios**
   - Create fallback email for "HackerNews is down" scenario
   - Format emails with mixed successful/failed article scrapes
   - Include error summary at top when issues occur
   - Ensure email is sent even when most content processing fails

4. **Create scheduling and deployment system**
   - Write deployment scripts for production environment
   - Create cron job configuration for 4 PM EST daily execution
   - Add environment variable management for API keys
   - Include logging that enables monitoring of daily runs

5. **Write email and scheduling tests**
   - Unit tests for email formatting with various content scenarios
   - Mock tests for SendGrid API integration
   - Test timezone handling for cron scheduling
   - Integration test that sends actual test emails

6. **End-to-end production validation**
   - Deploy to production environment and test manual execution
   - Verify cron job runs at correct time
   - Send test digest and verify email formatting in target email client
   - Monitor first few automated runs and adjust as needed

---

## Phase 4: Production Hardening and Monitoring

### Summary
Add robust error handling, logging, monitoring, and operational features needed for reliable daily production use.

### Phase Relationships
- **Builds on**: Phase 3 (complete working system)
- **Enables**: Long-term reliable operation with minimal maintenance

### Success Criteria
- Comprehensive logging enables debugging of any issues
- Application handles all specified error scenarios gracefully
- Monitoring alerts when daily digest fails to send
- Performance is adequate for daily execution (completes within reasonable time)

### Keep in Mind
- Production issues often involve combinations of failures not tested individually
- Logging must balance detail with storage/privacy concerns
- Rate limiting becomes more important with daily automated execution
- Need operational runbooks for common troubleshooting scenarios

### Steps

1. **Enhance error handling and resilience**
   - Add comprehensive try-catch blocks around all external API calls
   - Implement exponential backoff for transient failures
   - Create circuit breaker pattern for repeatedly failing article sources
   - Add graceful degradation when AI services are unavailable

2. **Implement comprehensive logging**
   - Add structured logging with appropriate levels (INFO, WARN, ERROR)
   - Log key metrics (articles processed, success rates, execution time)
   - Include correlation IDs to trace individual article processing
   - Ensure sensitive data (API keys) never appears in logs

3. **Create monitoring and alerting**
   - Add health check endpoint for monitoring systems
   - Create metrics for daily digest success/failure
   - Set up alerts for consecutive daily failures
   - Log execution time and performance metrics

4. **Add operational tooling**
   - Create manual trigger script for testing and emergency sends
   - Add dry-run mode for testing without sending emails
   - Include configuration validation on startup
   - Create simple admin interface for adjusting filter keywords

5. **Write comprehensive integration tests**
   - Test complete system with mocked external dependencies
   - Test all error scenarios specified in requirements
   - Load test with large numbers of articles
   - Test recovery from various failure modes

6. **Production deployment and validation**
   - Deploy final version to production environment
   - Run several manual executions to validate all functionality
   - Monitor first week of automated execution closely
   - Document operational procedures and troubleshooting guides

---

## Phase 5: Documentation and Handoff

### Summary
Create comprehensive documentation for operation, maintenance, and potential future enhancements of the digest system.

### Phase Relationships
- **Builds on**: Phase 4 (production-ready system)
- **Enables**: Long-term maintenance and potential feature additions

### Success Criteria
- Complete README with setup and operation instructions
- API documentation for all major components
- Troubleshooting guide for common operational issues
- Architecture documentation for future developers

### Keep in Mind
- Documentation should enable someone else to operate and maintain the system
- Include specific examples of error scenarios and their resolutions
- Document all configuration options and their impacts
- Consider automated documentation generation where possible

### Steps

1. **Create comprehensive README**
   - Installation and setup instructions
   - Configuration options and environment variables
   - Manual execution instructions for testing
   - Cron job setup and timezone considerations

2. **Document API and architecture**
   - Code documentation for all major functions and classes
   - Architecture overview with data flow diagrams
   - Configuration management and secret handling
   - Integration points with external services

3. **Create operational runbooks**
   - Troubleshooting guide for common failure scenarios
   - Instructions for adjusting filtering keywords
   - SendGrid account management and API key rotation
   - Monitoring and alerting setup instructions

4. **Add inline code documentation**
   - Comprehensive docstrings for all public functions
   - Type hints throughout the codebase
   - Comments explaining complex filtering and processing logic
   - Examples of expected data structures

5. **Final testing and validation**
   - Verify all documentation by following setup instructions from scratch
   - Test troubleshooting procedures with simulated failures
   - Validate that monitoring and alerting work as documented
   - Confirm system can be operated based solely on documentation
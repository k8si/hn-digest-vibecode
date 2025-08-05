# Podcast Generation Feature Spec

## Overview
Add text-to-speech capability to convert HackerNews AI digest text into audio podcasts using OpenAI's TTS API.

## Requirements

### Core Functionality
- Convert existing text digests to audio podcasts using OpenAI TTS
- Single narrator format (no conversational elements)
- Generate podcasts on-demand via `--podcast` flag during digest generation
- Always generate and persist text digest, podcast generation is optional

### Technical Implementation
- **TTS Service**: OpenAI TTS API
- **Voice**: Configurable voice selection, default to "fable"
- **Audio Format**: MP3
- **File Storage**: Store alongside text digest files with same filename but `.mp3` extension

### Workflow Integration
- Add `--podcast` flag to digest generation command
- When flag is present: generate text digest → convert to audio podcast
- When flag is absent: only generate text digest (current behavior)

### Error Handling
- If podcast generation fails: log error but continue, leaving text digest intact
- Do not fail entire digest generation process due to TTS failures
- Provide adequate error logging for debugging

### User Feedback
- Display progress message when podcast generation starts
- Display completion message with file size information when finished
- Log file size details for generated podcast files

### Configuration
- Configurable OpenAI TTS voice selection (default: "fable")
- Keep configuration simple for prototype - no additional audio settings

### Testing Requirements
- **Unit Tests**: Mock OpenAI API calls to test internal functionality
- **Integration Tests**: End-to-end test that actually calls OpenAI API
- Update `.env` files with required OpenAI API key configuration
- Test audio file generation and validation

### Production Readiness
- **Level**: Prototype/proof-of-concept
- **Polish**: Basic functionality with adequate error logging
- **Scope**: Not production-ready, focus on core functionality

### Dependencies
- OpenAI API key required for TTS functionality
- Update environment configuration files accordingly

## Success Criteria
- Can generate MP3 podcast from existing text digest
- Podcast files stored with correct naming convention
- Graceful error handling that doesn't break digest generation
- Clear user feedback during processing
- Comprehensive test coverage with both mocked and real API tests

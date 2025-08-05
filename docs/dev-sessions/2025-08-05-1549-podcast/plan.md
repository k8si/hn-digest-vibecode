# Implementation Plan: Podcast Generation Feature

## High Level Summary

This plan implements text-to-speech podcast generation for the HackerNews AI digest application. The feature adds an optional `--podcast` flag to the existing CLI that converts generated text digests into MP3 audio files using OpenAI's TTS API. The implementation integrates seamlessly with the existing digest generation pipeline, maintaining backward compatibility while adding new podcast capabilities.

**Spec Reference:** See `spec.md` for detailed requirements and success criteria.

### Keep in Mind (Plan Level)
- **Existing Architecture**: The codebase follows a modular pipeline pattern with clear separation of concerns - the podcast feature should follow these same patterns
- **Error Isolation**: Podcast generation failures must not break the core digest functionality 
- **Configuration Management**: Leverage existing Config class patterns for TTS settings
- **File Naming**: Follow existing backup file naming conventions (`digest_backup_YYYYMMDD_HHMMSS.txt` → `digest_YYYYMMDD_HHMMSS.mp3`)
- **Testing Philosophy**: Project uses comprehensive mocking for external APIs with integration tests - maintain this approach for OpenAI TTS

## Phase 1: Core TTS Infrastructure Setup

**Summary:** Establish the foundational text-to-speech infrastructure, configuration management, and basic podcast generation capability.

**Phase Relationships:** This phase creates the base components that Phase 2 will integrate into the CLI workflow. It provides isolated, testable TTS functionality.

**Success Criteria:**
- OpenAI TTS API integration working with proper authentication
- Configurable voice selection with "fable" as default
- Basic podcast generation from text to MP3 file
- Comprehensive unit tests with mocked API calls
- Integration test that validates real OpenAI API interaction

**Keep in Mind:**
- OpenAI TTS API has rate limits and text length restrictions
- MP3 file handling requires proper binary data management
- Configuration should extend existing patterns without breaking current functionality
- Error handling must be robust for network failures and API errors

### Steps:

1. **Add OpenAI dependency and environment configuration**
   - Add `openai` package to requirements.txt
   - Update `.env` files with `OPENAI_API_KEY` placeholder
   - Document required API key in project README/docs

2. **Create podcast generator module**
   - Create `src/hn_digest/podcast_generator.py`
   - Implement `PodcastGenerator` class with basic structure
   - Add initialization with OpenAI client setup

3. **Extend configuration management**
   - Update `src/hn_digest/config.py` to include podcast settings
   - Add `OPENAI_API_KEY`, `TTS_VOICE` (default: "fable"), `PODCAST_ENABLED` configs
   - Maintain existing configuration patterns and validation

4. **Implement core TTS functionality**
   - Add `generate_podcast()` method to convert text to MP3
   - Handle OpenAI TTS API calls with proper error handling
   - Implement file I/O for MP3 audio data
   - Add logging for progress and file size information

5. **Create comprehensive unit tests**
   - Create `tests/test_podcast_generator.py`
   - Mock OpenAI API responses for various scenarios (success, failure, timeout)
   - Test configuration loading and validation
   - Test error handling and logging behavior

6. **Create integration test**
   - Add integration test function that calls real OpenAI API
   - Test with actual API key (skip if not available)
   - Validate generated MP3 file is valid and playable
   - Include in existing integration test suite

## Phase 2: CLI Integration and Workflow Enhancement

**Summary:** Integrate podcast generation into the existing CLI and digest generation workflow, adding the `--podcast` flag and maintaining pipeline integrity.

**Phase Relationships:** Builds on Phase 1's TTS infrastructure to create the complete user-facing feature. Modifies existing workflow without breaking current functionality.

**Success Criteria:**
- `--podcast` flag successfully triggers podcast generation after digest creation
- Text digest generation remains unaffected when podcast generation fails
- Generated MP3 files are stored alongside text digests with correct naming
- User feedback shows progress and completion messages
- All existing tests continue to pass

**Keep in Mind:**
- CLI modification must maintain backward compatibility
- Pipeline integration should be non-intrusive to existing workflow
- File naming must align with existing digest backup conventions
- Error handling should isolate podcast failures from digest success

### Steps:

1. **Extend CLI argument parser**
   - Update `create_cli_parser()` in `main.py` to add `--podcast` flag
   - Add argument validation and help documentation
   - Ensure flag works with existing modes (scan/full/email)

2. **Modify digest generation workflow**
   - Update `HNDigestApp` class to accept podcast generation option
   - Add podcast generation step after successful digest creation
   - Ensure text digest is saved first, then podcast generation occurs

3. **Implement file storage integration**
   - Update file naming to use digest timestamp for podcast files
   - Store MP3 files in same directory as text digests
   - Handle file path generation consistently with existing patterns

4. **Add user feedback and logging**
   - Implement progress messages for TTS conversion
   - Add completion messages with file size information
   - Integrate with existing logging infrastructure
   - Ensure debug mode shows detailed podcast generation logs

5. **Create end-to-end tests**
   - Add test cases for `--podcast` flag in CLI parsing
   - Test complete workflow from digest generation to podcast creation
   - Test error scenarios where podcast fails but digest succeeds
   - Validate file naming and storage behavior

6. **Update project documentation**
   - Add `--podcast` flag to CLI help and usage examples
   - Document OpenAI API key requirement
   - Update README with podcast generation instructions

## Phase 3: Polish and Production Readiness

**Summary:** Add final touches, comprehensive error handling, and ensure the feature is ready for prototype usage with proper debugging capabilities.

**Phase Relationships:** Completes the implementation by hardening the feature for real-world usage. Builds on the working foundation from Phases 1 and 2.

**Success Criteria:**
- Robust error handling for all failure scenarios
- Comprehensive logging for debugging and monitoring
- Performance optimization for large text inputs
- Complete test coverage including edge cases
- Feature is ready for prototype deployment

**Keep in Mind:**
- This is prototype-level polish, not production-ready
- Focus on debugging capabilities and error visibility
- Performance should be reasonable but not optimized for scale
- Test coverage should be comprehensive but not exhaustive

### Steps:

1. **Enhance error handling and recovery**
   - Add retry logic for transient API failures
   - Implement graceful degradation for network issues
   - Add validation for text length limits and API constraints
   - Ensure all errors are properly logged with context

2. **Optimize performance and resource usage**
   - Add text chunking for large digest content
   - Implement basic rate limiting respect for OpenAI API
   - Add file cleanup for failed podcast generations
   - Optimize memory usage for large audio files

3. **Expand test coverage for edge cases**
   - Test with very long text inputs
   - Test with empty or malformed digest content
   - Test API rate limiting scenarios
   - Test file system errors (permissions, disk space)

4. **Add monitoring and debugging features**
   - Add detailed timing information for TTS operations
   - Include audio quality metrics in logs
   - Add configuration validation at startup
   - Implement health check for OpenAI API connectivity

5. **Final integration and validation**
   - Run full end-to-end tests with real digest generation
   - Validate podcast quality with sample digest content
   - Test all CLI combinations and modes
   - Ensure no regressions in existing functionality

6. **Prepare for deployment**
   - Update environment configuration templates
   - Document troubleshooting steps for common issues
   - Create example usage scenarios and test cases
   - Ensure all dependencies are properly specified
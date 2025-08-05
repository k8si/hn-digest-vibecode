#!/bin/bash

# Daily HackerNews AI Digest Script
# This script is designed to be run by cron at 4 PM EST daily

source .env

# Set up environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/daily_digest.log"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to rotate log files (keep last 30 days)
rotate_logs() {
    if [ -f "$LOG_FILE" ]; then
        # If log file is larger than 10MB, rotate it
        if [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt 10485760 ]; then
            mv "$LOG_FILE" "${LOG_FILE}.$(date +%Y%m%d_%H%M%S)"
            # Keep only last 10 rotated logs
            find "$PROJECT_DIR" -name "daily_digest.log.*" -type f -mtime +10 -delete
        fi
    fi
}

# Main execution
main() {
    log "=== Starting daily HackerNews AI digest generation ==="
    
    # Rotate logs if needed
    rotate_logs
    
    # Change to project directory
    cd "$PROJECT_DIR" || {
        log "ERROR: Could not change to project directory: $PROJECT_DIR"
        exit 1
    }
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        log "ERROR: Virtual environment not found. Run setup first."
        exit 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate || {
        log "ERROR: Could not activate virtual environment"
        exit 1
    }
    
    # Verify required environment variables
    if [ -z "$SENDGRID_API_KEY" ]; then
        log "ERROR: SENDGRID_API_KEY environment variable not set"
        exit 1
    fi
    
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        log "ERROR: ANTHROPIC_API_KEY environment variable not set"
        exit 1
    fi
    
    # Run the digest generation
    log "Starting digest generation..."
    
    # Run with timeout to prevent hanging
    timeout 1800 python -m src.hn_digest.main --mode email 2>&1 | while read line; do
        log "$line"
    done
    
    EXIT_CODE=${PIPESTATUS[0]}
    
    if [ $EXIT_CODE -eq 0 ]; then
        log "SUCCESS: Daily digest completed successfully"
    elif [ $EXIT_CODE -eq 124 ]; then
        log "ERROR: Digest generation timed out after 30 minutes"
        exit 1
    else
        log "ERROR: Digest generation failed with exit code $EXIT_CODE"
        exit 1
    fi
    
    log "=== Daily digest generation completed ==="
}

# Handle script interruption
trap 'log "Script interrupted"; exit 130' INT TERM

# Run main function
main "$@"
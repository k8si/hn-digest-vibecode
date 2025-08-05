#!/bin/bash

# Setup script for HackerNews AI Digest cron job
# This script configures the cron job to run daily at 4 PM EST

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DAILY_SCRIPT="$SCRIPT_DIR/daily_digest.sh"

echo "Setting up HackerNews AI Digest cron job..."

# Check if daily script exists
if [ ! -f "$DAILY_SCRIPT" ]; then
    echo "ERROR: Daily digest script not found at $DAILY_SCRIPT"
    exit 1
fi

# Make sure the script is executable
chmod +x "$DAILY_SCRIPT"

# Create environment file for cron (cron has limited environment)
ENV_FILE="$PROJECT_DIR/.env.cron"

echo "Creating environment file for cron at $ENV_FILE"
cat > "$ENV_FILE" << EOF
# Environment variables for HackerNews AI Digest cron job
# This file is sourced by the cron job to set up the environment

# Python path
PYTHONPATH="$PROJECT_DIR:\$PYTHONPATH"

# Add project's virtual environment to PATH
PATH="$PROJECT_DIR/venv/bin:\$PATH"

# API Keys (you need to set these manually)
# SENDGRID_API_KEY=your_sendgrid_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Email configuration
EMAIL_RECIPIENT=ksilverstein@mozilla.com
USERNAME=Kate

# Optional: Anthropic model (defaults to claude-3-haiku-20240307)
# ANTHROPIC_MODEL=claude-3-haiku-20240307
EOF

# Update daily script to source environment
cat > "$DAILY_SCRIPT.tmp" << 'EOF'
#!/bin/bash

# Daily HackerNews AI Digest Script
# This script is designed to be run by cron at 4 PM EST daily

# Set up environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_DIR/daily_digest.log"
ENV_FILE="$PROJECT_DIR/.env.cron"

# Source environment variables if file exists
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

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
EOF

mv "$DAILY_SCRIPT.tmp" "$DAILY_SCRIPT"
chmod +x "$DAILY_SCRIPT"

# Create the cron job entry
# Note: 4 PM EST = 21:00 UTC (during standard time) or 20:00 UTC (during daylight time)
# We'll use 21:00 UTC and let the user adjust if needed
CRON_ENTRY="0 21 * * * $DAILY_SCRIPT"

echo ""
echo "Cron job configuration:"
echo "========================"
echo "$CRON_ENTRY"
echo ""
echo "To install this cron job, run:"
echo "  echo '$CRON_ENTRY' | crontab -"
echo ""
echo "Or manually add it by running 'crontab -e' and adding the line above."
echo ""
echo "IMPORTANT SETUP STEPS:"
echo "1. Edit $ENV_FILE and add your API keys"
echo "2. Verify the timezone - this is set for 4 PM EST (21:00 UTC standard time)"
echo "   - During daylight saving time, you may need to adjust to 20:00 UTC"
echo "3. Test the setup by running: $DAILY_SCRIPT"
echo "4. Install the cron job as shown above"
echo ""
echo "To view current cron jobs: crontab -l"
echo "To remove the cron job: crontab -e (then delete the line)"
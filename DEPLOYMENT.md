# HackerNews AI Digest - Deployment Guide

This guide covers deploying the HackerNews AI Digest application for daily automated execution.

## Prerequisites

- Python 3.8 or higher
- SendGrid account and API key
- Anthropic API key
- Unix-like system with cron support (Linux, macOS)

## Installation Steps

### 1. Clone and Setup Project

```bash
# Clone the repository (or copy the project files)
cd /path/to/your/deployment/location

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# API Keys (required)
SENDGRID_API_KEY=your_sendgrid_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Email configuration
EMAIL_RECIPIENT=ksilverstein@mozilla.com
USERNAME=Kate

# Optional: AI model selection (defaults to claude-3-haiku-20240307)
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

**Security Note**: Keep your `.env` file secure and never commit it to version control.

### 3. Test the Application

Test each mode to ensure everything works:

```bash
# Test story scanning only
python -m src.hn_digest.main --mode scan

# Test full digest generation (no email)
python -m src.hn_digest.main --mode full

# Test email functionality (dry run)
python -m src.hn_digest.main --mode email --dry-run

# Test actual email sending
python -m src.hn_digest.main --mode email
```

### 4. Set Up Automated Scheduling

Run the cron setup script:

```bash
./scripts/setup_cron.sh
```

This will:
- Create an environment file for cron (`/.env.cron`)
- Display the cron job configuration
- Provide installation instructions

**Manual cron setup:**

1. Edit the cron environment file:
   ```bash
   nano .env.cron
   # Add your API keys to this file
   ```

2. Install the cron job:
   ```bash
   # Add the cron job (runs daily at 4 PM EST / 9 PM UTC)
   echo "0 21 * * * /path/to/project/scripts/daily_digest.sh" | crontab -
   ```

3. Verify cron job installation:
   ```bash
   crontab -l
   ```

## Configuration Options

### Email Settings

- `EMAIL_RECIPIENT`: Email address to receive the digest
- `USERNAME`: Name to personalize the digest (appears in subject and content)
- `SENDGRID_API_KEY`: Your SendGrid API key for email delivery

### AI Settings

- `ANTHROPIC_API_KEY`: Your Anthropic API key for content summarization
- `ANTHROPIC_MODEL`: AI model to use (default: claude-3-haiku-20240307)

### Timing Settings

The default cron job runs at 4 PM EST (21:00 UTC). To adjust the time:

1. Edit the cron job: `crontab -e`
2. Modify the time in the cron expression: `MINUTE HOUR * * *`
3. Consider daylight saving time adjustments

**Timezone Examples:**
- 4 PM EST (Standard Time): `0 21 * * *`
- 4 PM EDT (Daylight Time): `0 20 * * *`
- 3 PM PST: `0 23 * * *`

## Monitoring and Maintenance

### Log Files

- `daily_digest.log`: Main application log with timestamp entries
- `digest_backup_*.txt`: Backup files when email delivery fails
- `digest_error_*.txt`: Error logs for critical failures

### Log Rotation

Logs are automatically rotated when they exceed 10MB. Old logs are kept for 10 days.

### Monitoring Email Delivery

The system provides several fallback mechanisms:

1. **Successful delivery**: Logged as "Digest email sent successfully"
2. **Email failure**: Content saved to `digest_backup_*.txt`
3. **Critical failure**: Fallback email sent or error saved to `digest_error_*.txt`

### Common Issues and Troubleshooting

**Cron job not running:**
- Check cron service: `sudo service cron status` (Linux) or `sudo launchctl list | grep cron` (macOS)
- Verify cron job exists: `crontab -l`
- Check system logs: `/var/log/cron` or `/var/log/system.log`

**Email not sending:**
- Verify SendGrid API key is valid
- Check `daily_digest.log` for error messages
- Test manually: `python -m src.hn_digest.main --mode email --dry-run`

**No stories found:**
- HackerNews may have no AI-related content that day
- Check if HackerNews API is accessible
- Review AI keywords in `src/hn_digest/config.py`

**Script permissions:**
```bash
chmod +x scripts/daily_digest.sh
chmod +x scripts/setup_cron.sh
```

## Security Considerations

1. **API Keys**: Store in environment variables, never in code
2. **File Permissions**: Ensure log files and scripts have appropriate permissions
3. **Network Access**: Application requires outbound HTTPS access
4. **Log Content**: Logs may contain URLs and titles but no sensitive content

## Maintenance Tasks

### Weekly
- Check log files for errors
- Verify email delivery is working

### Monthly
- Review and clean old log files
- Check API key usage/limits
- Update dependencies if needed

### As Needed
- Adjust AI keywords for better filtering
- Update cron timing for seasonal timezone changes
- Rotate API keys

## Uninstalling

To remove the scheduled digest:

```bash
# Remove cron job
crontab -e  # Delete the digest line

# Or remove all cron jobs for the user
crontab -r

# Clean up files
rm -rf /path/to/project
```

## Support

For issues or questions:
1. Check the application logs first
2. Test components individually (scan, full, email modes)
3. Verify all configuration settings
4. Check network connectivity and API access
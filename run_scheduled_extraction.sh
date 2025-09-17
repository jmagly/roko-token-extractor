#!/bin/bash

# ROKO Token Extractor Scheduled Job Script
# Runs every 15 minutes via cron
# Outputs to production directory and creates timestamped archive

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"
OUTPUT_DIR="/home/roctinam/production-deploy/roko-token-extractor/public"
ARCHIVE_DIR="/home/roctinam/production-deploy/roko-token-extractor/data"
OUTPUT_FILE="roko-price.json"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/scheduled_extraction.log"

# Create directories if they don't exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$ARCHIVE_DIR"
mkdir -p "$LOG_DIR"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S UTC')] $1" | tee -a "$LOG_FILE"
}

# Start extraction
log_message "Starting scheduled ROKO token extraction"

# Change to script directory
cd "$SCRIPT_DIR"

# Activate virtual environment and run extraction
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"

    # Run the extraction script with output to public directory
    # Note: This can take 3-5 minutes due to RPC node response times
    log_message "Running token extractor (this may take 3-5 minutes)..."
    if timeout 360 python update_roko_data.py --output-dir "$OUTPUT_DIR" --filename "$OUTPUT_FILE" 2>&1 | tee -a "$LOG_FILE"; then

        # If extraction successful, create timestamped archive copy
        if [ -f "$OUTPUT_DIR/$OUTPUT_FILE" ]; then
            # Generate timestamp in UTC with milliseconds
            TIMESTAMP=$(date -u '+%Y_%m_%d_%H%M%S')
            MILLISECONDS=$(date +%3N)
            ARCHIVE_FILE="roko-price-${TIMESTAMP}${MILLISECONDS}.json"

            # Copy to archive directory with timestamp
            cp "$OUTPUT_DIR/$OUTPUT_FILE" "$ARCHIVE_DIR/$ARCHIVE_FILE"

            log_message "Successfully created archive: $ARCHIVE_FILE"
            log_message "Extraction completed successfully"

            # Clean up old archive files (optional - keep last 7 days)
            # find "$ARCHIVE_DIR" -name "roko-price-*.json" -mtime +7 -delete

        else
            log_message "ERROR: Output file not created at $OUTPUT_DIR/$OUTPUT_FILE"
            exit 1
        fi

    else
        log_message "ERROR: Token extraction failed"
        exit 1
    fi

    # Deactivate virtual environment
    deactivate
else
    log_message "ERROR: Virtual environment not found at $VENV_PATH"
    exit 1
fi

log_message "Scheduled extraction completed"
log_message "----------------------------------------"
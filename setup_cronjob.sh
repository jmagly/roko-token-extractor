#!/bin/bash
# Setup script for ROKO data update cronjob

echo "Setting up ROKO data update cronjob..."

# Get the current directory
CURRENT_DIR=$(pwd)
SCRIPT_PATH="$CURRENT_DIR/update_roko_data.py"

# Make the script executable
chmod +x "$SCRIPT_PATH"

# Create web_delivery directory
mkdir -p web_delivery

# Create logs directory
mkdir -p logs

echo "✅ Script setup complete"
echo "📁 Web delivery directory: $CURRENT_DIR/web_delivery"
echo "📁 Logs directory: $CURRENT_DIR/logs"
echo ""
echo "To add to crontab, run:"
echo "crontab -e"
echo ""
echo "Then add this line for hourly updates:"
echo "0 * * * * cd $CURRENT_DIR && python3 $SCRIPT_PATH >> logs/cron.log 2>&1"
echo ""
echo "Or for every 30 minutes:"
echo "*/30 * * * * cd $CURRENT_DIR && python3 $SCRIPT_PATH >> logs/cron.log 2>&1"
echo ""
echo "Or for every 15 minutes:"
echo "*/15 * * * * cd $CURRENT_DIR && python3 $SCRIPT_PATH >> logs/cron.log 2>&1"
echo ""
echo "Test the script manually first:"
echo "python3 $SCRIPT_PATH"

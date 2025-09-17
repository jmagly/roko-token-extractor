#!/bin/bash
# Setup script for RPC endpoint updates (weekly)

echo "Setting up RPC endpoint update cronjob..."

# Get the current directory
CURRENT_DIR=$(pwd)
SCRIPT_PATH="$CURRENT_DIR/update_rpc_endpoints.py"

# Make the script executable
chmod +x "$SCRIPT_PATH"

# Create logs directory
mkdir -p logs

echo "✅ RPC update script setup complete"
echo "📁 Logs directory: $CURRENT_DIR/logs"
echo ""
echo "To add to crontab, run:"
echo "crontab -e"
echo ""
echo "Then add this line for weekly RPC updates (every Sunday at 2 AM):"
echo "0 2 * * 0 cd $CURRENT_DIR && python3 $SCRIPT_PATH >> logs/rpc_cron.log 2>&1"
echo ""
echo "Or for daily updates (every day at 2 AM):"
echo "0 2 * * * cd $CURRENT_DIR && python3 $SCRIPT_PATH >> logs/rpc_cron.log 2>&1"
echo ""
echo "Test the script manually first:"
echo "python3 $SCRIPT_PATH"

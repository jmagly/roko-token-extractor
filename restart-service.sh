#!/bin/bash

echo "Restarting ROKO Token Web Server..."

# Stop the existing process
echo "Stopping existing process..."
pkill -f "serve_web.py" || echo "No existing process found"

# Give it a moment to stop
sleep 2

# Start the service again
echo "Starting service..."
cd /home/roctinam/production-deploy/roko-token-extractor
nohup python3 serve_web.py --port 8187 --directory /home/roctinam/production-deploy/roko-token-extractor/public > logs/serve_web.log 2>&1 &

echo "Service restarted. PID: $!"
echo "Logs: /home/roctinam/production-deploy/roko-token-extractor/logs/serve_web.log"

# Test the service
sleep 2
echo ""
echo "Testing service..."
echo "Direct access (old way): /price"
curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:8187/price

echo "With /token prefix (new way): /token/price"
curl -s -o /dev/null -w "  Status: %{http_code}\n" http://localhost:8187/token/price
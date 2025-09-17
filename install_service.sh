#!/bin/bash

# Script to install and start the ROKO web server as a systemd service
# Must be run with sudo

set -e

SERVICE_NAME="roko-webserver"
SERVICE_FILE="/home/roctinam/production-deploy/roko-token-extractor/roko-webserver.service"
SYSTEMD_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo:"
    echo "sudo $0"
    exit 1
fi

echo "Installing ROKO Web Server Service..."
echo "======================================="

# Copy service file to systemd directory
echo "1. Copying service file to systemd..."
cp "$SERVICE_FILE" "$SYSTEMD_PATH"

# Reload systemd daemon to recognize new service
echo "2. Reloading systemd daemon..."
systemctl daemon-reload

# Enable service to start on boot
echo "3. Enabling service for auto-start on boot..."
systemctl enable ${SERVICE_NAME}.service

# Start the service
echo "4. Starting the service..."
systemctl start ${SERVICE_NAME}.service

# Check service status
echo "5. Checking service status..."
systemctl status ${SERVICE_NAME}.service --no-pager

echo ""
echo "======================================="
echo "Service installation completed!"
echo ""
echo "Useful commands:"
echo "  Check status:  sudo systemctl status ${SERVICE_NAME}"
echo "  Stop service:  sudo systemctl stop ${SERVICE_NAME}"
echo "  Start service: sudo systemctl start ${SERVICE_NAME}"
echo "  Restart:       sudo systemctl restart ${SERVICE_NAME}"
echo "  View logs:     sudo journalctl -u ${SERVICE_NAME} -f"
echo "  Disable:       sudo systemctl disable ${SERVICE_NAME}"
echo ""
echo "Web server is running on: http://$(hostname -I | awk '{print $1}'):8187"
echo ""
echo "API Endpoints:"
echo "  Price data: http://$(hostname -I | awk '{print $1}'):8187/price"
echo "  Dashboard:  http://$(hostname -I | awk '{print $1}'):8187/"
echo ""
echo "For production (roko.matric.io):"
echo "  Price API: https://roko.matric.io/price"
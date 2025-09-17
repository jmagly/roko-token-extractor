# Production Deployment Guide

This guide covers the complete production deployment of the ROKO Token Extractor system, including data collection, web server, and monitoring.

## Overview

The production deployment consists of:
- **Data Collection**: Scheduled extraction every 15 minutes via cron
- **Web Server**: Python HTTP server with ETag caching on port 8187
- **API Endpoint**: Clean `/price` endpoint via symlink
- **Dashboard**: Web interface for monitoring token data
- **Service Management**: Systemd service for automatic startup and monitoring

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cron Job      │───→│  Data Extraction │───→│  JSON Files     │
│  (15 minutes)   │    │   (3-5 minutes)  │    │  public/        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Dashboard │←───│  Python Server   │←───│  Symlink        │
│  index.html     │    │  Port 8187       │    │  price → json   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Initial Setup

```bash
# Clone the repository
git clone https://github.com/your-username/roko-token-extractor.git
cd roko-token-extractor

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your configuration
```

### 2. Install Production System

```bash
# Install the systemd service
sudo ./install_service.sh

# Set up cron job for data extraction
crontab -e
# Add this line:
*/15 * * * * /home/roctinam/roko-token-extractor/run_scheduled_extraction.sh >> /home/roctinam/roko-token-extractor/logs/cron.log 2>&1
```

### 3. Verify Deployment

```bash
# Check service status
sudo systemctl status roko-webserver

# Test API endpoint
curl http://localhost:8187/price

# View logs
sudo journalctl -u roko-webserver -f
```

## Production Configuration

### File Structure

```
/home/roctinam/production-deploy/roko-token-extractor/
├── public/
│   ├── index.html          # Web dashboard
│   ├── roko-price.json     # Latest price data
│   └── price → roko-price.json  # Symlink for API
├── data/                   # Timestamped archives
├── logs/                   # Server and extraction logs
├── serve_web.py           # Web server with ETag support
├── roko-webserver.service # Systemd service definition
└── install_service.sh     # Service installation script
```

### Web Server (serve_web.py)

**Features:**
- **Port**: 8187
- **ETag Caching**: Based on JSON timestamp for efficient updates
- **CORS Headers**: Full cross-origin support
- **Cache Strategy**: 15-minute cache with must-revalidate
- **API Endpoint**: `/price` symlink for clean URLs
- **Logging**: Detailed request logging with cache status

**Configuration:**
```python
# Default settings
PORT = 8187
DIRECTORY = "/home/roctinam/production-deploy/roko-token-extractor/public"
CACHE_MAX_AGE = 900  # 15 minutes
```

### Systemd Service (roko-webserver.service)

**Service Configuration:**
- **User**: roctinam
- **Auto-restart**: Yes (10-second delay)
- **Security**: NoNewPrivileges, PrivateTmp, ProtectSystem
- **Logging**: Separate stdout/stderr logs

**Service Commands:**
```bash
sudo systemctl start roko-webserver      # Start service
sudo systemctl stop roko-webserver       # Stop service
sudo systemctl restart roko-webserver    # Restart service
sudo systemctl status roko-webserver     # Check status
sudo systemctl enable roko-webserver     # Enable auto-start
sudo systemctl disable roko-webserver    # Disable auto-start
```

### Data Extraction (run_scheduled_extraction.sh)

**Schedule**: Every 15 minutes via cron
**Duration**: 3-5 minutes per extraction
**Timeout**: 6 minutes (360 seconds)

**Cron Configuration:**
```bash
# Edit cron jobs
crontab -e

# Add this line for 15-minute intervals
*/15 * * * * /home/roctinam/roko-token-extractor/run_scheduled_extraction.sh >> /home/roctinam/roko-token-extractor/logs/cron.log 2>&1

# Alternative: 5-minute intervals (more frequent)
*/5 * * * * /home/roctinam/roko-token-extractor/run_scheduled_extraction.sh >> /home/roctinam/roko-token-extractor/logs/cron.log 2>&1
```

**Features:**
- Timestamped archive creation
- Comprehensive error handling
- Virtual environment management
- Detailed logging

## API Documentation

### Endpoints

#### GET /price
Returns the latest ROKO token pricing and metrics data.

**URL**: `http://your-server:8187/price`
**Method**: GET
**Cache**: 15 minutes with ETag support

**Response Example:**
```json
{
  "pricing": {
    "usd_per_token": "0.00001234",
    "eth_per_token": "0.000000005678",
    "market_cap_usd": "1234567.89",
    "token_eth_ratio": 175438.596,
    "eth_price_usd": "2456.78"
  },
  "tvl": {
    "total_tvl_usd": "987654.32",
    "pools_count": 15
  },
  "volume": {
    "volume_24h_usd": "12345.67",
    "volume_7d_usd": "86420.00"
  },
  "token": {
    "total_supply": "100000000000",
    "circulating_supply": "85000000000",
    "treasury_percentage": "15.0"
  },
  "last_updated": "2024-09-18 01:30:00 UTC",
  "timestamp": 1726621800
}
```

#### GET /
Web dashboard interface for monitoring token data.

**Features:**
- Real-time data display
- Cache status indicators
- Raw JSON viewer
- Integration examples

### ETag Caching

The API implements intelligent caching using ETags based on the JSON timestamp:

1. **ETag Generation**: MD5 hash of `{timestamp}-{file_size}`
2. **Cache Headers**: `Cache-Control: public, max-age=900, must-revalidate`
3. **304 Responses**: Returned when data hasn't changed
4. **Client Behavior**: Browsers automatically handle cache validation

**Example Requests:**
```bash
# First request - returns 200 with ETag
curl -v http://localhost:8187/price

# Subsequent request with ETag - returns 304 if unchanged
curl -v -H 'If-None-Match: "abc123def456"' http://localhost:8187/price
```

## Monitoring & Maintenance

### Log Files

**Web Server Logs:**
```bash
# Server access logs
tail -f /home/roctinam/production-deploy/roko-token-extractor/logs/webserver.log

# Server error logs
tail -f /home/roctinam/production-deploy/roko-token-extractor/logs/webserver_error.log

# Systemd service logs
sudo journalctl -u roko-webserver -f
```

**Data Extraction Logs:**
```bash
# Scheduled extraction logs
tail -f /home/roctinam/roko-token-extractor/logs/scheduled_extraction.log

# Cron execution logs
tail -f /home/roctinam/roko-token-extractor/logs/cron.log
```

### Health Checks

**Service Health:**
```bash
# Check if service is running
sudo systemctl is-active roko-webserver

# Check service details
sudo systemctl status roko-webserver --no-pager

# Test API availability
curl -f http://localhost:8187/price > /dev/null && echo "API OK" || echo "API FAILED"
```

**Data Freshness:**
```bash
# Check last update time
stat /home/roctinam/production-deploy/roko-token-extractor/public/roko-price.json

# Verify data is recent (less than 20 minutes old)
find /home/roctinam/production-deploy/roko-token-extractor/public -name "roko-price.json" -mmin -20
```

### Maintenance Tasks

**Archive Cleanup (Optional):**
```bash
# Remove archives older than 7 days
find /home/roctinam/production-deploy/roko-token-extractor/data -name "roko-price-*.json" -mtime +7 -delete

# Keep only last 100 archives
cd /home/roctinam/production-deploy/roko-token-extractor/data
ls -t roko-price-*.json | tail -n +101 | xargs rm -f
```

**Log Rotation:**
```bash
# Rotate large log files
cd /home/roctinam/production-deploy/roko-token-extractor/logs
for log in *.log; do
    if [ -f "$log" ] && [ $(stat -f%z "$log" 2>/dev/null || stat -c%s "$log") -gt 10485760 ]; then
        mv "$log" "$log.old"
        touch "$log"
    fi
done
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status and logs
sudo systemctl status roko-webserver
sudo journalctl -u roko-webserver --no-pager

# Common fixes:
sudo systemctl daemon-reload
sudo systemctl reset-failed roko-webserver
sudo systemctl start roko-webserver
```

#### Port Already in Use
```bash
# Find process using port 8187
sudo lsof -i :8187
sudo netstat -tulpn | grep 8187

# Kill conflicting process
sudo kill -9 PID
```

#### Data Not Updating
```bash
# Check cron job
crontab -l | grep run_scheduled_extraction

# Check extraction logs
tail -20 /home/roctinam/roko-token-extractor/logs/scheduled_extraction.log

# Manual extraction test
cd /home/roctinam/roko-token-extractor
./run_scheduled_extraction.sh
```

#### Cache Issues
```bash
# Clear browser cache or test with curl
curl -H "Cache-Control: no-cache" http://localhost:8187/price

# Restart web server to clear any server-side issues
sudo systemctl restart roko-webserver
```

### Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 404 | File not found | Check if symlink exists, verify file permissions |
| 500 | Server error | Check server logs, verify Python script syntax |
| 503 | Service unavailable | Check if service is running, verify port availability |
| Connection refused | Server not running | Start the service: `sudo systemctl start roko-webserver` |

### Performance Tuning

**For High Traffic:**
```python
# In serve_web.py, adjust cache headers
self.send_header('Cache-Control', 'public, max-age=300')  # 5 minutes
```

**For Faster Updates:**
```bash
# Reduce extraction interval to 5 minutes
*/5 * * * * /home/roctinam/roko-token-extractor/run_scheduled_extraction.sh
```

## Security Considerations

### Systemd Security Features
- `NoNewPrivileges=true`: Prevents privilege escalation
- `PrivateTmp=true`: Isolates /tmp directory
- `ProtectSystem=strict`: Read-only system directories
- `ProtectHome=read-only`: Limited home directory access

### Network Security
- Server binds to all interfaces (0.0.0.0) - consider firewall rules
- CORS enabled for cross-origin requests
- No authentication required - consider adding if needed

### File Permissions
```bash
# Recommended permissions
chmod 755 /home/roctinam/production-deploy/roko-token-extractor/serve_web.py
chmod 644 /home/roctinam/production-deploy/roko-token-extractor/roko-webserver.service
chmod 755 /home/roctinam/production-deploy/roko-token-extractor/install_service.sh
chmod 755 /home/roctinam/roko-token-extractor/run_scheduled_extraction.sh
```

## Production URLs

### Local Access
- **Dashboard**: http://localhost:8187/
- **API**: http://localhost:8187/price

### Production (roko.matric.io)
- **API**: https://roko.matric.io/price
- **Dashboard**: https://roko.matric.io/

The production domain should be configured with a reverse proxy (nginx/apache) that forwards requests to port 8187.

## Backup & Recovery

### Data Backup
```bash
# Backup current production data
tar -czf roko-backup-$(date +%Y%m%d).tar.gz \
  /home/roctinam/production-deploy/roko-token-extractor/public \
  /home/roctinam/production-deploy/roko-token-extractor/data \
  /home/roctinam/production-deploy/roko-token-extractor/logs
```

### Service Recovery
```bash
# Complete service reinstallation
sudo systemctl stop roko-webserver
sudo systemctl disable roko-webserver
sudo rm /etc/systemd/system/roko-webserver.service
sudo ./install_service.sh
```

## Updates & Maintenance

### Updating the System
```bash
# Pull latest changes
cd /home/roctinam/roko-token-extractor
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart roko-webserver
```

### Zero-Downtime Updates
```bash
# For production environments, use blue-green deployment
# 1. Deploy to alternate directory
# 2. Update symlinks
# 3. Restart service
# 4. Verify functionality
# 5. Remove old deployment
```

This deployment guide provides comprehensive coverage of the ROKO Token Extractor production system. For additional support or questions, refer to the project repository or contact the development team.
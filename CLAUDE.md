# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a production-ready ERC20 token data extraction tool designed for automated deployment. It extracts real-time blockchain data including pricing, TVL (Total Value Locked), volume metrics, and holder information for any ERC20 token on Ethereum mainnet. The system features RPC load balancing, treasury exclusion for accurate circulating supply, and is optimized for web delivery via cronjobs.

## Essential Commands

### Running the Extractor
```bash
# Basic extraction with default settings
python update_roko_data.py

# Production deployment with custom paths
python update_roko_data.py --output-dir /var/www/html --filename token.json --timestamped

# With custom export directory
python update_roko_data.py --output-dir /var/www/html --export-dir /var/log/token --filename token.json

# Update RPC endpoints (run weekly)
python update_rpc_endpoints.py

# Development/testing interface
python src/main.py
```

### Production Web Server & Service Management
```bash
# Install systemd service (runs web server on port 8187)
sudo ./install_service.sh

# Service management commands
sudo systemctl start roko-webserver       # Start web server
sudo systemctl stop roko-webserver        # Stop web server
sudo systemctl restart roko-webserver     # Restart web server
sudo systemctl status roko-webserver      # Check service status
sudo systemctl enable roko-webserver      # Enable auto-start on boot
sudo systemctl disable roko-webserver     # Disable auto-start

# View web server logs
sudo journalctl -u roko-webserver -f      # Follow live logs
tail -f logs/webserver.log                # Access logs
tail -f logs/webserver_error.log          # Error logs

# Manual web server (for testing)
python serve_web.py --port 8187 --directory public

# Test API endpoints
curl http://localhost:8187/price          # API endpoint
curl http://localhost:8187/               # Dashboard
```

### Automated Data Extraction (Cron)
```bash
# Set up 15-minute cron schedule
crontab -e
# Add: */15 * * * * /home/roctinam/roko-token-extractor/run_scheduled_extraction.sh >> /home/roctinam/roko-token-extractor/logs/cron.log 2>&1

# Manual scheduled extraction
./run_scheduled_extraction.sh

# View extraction logs
tail -f logs/scheduled_extraction.log     # Extraction logs
tail -f logs/cron.log                     # Cron execution logs

# Monitor extraction status
ls -la public/roko-price.json             # Check last update time
ls -la data/roko-price-*.json             # View archived extractions
```

### Installation and Setup
```bash
# System prerequisites (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3-pip python3.12-venv

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with token addresses and API keys

# Verify configuration
python src/main.py --validate
```

## High-Level Architecture

### Core Components

**Enhanced RPC Client System** (`src/core/enhanced_rpc_client.py`, `src/core/rpc_load_balancer.py`)
- Manages multiple RPC endpoints with automatic failover
- Health testing and rate limit handling
- ChainList.org integration for endpoint discovery
- Alchemy priority mode when API key is configured
- Temporary exclusion of failed endpoints

**Token Analysis Pipeline** (`src/core/token_analyzer.py`)
- Extracts ERC20 token metadata (name, symbol, decimals, supply)
- Calculates circulating supply by excluding treasury wallets
- Full precision arithmetic to prevent floating-point errors
- Direct blockchain queries for accurate data

**Pool Monitoring System** (`src/core/pool_monitor.py`)
- Monitors Uniswap V2 and V3 pools
- Calculates TVL from pool reserves
- Tracks volume metrics (24h, 7d, 30d)
- Identifies all pools containing the target token

**Price Oracle** (`src/core/price_oracle.py`)
- Pool-based pricing using token:ETH ratio from Uniswap
- ETH price from stablecoin pools (USDC/USDT)
- Market cap calculations using circulating supply
- Full decimal precision maintained throughout

**Data Processing** (`src/utils/data_processor.py`)
- Formats data for web delivery
- Maintains full precision in JSON output
- Creates timestamped backups
- Handles export to CSV format

**Production Web Server** (`serve_web.py`)
- HTTP server with CORS support and ETag caching
- Serves JSON data on port 8187
- Intelligent cache headers (15-minute TTL)
- Clean API endpoint via symlink (`/price` → `roko-price.json`)

**Service Management** (`roko-webserver.service`, `install_service.sh`)
- Systemd service for automatic startup and monitoring
- Security hardening (NoNewPrivileges, PrivateTmp, ProtectSystem)
- Automatic restart on failure
- Dedicated logging to separate files

**Scheduled Extraction** (`run_scheduled_extraction.sh`)
- Cron wrapper for automated data updates every 15 minutes
- Creates timestamped archives in data/ directory
- Comprehensive error handling and logging
- Virtual environment management

### Configuration Management

**Config System** (`src/config/settings.py`, `config/config.yaml`)
- YAML-based configuration with environment variable overrides
- Token addresses and treasury wallets
- RPC endpoint configuration
- Uniswap factory and WETH addresses
- API keys for various services

**Environment Variables** (`.env`)
- `TOKEN_ADDRESS`: Target ERC20 token contract
- `TOKEN_NAME`, `TOKEN_SYMBOL`: Display information
- `TREASURY_WALLETS`: Comma-separated treasury addresses
- `ALCHEMY_API_KEY`: Priority RPC endpoint
- Stablecoin addresses for ETH pricing

### Production Features

**Command Line Interface** (`update_roko_data.py`)
- `--output-dir/-o`: Web delivery directory
- `--export-dir/-e`: CSV/JSON export location
- `--filename/-f`: Output filename
- `--timestamped/-t`: Create timestamped backups

**RPC Management** (`update_rpc_endpoints.py`)
- Fetches fresh endpoints from ChainList.org
- Tests endpoint health and response times
- Updates `config/config.yaml` with working endpoints
- Maintains backup of ChainList data

## Key Architectural Decisions

### Treasury Exclusion System
The system calculates circulating supply by excluding configured treasury wallets. This provides accurate market cap calculations and is essential for tokenomics analysis. Treasury addresses are configured in the `.env` file as a comma-separated list.

### Full Precision Arithmetic
All numerical values are stored as strings with full decimal precision to prevent floating-point errors. The `format_precision()` function handles conversion while the `format_display()` function adds commas for console output.

### RPC Load Balancing Strategy
The system uses multiple RPC endpoints with health monitoring:
1. Alchemy API (priority when available)
2. ChainList.org public endpoints (auto-discovered)
3. Temporary exclusion of failed endpoints
4. Automatic retry with exponential backoff

### Pool-Based Pricing
Prices are calculated directly from Uniswap pool reserves rather than external APIs. This provides:
- Real-time accuracy from actual trading data
- No dependency on third-party price feeds
- Direct token:ETH ratio calculation
- ETH pricing from stablecoin pools

## Data Output Structure

The system generates JSON with this structure:
```json
{
  "timestamp": unix_timestamp,
  "datetime": "ISO 8601 format",
  "last_updated": "Human readable UTC",
  "token": {
    "address": "0x...",
    "name": "Token Name",
    "symbol": "SYMBOL",
    "decimals": 18,
    "total_supply": "full_precision_string",
    "circulating_supply": "full_precision_string",
    "treasury_holdings": "full_precision_string",
    "treasury_percentage": "43.68"
  },
  "pricing": {
    "token_eth_ratio": "full_precision_string",
    "eth_per_token": "full_precision_string",
    "usd_per_token": "full_precision_string",
    "eth_price_usd": "full_precision_string",
    "market_cap_usd": "formatted_with_commas",
    "total_market_cap_usd": "formatted_with_commas"
  },
  "tvl": {
    "total_tvl_usd": "formatted_with_commas",
    "pools_count": 1,
    "pools": [...]
  },
  "volume": {
    "volume_24h_usd": "formatted_with_commas",
    "volume_7d_usd": "formatted_with_commas",
    "volume_30d_usd": "formatted_with_commas"
  }
}
```

## Development Guidelines

### Adding New Token Support
1. Update `.env` file with new token address and details
2. Add treasury wallets if applicable
3. Verify token has Uniswap pools (V2 or V3)
4. Run extraction to validate data

### Modifying Price Sources
Price calculation happens in `src/core/price_oracle.py`. The system uses:
1. Direct pool reserves for token:ETH ratio
2. Stablecoin pools for ETH:USD pricing
3. No external API dependencies by default

### Extending Data Fields
1. Add extraction logic to relevant analyzer class
2. Update `format_data()` in `update_roko_data.py`
3. Ensure full precision is maintained
4. Update output validation if needed

### Error Handling
- All RPC calls have retry logic with exponential backoff
- Failed endpoints are temporarily excluded
- Comprehensive logging to `logs/` directory
- Graceful degradation when data sources fail

## Deployment Notes

### Production Checklist
1. Configure `.env` with production values
2. Set up output directory with appropriate permissions
3. Configure cronjob or systemd timer for automation
4. Run `update_rpc_endpoints.py` weekly for fresh endpoints
5. Monitor logs for RPC failures or rate limits

### Security Considerations
- Never commit `.env` file (use `env.example` as template)
- API keys should have minimal required permissions
- Output directory should have restricted write access
- Use systemd service with dedicated user for production

### Performance Optimization
- RPC load balancer minimizes latency
- Concurrent requests where applicable
- Caching of static data (token metadata)
- Efficient batch queries for holder data

## Important Implementation Details

### RPC Endpoint Management
The system maintains a dynamic list of RPC endpoints in `config/config.yaml`. Failed endpoints are tracked in memory and excluded temporarily. The `update_rpc_endpoints.py` script refreshes this list from ChainList.org.

### Treasury Wallet Handling
Treasury wallets are excluded from circulating supply calculations. Multiple wallets can be specified as comma-separated values in `TREASURY_WALLETS` environment variable.

### Decimal Precision
All Web3 interactions use full precision integers. Conversion to decimal only happens for display/storage, maintaining precision throughout the calculation pipeline.

### Volume Metrics
Currently placeholder values in the output. Full implementation would require indexing historical swap events from Uniswap pools.
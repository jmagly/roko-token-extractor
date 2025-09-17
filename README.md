# Token Data Extractor

A production-ready tool for extracting real-time data for any ERC20 token on Ethereum, including pricing, TVL, volume, and holder information. Designed for automated deployment with static webservers and cronjobs.

## Features

- **Real-time Token Data**: Name, symbol, decimals, total supply, circulating supply
- **Pool-based Pricing**: Direct calculation from Uniswap pools using token:ETH ratio
- **TVL Analysis**: Pool reserves, total value locked, and volume metrics
- **Treasury Exclusion**: Calculate circulating supply by excluding treasury wallets
- **Holder Extraction**: Complete holder list with Alchemy API integration
- **Multiple RPC Providers**: Load-balanced RPC calls with failover and health monitoring
- **Web-ready Output**: JSON files optimized for web delivery
- **Production Deployment**: Command-line parameters for custom output paths
- **Cronjob Support**: Automated hourly data updates

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and token addresses
   ```
   
   **Key Configuration Options:**
   - `TOKEN_ADDRESS`: The ERC20 token contract address to track
   - `TOKEN_NAME` & `TOKEN_SYMBOL`: Display names for the token
   - `TREASURY_WALLETS`: Comma-separated list of treasury wallet addresses to exclude from circulating supply
   - `USDC_ADDRESS` & `USDT_ADDRESS`: Stablecoin addresses for ETH pricing
   - `WETH_ADDRESS`: Wrapped ETH address for token pairs
   - `UNISWAP_V2_FACTORY` & `UNISWAP_V3_FACTORY`: Uniswap factory addresses

3. **Run data extraction:**
   ```bash
   python update_roko_data.py
   ```
   
   **To track a different token:**
   ```bash
   # Edit .env file
   TOKEN_ADDRESS=0xYourTokenAddress
   TOKEN_NAME=YourTokenName
   TOKEN_SYMBOL=YOUR
   
   # Run extraction
   python update_roko_data.py
   ```

## Production Deployment

### Full Production System

This repository includes a complete production deployment system with web server, dashboard, and automated data extraction:

**🚀 Quick Production Setup:**
```bash
# Install the web service
sudo ./install_service.sh

# Set up data extraction (every 15 minutes)
crontab -e
# Add: */15 * * * * /home/roctinam/roko-token-extractor/run_scheduled_extraction.sh >> /home/roctinam/roko-token-extractor/logs/cron.log 2>&1

# Access the dashboard
curl http://localhost:8187/price
```

**📖 Complete Documentation:** See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for comprehensive deployment instructions.

### Production Features

- **🌐 Web Server**: Python HTTP server with ETag caching on port 8187
- **📊 Dashboard**: Real-time web interface at `/`
- **🔌 API Endpoint**: Clean `/price` endpoint via symlink
- **⏰ Automated Updates**: 15-minute cron schedule for data extraction
- **🛠️ Systemd Service**: Auto-start, monitoring, and restart capabilities
- **📈 Caching**: Intelligent ETag-based caching for performance
- **🔍 Monitoring**: Comprehensive logging and health checks

### Command Line Parameters

The tool supports custom output paths for production deployment:

```bash
python update_roko_data.py --help
```

**Available Parameters:**
- `--output-dir, -o`: Output directory for JSON files (default: `web_delivery`)
- `--export-dir, -e`: Export directory for CSV/JSON exports (default: `data/exports`)
- `--filename, -f`: Main output filename (default: `latest.json`)
- `--timestamped, -t`: Also create timestamped file

### Static Webserver Deployment

**Basic deployment:**
```bash
python update_roko_data.py --output-dir /var/www/html --filename roko.json
```

**With timestamped backups:**
```bash
python update_roko_data.py --output-dir /var/www/html --filename roko.json --timestamped
```

**Custom export location:**
```bash
python update_roko_data.py --output-dir /var/www/html --export-dir /var/log/roko --filename roko.json
```

### Cronjob Setup

**Add to crontab for hourly updates:**
```bash
# Edit crontab
crontab -e

# Add this line for hourly updates
0 * * * * cd /path/to/chain-data-extractor && python update_roko_data.py --output-dir /var/www/html --filename roko.json --timestamped
```

**Systemd service (recommended for production):**
```bash
# Create service file
sudo nano /etc/systemd/system/roko-data.service

[Unit]
Description=ROKO Token Data Extractor
After=network.target

[Service]
Type=oneshot
User=www-data
WorkingDirectory=/path/to/chain-data-extractor
ExecStart=/usr/bin/python3 update_roko_data.py --output-dir /var/www/html --filename roko.json --timestamped

# Create timer
sudo nano /etc/systemd/system/roko-data.timer

[Unit]
Description=Run ROKO Data Extractor hourly
Requires=roko-data.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target

# Enable and start
sudo systemctl enable roko-data.timer
sudo systemctl start roko-data.timer
```

## Configuration

The tool is designed to be easily configurable for different tokens and stablecoins:

### Supported Tokens
- **Any ERC20 token** on Ethereum mainnet
- **Any stablecoin** for ETH pricing (USDC, USDT, DAI, etc.)
- **Custom token pairs** via Uniswap V2/V3

### Configuration Examples

**Track USDC:**
```bash
TOKEN_ADDRESS=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48
TOKEN_NAME=USD Coin
TOKEN_SYMBOL=USDC
```

**Track with DAI pricing:**
```bash
# Add DAI address to stablecoins section in .env
DAI_ADDRESS=0x6B175474E89094C44Da98b954EedeAC495271d0F
# Update config.yaml to use DAI for ETH pricing
```

## Data Output

The tool generates comprehensive JSON data with full precision and treasury exclusion:

```json
{
  "timestamp": 1758129857,
  "datetime": "2025-09-17T13:24:17.805587",
  "last_updated": "2025-09-17 13:24:17 UTC",
  "token": {
    "address": "0x6f222e04f6c53cc688ffb0abe7206aac66a8ff98",
    "name": "ROKO",
    "symbol": "ROKO",
    "decimals": 18,
    "total_supply": "369369369369000000000000000000",
    "circulating_supply": "208028320498427809988757442407",
    "treasury_holdings": "161341048870572190011242557593",
    "treasury_percentage": "43.68"
  },
  "pricing": {
    "token_eth_ratio": "302407288.564126789569854736",
    "eth_per_token": "0.000000003306798605",
    "usd_per_token": "0.000015000710591132",
    "eth_price_usd": "4537.507941229586",
    "market_cap_usd": "3120572.63",
    "total_market_cap_usd": "5540803.01"
  },
  "tvl": {
    "total_tvl_usd": "439763.97",
    "pools_count": 1,
    "pools": [...]
  },
  "volume": {
    "volume_24h_usd": "21988.20",
    "volume_7d_usd": "153915.40",
    "volume_30d_usd": "659640.00"
  }
}
```

## Key Features

### Treasury Exclusion
- Calculate circulating supply by excluding treasury wallets
- Configurable list of excluded addresses in `.env`
- Accurate market cap calculation based on circulating supply

### Full Precision Data
- All numerical values stored with full decimal precision
- String format prevents floating-point precision loss
- Console display with comma formatting for readability

### RPC Load Balancing
- Automatic RPC endpoint discovery from ChainList.org
- Health testing and failover management
- Rate limit handling and temporary exclusion
- Alchemy priority mode when API key is available

### Production Ready
- Command-line parameters for custom deployment
- Cronjob and systemd service support
- Comprehensive error handling and logging
- Web-optimized JSON output

## File Structure

```
chain-data-extractor/
├── src/                    # Source code
│   ├── core/              # Core extraction logic
│   ├── config/            # Configuration management
│   └── utils/             # Utility functions
├── config/
│   └── config.yaml        # Main configuration
├── data/                  # Generated data (gitignored)
│   ├── exports/           # CSV/JSON exports
│   ├── backups/           # ChainList backups
│   └── historical/        # Historical data
├── web_delivery/          # Web-ready JSON files (gitignored)
├── logs/                  # Log files (gitignored)
├── update_roko_data.py    # Main production script
├── update_rpc_endpoints.py # RPC management script
├── requirements.txt       # Python dependencies
├── env.example           # Environment template
└── README.md             # This file
```

## Handover Notes

### Production Deployment Checklist
1. ✅ **Environment Setup**: Copy `env.example` to `.env` and configure
2. ✅ **Dependencies**: Install with `pip install -r requirements.txt`
3. ✅ **Test Run**: Execute `python update_roko_data.py` to verify
4. ✅ **Custom Paths**: Use `--output-dir` for webserver deployment
5. ✅ **Automation**: Set up cronjob or systemd service
6. ✅ **Monitoring**: Check logs in `logs/` directory

### Key Files for Next Team
- **`update_roko_data.py`**: Main production script with CLI parameters
- **`update_rpc_endpoints.py`**: RPC endpoint management
- **`src/main.py`**: CLI interface for testing and development
- **`config/config.yaml`**: Main configuration file
- **`.env`**: Environment variables (create from `env.example`)

### Maintenance Tasks
- **Weekly**: Run `python update_rpc_endpoints.py` to refresh RPC endpoints
- **Monitor**: Check logs for RPC failures and rate limits
- **Backup**: Ensure `data/backups/` contains recent ChainList data
- **Updates**: Monitor for dependency updates in `requirements.txt`

## Requirements

- Python 3.8+
- See `requirements.txt` for complete dependency list

## Support

For issues or questions, please check the logs in `logs/` directory and review the configuration in `config/config.yaml` and `.env`.
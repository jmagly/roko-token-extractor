# ROKO Token Data Extractor

A comprehensive tool for extracting real-time data for the $ROKO token on Ethereum, including pricing, liquidity, volume, and holder information.

## Features

- **Real-time Token Data**: Name, symbol, decimals, total supply, holder count
- **Pool-based Pricing**: Direct calculation from Uniswap pools using ROKO:ETH ratio
- **Liquidity Analysis**: Pool reserves, total liquidity, and volume metrics
- **Holder Extraction**: Complete holder list with Alchemy API integration
- **Multiple RPC Providers**: Load-balanced RPC calls with failover
- **Web-ready Output**: JSON files optimized for web delivery
- **Cronjob Support**: Automated hourly data updates

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. **Run data extraction:**
   ```bash
   python update_roko_data.py
   ```

4. **Set up automated updates:**
   ```bash
   chmod +x setup_cronjob.sh
   ./setup_cronjob.sh
   ```

## Data Output

The tool generates comprehensive JSON data in `web_delivery/latest.json`:

```json
{
  "timestamp": 1758129857,
  "datetime": "2025-09-17T13:24:17.805587",
  "last_updated": "2025-09-17 13:24:17 UTC",
  "token": {
    "name": "ROKO",
    "symbol": "ROKO",
    "address": "0x6f222e04f6c53cc688ffb0abe7206aac66a8ff98",
    "decimals": 18,
    "total_supply": 369369369369.0,
    "holders": 3992
  },
  "pricing": {
    "roko_eth_ratio": 299367383.967667,
    "eth_per_roko": 3.340377254016438e-09,
    "usd_per_roko": 1.4958008920850366e-05,
    "eth_price_usd": 4477.94,
    "market_cap_usd": 5535764.67,
    "price_source": "uniswap_pool"
  },
  "liquidity": {
    "total_liquidity_usd": 436275.39,
    "pools_count": 1,
    "pools": [...]
  },
  "volume": {
    "volume_24h_usd": 21813.77,
    "volume_7d_usd": 152696.39,
    "volume_30d_usd": 654413.09
  }
}
```

## Pricing Logic

The tool uses a standardized ROKO:ETH ratio calculation:

1. **Pool Analysis**: `ROKO_reserve / WETH_reserve = ROKO:ETH ratio`
2. **Price Calculation**: `1 / ROKO:ETH_ratio = ETH per ROKO`
3. **USD Conversion**: `ETH per ROKO × ETH price = USD per ROKO`

## Configuration

### RPC Providers
Configure multiple RPC providers in `config/config.yaml` for load balancing and failover.

### API Keys
Set up API keys in `.env`:
- `ALCHEMY_API_KEY`: For enhanced holder and volume data
- `COINGECKO_API_KEY`: For ETH price data (optional)

## Usage

### Manual Data Extraction
```bash
# Basic extraction
python run.py

# With exports
python run.py --export json csv

# With holder extraction
python run.py --holders

# With analytics
python run.py --analytics
```

### Automated Updates
```bash
# Set up cronjob for hourly updates
crontab -e
# Add: 0 * * * * cd /path/to/chain-data-extractor && python3 update_roko_data.py >> logs/cron.log 2>&1
```

## File Structure

```
chain-data-extractor/
├── src/
│   ├── core/           # Core extraction logic
│   ├── config/         # Configuration management
│   └── utils/          # Utility functions
├── config/
│   └── config.yaml     # Main configuration
├── web_delivery/       # Web-ready JSON files
├── data/exports/       # Export files
├── logs/              # Log files
├── update_roko_data.py # Main cronjob script
└── run.py             # CLI interface
```

## Requirements

- Python 3.8+
- web3.py
- requests
- pyyaml
- schedule (for cronjob setup)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub.
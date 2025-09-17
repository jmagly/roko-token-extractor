# ROKO Token Data Extractor - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Features](#features)
5. [CLI Reference](#cli-reference)
6. [Configuration](#configuration)
7. [Data Sources](#data-sources)
8. [Output Formats](#output-formats)
9. [Advanced Analytics](#advanced-analytics)
10. [Troubleshooting](#troubleshooting)
11. [API Reference](#api-reference)
12. [Examples](#examples)

## Overview

The ROKO Token Data Extractor is a comprehensive Python tool designed to extract detailed token and liquidity pool pricing data for the ROKO token on the Ethereum blockchain using direct RPC API communications.

### Key Capabilities
- **Real-time Data Extraction**: Live blockchain data retrieval
- **Multiple Price Sources**: Integration with CoinGecko, DexScreener, 1inch, and Uniswap
- **Pool Analysis**: Uniswap V2/V3 liquidity pool detection and monitoring
- **Historical Tracking**: SQLite database for long-term data storage
- **Advanced Analytics**: Token holder analysis and exchange interaction tracking
- **Comprehensive Export**: JSON and CSV data export capabilities
- **Real-time Monitoring**: Configurable interval monitoring

### Token Information
- **Contract Address**: `0x6f222e04f6c53cc688ffb0abe7206aac66a8ff98`
- **Network**: Ethereum Mainnet
- **Standard**: ERC-20
- **Etherscan**: [View on Etherscan](https://etherscan.io/address/0x6f222e04f6c53cc688ffb0abe7206aac66a8ff98)
- **Uniswap**: [View on Uniswap](https://app.uniswap.org/explore/tokens/ethereum/0x6f222E04F6c53Cc688FfB0Abe7206aAc66A8FF98)

## Installation

### Prerequisites
- Python 3.8 or higher
- Git
- Internet connection for API access

### Setup
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd chain-data-extractor
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env and add your API keys if needed
   ```

4. **Verify installation:**
   ```bash
   python test_connection.py
   ```

## Quick Start

### Basic Usage
```bash
# Extract current token data
python run.py

# Export to JSON
python run.py --export json

# Export to multiple formats
python run.py --export json csv
```

### Advanced Usage
```bash
# Full extraction with analytics
python run.py --analytics --export json

# Real-time monitoring
python run.py --monitor --interval 60

# Historical analysis
python run.py --historical 30
```

### Help System
```bash
# Basic help
python run.py --help

# Detailed help
python run.py --help-detailed

# Specific help sections
python run.py --help-detailed examples
python run.py --help-detailed configuration
python run.py --help-detailed troubleshooting
```

## Features

### Core Features
- **Token Data Extraction**: Name, symbol, decimals, total supply, pricing
- **Pool Detection**: Automatic discovery of Uniswap V2/V3 pools
- **Price Aggregation**: Multiple price sources with intelligent selection
- **Real-time Monitoring**: Configurable interval data collection
- **Historical Tracking**: Persistent data storage and analysis
- **Data Export**: JSON and CSV export capabilities

### Advanced Analytics
- **Token Holder Analysis**: Extract all wallet addresses from Transfer events
- **Exchange Interaction Tracking**: Monitor DEX usage patterns
- **Concentration Metrics**: Gini coefficient and wealth distribution analysis
- **User Behavior Analysis**: Trading patterns and exchange preferences
- **Liquidity Provider Identification**: Framework for LP analysis

### Data Sources
- **Ethereum RPC**: Direct blockchain communication
- **CoinGecko API**: Token price data
- **DexScreener API**: DEX aggregation data
- **1inch API**: Liquidity-based pricing
- **Uniswap Integration**: Direct pool contract interaction

## CLI Reference

### Basic Commands
```bash
python run.py                    # Basic data extraction
python run.py --export json      # Export to JSON
python run.py --export json csv  # Export to multiple formats
```

### Advanced Commands
```bash
python run.py --analytics                    # Include advanced analytics
python run.py --monitor                      # Start real-time monitoring
python run.py --monitor --interval 60        # Custom monitoring interval
python run.py --historical 30                # Historical data summary
python run.py --config custom.yaml           # Custom configuration
```

### Help Commands
```bash
python run.py --help                         # Basic help
python run.py --help-detailed                # Detailed help
python run.py --help-detailed examples       # Usage examples
python run.py --help-detailed configuration  # Configuration guide
python run.py --help-detailed troubleshooting # Troubleshooting guide
```

### Command Line Options
| Option | Description | Default |
|--------|-------------|---------|
| `--config` | Configuration file path | `config/config.yaml` |
| `--export` | Export formats (json, csv) | None |
| `--monitor` | Start real-time monitoring | False |
| `--interval` | Monitoring interval in seconds | 30 |
| `--analytics` | Include advanced analytics | False |
| `--historical` | Show historical summary for N days | None |
| `--help-detailed` | Show detailed help information | None |

## Configuration

### Configuration File
The main configuration is stored in `config/config.yaml`:

```yaml
ethereum:
  rpc_url: "https://eth.llamarpc.com"
  api_key: ""
  chain_id: 1
  gas_limit: 100000

roko_token:
  address: "0x6f222e04f6c53cc688ffb0abe7206aac66a8ff98"
  name: "ROKO"
  symbol: "ROKO"

monitoring:
  update_interval: 30
  historical_data_days: 30
  export_format: ["json", "csv"]
  log_level: "INFO"

pools:
  uniswap_v2_factory: "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
  uniswap_v3_factory: "0x1F98431c8aD98523631AE4a59f267346ea31F984"
  weth_address: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
  usdc_address: "0xA0b86a33E6441b8C4C8C0C4C8C0C4C8C0C4C8C0C4"
```

### Configuration Sections

#### Ethereum Settings
- `rpc_url`: Ethereum RPC endpoint URL
- `api_key`: API key for authentication (if required)
- `chain_id`: Ethereum chain ID (1 for mainnet)
- `gas_limit`: Gas limit for transactions

#### ROKO Token Settings
- `address`: ROKO token contract address
- `name`: Token name
- `symbol`: Token symbol

#### Monitoring Settings
- `update_interval`: Default monitoring interval in seconds
- `historical_data_days`: Days of historical data to keep
- `export_format`: Default export formats
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR)

#### Pool Settings
- `uniswap_v2_factory`: Uniswap V2 factory contract address
- `uniswap_v3_factory`: Uniswap V3 factory contract address
- `weth_address`: WETH contract address
- `usdc_address`: USDC contract address

## Data Sources

### Price Sources

#### CoinGecko API
- **URL**: `https://api.coingecko.com/api/v3/simple/token_price/ethereum`
- **Rate Limit**: 10-50 calls/minute
- **Supports**: USD prices for verified tokens
- **Reliability**: High for established tokens

#### DexScreener API
- **URL**: `https://api.dexscreener.com/latest/dex/tokens/`
- **Rate Limit**: 300 calls/minute
- **Supports**: DEX prices and trading data
- **Reliability**: Good for DEX data

#### 1inch API
- **URL**: `https://api.1inch.io/v5.0/1/quote`
- **Rate Limit**: 100 calls/minute
- **Supports**: Liquidity-based pricing
- **Reliability**: Good for liquidity data

#### Uniswap Integration
- **Method**: Direct pool contract interaction
- **Rate Limit**: Depends on RPC provider
- **Supports**: Real-time pool-based pricing
- **Reliability**: High for active pools

### RPC Endpoints

#### eth.llamarpc.com (Public)
- **URL**: `https://eth.llamarpc.com`
- **Type**: Public
- **Rate Limit**: Moderate
- **Reliability**: Good
- **Cost**: Free

#### Alchemy (Commercial)
- **URL**: `https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY`
- **Type**: Commercial
- **Rate Limit**: High
- **Reliability**: Excellent
- **Cost**: Paid (free tier available)

## Output Formats

### JSON Export
- **Location**: `data/exports/roko_data_TIMESTAMP.json`
- **Description**: Complete data structure for programmatic use
- **Includes**:
  - Token metadata and pricing
  - Pool data and liquidity information
  - Historical data and analytics
  - Exchange interaction data

### CSV Export
- **Location**: `data/exports/roko_token_TIMESTAMP.csv`
- **Description**: Time-series data for analysis in spreadsheet applications
- **Includes**:
  - Token data over time
  - Price history
  - Holder statistics
  - Exchange activity

### SQLite Database
- **Location**: `data/historical/token_data.db`
- **Description**: Persistent storage for historical tracking
- **Tables**:
  - `price_history`: Price data over time
  - `holder_history`: Holder count and concentration metrics
  - `exchange_activity`: Exchange usage statistics

## Advanced Analytics

### Token Holder Analysis
The system extracts token holders by analyzing Transfer events from the blockchain:

```python
# Example holder analysis output
{
  "total_holders": 1250,
  "top_holders": [
    {
      "address": "0x...",
      "balance": 1000000000000000000000,
      "percentage": 15.5
    }
  ],
  "concentration_metrics": {
    "top_10_percentage": 45.2,
    "top_100_percentage": 78.9,
    "gini_coefficient": 0.65
  }
}
```

### Exchange Interaction Tracking
Monitor which exchanges users interact with:

```python
# Example exchange interaction data
{
  "total_exchange_transactions": 5420,
  "unique_users_interacting": 890,
  "exchange_breakdown": {
    "uniswap_v2_router": {
      "transaction_count": 3200,
      "total_volume": 1500000000000000000000,
      "unique_users": 450
    }
  }
}
```

### Concentration Metrics
- **Gini Coefficient**: Measures wealth distribution inequality
- **Top Holder Percentages**: Concentration in top 10, 100 holders
- **Holder Growth**: Track holder count changes over time

## Troubleshooting

### Common Issues

#### Rate Limiting (429 Error)
**Symptom**: `429 Client Error: Too Many Requests`
**Cause**: RPC endpoint or API rate limiting
**Solution**: 
- Wait a few minutes before retrying
- Use a different RPC endpoint
- Increase monitoring intervals

#### Connection Error
**Symptom**: `Failed to connect to Ethereum node`
**Cause**: RPC endpoint unavailable or incorrect URL
**Solution**:
- Check RPC URL in configuration
- Verify internet connection
- Try a different RPC endpoint

#### No Pools Found
**Symptom**: `Found 0 ROKO pools`
**Cause**: Token may not have active liquidity pools
**Solution**: This is normal for new or low-liquidity tokens

#### Price Data Unavailable
**Symptom**: Price shows as placeholder values
**Cause**: Price APIs rate limited or token not supported
**Solution**:
- Check API keys and token address
- Verify token is listed on price sources
- Wait for rate limits to reset

### Debugging Steps

1. **Enable Debug Logging**:
   Set `log_level: DEBUG` in `config/config.yaml`

2. **Check Logs**:
   View `logs/roko_extractor.log` for detailed information

3. **Test Connection**:
   Run `python test_connection.py`

4. **Verify Configuration**:
   Check `config/config.yaml` for correct settings

5. **Test Individual Components**:
   Run `python test_pricing.py`
   Run `python test_all_features.py`

### Performance Optimization

- Use commercial RPC endpoints for better rate limits
- Increase monitoring intervals for reduced API usage
- Enable caching for frequently accessed data
- Use historical data for analysis instead of real-time queries

## API Reference

### Core Classes

#### ROKODataExtractor
Main class for data extraction and monitoring.

```python
extractor = ROKODataExtractor(config_path="config/config.yaml")
summary = extractor.run_extraction(export_formats=['json'], include_analytics=True)
```

#### TokenAnalytics
Advanced analytics for token holders and exchange interactions.

```python
analytics = TokenAnalytics(rpc_client, token_address)
holder_data = analytics.get_token_holders_from_events()
exchange_data = analytics.get_exchange_interactions()
```

#### HistoricalTracker
Historical data tracking and storage.

```python
tracker = HistoricalTracker()
tracker.store_price_data(token_address, price_data)
history = tracker.get_price_history(token_address, days=30)
```

### Key Methods

#### Data Extraction
- `extract_token_data()`: Extract comprehensive token data
- `extract_pool_data()`: Extract liquidity pool data
- `run_extraction()`: Run complete extraction process

#### Analytics
- `get_token_holders_from_events()`: Extract token holders
- `get_exchange_interactions()`: Analyze exchange usage
- `get_comprehensive_analytics()`: Full analytics analysis

#### Historical Tracking
- `store_price_data()`: Store price data in database
- `get_price_history()`: Retrieve historical price data
- `get_summary_statistics()`: Get statistical summary

## Examples

### Basic Data Extraction
```bash
# Extract current data
python run.py

# Export to JSON
python run.py --export json

# Export to multiple formats
python run.py --export json csv
```

### Advanced Analysis
```bash
# Full extraction with analytics
python run.py --analytics --export json

# Historical analysis
python run.py --historical 7

# Real-time monitoring
python run.py --monitor --interval 300
```

### Production Use Cases

#### Daily Price Monitoring
```bash
python run.py --monitor --interval 3600 --export json
# Monitor price every hour and export to JSON
```

#### Research Analysis
```bash
python run.py --analytics --export json csv --historical 30
# Full analysis with 30 days of historical data
```

#### High-Frequency Monitoring
```bash
python run.py --monitor --interval 60 --config config/high_freq.yaml
# Monitor every minute with custom settings
```

### Custom Configuration
```bash
# Use custom configuration
python run.py --config config/production.yaml

# Monitor with custom settings
python run.py --monitor --interval 30 --config config/high_freq.yaml
```

## Support

### Getting Help
- Run `python run.py --help-detailed` for comprehensive help
- Check `logs/roko_extractor.log` for detailed error information
- Verify all configuration settings in `config/config.yaml`
- Test with different RPC endpoints if experiencing issues

### Logging
- Logs are stored in `logs/roko_extractor.log`
- Set `log_level: DEBUG` for detailed debugging information
- Logs include timestamps, error details, and performance metrics

### Configuration Validation
- Use `python test_connection.py` to verify RPC connection
- Check API keys and endpoints in configuration
- Ensure stable internet connection for API access

---

**Version**: 1.0.0  
**Last Updated**: January 2024  
**Author**: Chain Data Extractor Team  
**License**: MIT

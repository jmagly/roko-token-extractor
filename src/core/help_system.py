"""
Comprehensive help system for ROKO Token Data Extractor
"""

import json
from typing import Dict, Any, List


class HelpSystem:
    """Comprehensive help system with examples and documentation."""
    
    def __init__(self):
        """Initialize the help system."""
        self.help_data = self._load_help_data()
    
    def _load_help_data(self) -> Dict[str, Any]:
        """Load comprehensive help data."""
        return {
            "overview": {
                "title": "ROKO Token Data Extractor",
                "description": "A comprehensive tool for extracting detailed token and liquidity pool pricing data for the ROKO token on the Ethereum blockchain using direct RPC API communications.",
                "version": "1.0.0",
                "author": "Chain Data Extractor Team"
            },
            "features": {
                "core": [
                    "Real-time token data extraction from Ethereum blockchain",
                    "Multiple price source integration (CoinGecko, DexScreener, 1inch, Uniswap)",
                    "Uniswap V2/V3 pool detection and analysis",
                    "Complete token holder extraction with Alchemy API",
                    "Historical data tracking with SQLite database",
                    "Advanced analytics for token holders and exchange interactions",
                    "Comprehensive data export (JSON, CSV)",
                    "Real-time monitoring with configurable intervals"
                ],
                "analytics": [
                    "Token holder extraction from Transfer events",
                    "Exchange interaction tracking and analysis",
                    "Concentration metrics (Gini coefficient)",
                    "Top holder analysis and wealth distribution",
                    "User behavior patterns and trading analysis",
                    "Liquidity provider identification",
                    "Exchange usage statistics"
                ],
                "data_sources": [
                    "Ethereum RPC (eth.llamarpc.com)",
                    "CoinGecko API for token prices",
                    "DexScreener API for DEX data",
                    "1inch API for liquidity pricing",
                    "Direct Uniswap pool integration",
                    "Blockchain event logs analysis"
                ]
            },
            "commands": {
                "basic": {
                    "python run.py": "Basic data extraction with console output",
                    "python run.py --export json": "Extract data and export to JSON",
                    "python run.py --export json csv": "Extract data and export to multiple formats"
                },
                "advanced": {
                    "python run.py --analytics": "Include advanced analytics in extraction",
                    "python run.py --analytics --export json": "Full extraction with analytics and export",
                    "python run.py --holders": "Extract complete token holder data (requires Alchemy API key)",
                    "python run.py --monitor": "Start real-time monitoring (30s intervals)",
                    "python run.py --monitor --interval 60": "Real-time monitoring with custom interval",
                    "python run.py --historical 30": "Show historical data summary for 30 days"
                },
                "configuration": {
                    "python run.py --config custom.yaml": "Use custom configuration file",
                    "python run.py --help": "Show this help message"
                }
            },
            "examples": {
                "basic_usage": [
                    "# Basic data extraction",
                    "python run.py",
                    "",
                    "# Export to JSON file",
                    "python run.py --export json",
                    "",
                    "# Export to multiple formats",
                    "python run.py --export json csv"
                ],
                "advanced_usage": [
                    "# Full extraction with analytics",
                    "python run.py --analytics --export json",
                    "",
                    "# Complete holder extraction",
                    "python run.py --holders",
                    "",
                    "# Real-time monitoring",
                    "python run.py --monitor --interval 60",
                    "",
                    "# Historical analysis",
                    "python run.py --historical 7"
                ],
                "configuration": [
                    "# Use custom configuration",
                    "python run.py --config config/production.yaml",
                    "",
                    "# Monitor with custom settings",
                    "python run.py --monitor --interval 30 --config config/high_freq.yaml"
                ]
            },
            "configuration": {
                "file": "config/config.yaml",
                "sections": {
                "ethereum": {
                    "rpc_providers": "List of RPC providers for load balancing",
                    "rpc_url": "Ethereum RPC endpoint URL (legacy single provider)",
                    "api_key": "API key for authentication",
                    "chain_id": "Ethereum chain ID (1 for mainnet)",
                    "gas_limit": "Gas limit for transactions",
                    "load_balancing": "Load balancing configuration"
                },
                    "roko_token": {
                        "address": "ROKO token contract address",
                        "name": "Token name",
                        "symbol": "Token symbol"
                    },
                    "monitoring": {
                        "update_interval": "Default monitoring interval in seconds",
                        "historical_data_days": "Days of historical data to keep",
                        "export_format": "Default export formats",
                        "log_level": "Logging level (DEBUG, INFO, WARNING, ERROR)"
                    },
                    "pools": {
                        "uniswap_v2_factory": "Uniswap V2 factory contract address",
                        "uniswap_v3_factory": "Uniswap V3 factory contract address",
                        "weth_address": "WETH contract address",
                        "usdc_address": "USDC contract address"
                    }
                }
            },
            "output_formats": {
                "json": {
                    "description": "Complete data structure for programmatic use",
                    "location": "data/exports/roko_data_TIMESTAMP.json",
                    "includes": [
                        "Token metadata and pricing",
                        "Pool data and liquidity information",
                        "Historical data and analytics",
                        "Exchange interaction data"
                    ]
                },
                "csv": {
                    "description": "Time-series data for analysis in spreadsheet applications",
                    "location": "data/exports/roko_token_TIMESTAMP.csv",
                    "includes": [
                        "Token data over time",
                        "Price history",
                        "Holder statistics",
                        "Exchange activity"
                    ]
                },
                "database": {
                    "description": "SQLite database for historical tracking",
                    "location": "data/historical/token_data.db",
                    "tables": [
                        "price_history",
                        "holder_history", 
                        "exchange_activity"
                    ]
                }
            },
            "troubleshooting": {
                "common_issues": {
                    "rate_limiting": {
                        "symptom": "429 Client Error: Too Many Requests",
                        "cause": "RPC endpoint rate limiting",
                        "solution": "Wait a few minutes or use a different RPC endpoint"
                    },
                    "connection_error": {
                        "symptom": "Failed to connect to Ethereum node",
                        "cause": "RPC endpoint unavailable or incorrect URL",
                        "solution": "Check RPC URL in configuration or try a different endpoint"
                    },
                    "no_pools_found": {
                        "symptom": "Found 0 ROKO pools",
                        "cause": "Token may not have active liquidity pools",
                        "solution": "This is normal for new or low-liquidity tokens"
                    },
                    "price_data_unavailable": {
                        "symptom": "Price shows as placeholder values",
                        "cause": "Price APIs rate limited or token not supported",
                        "solution": "Check API keys and token address"
                    }
                },
                "debugging": {
                    "enable_debug_logging": "Set log_level to DEBUG in config.yaml",
                    "check_logs": "View logs/roko_extractor.log for detailed information",
                    "test_connection": "Run python test_connection.py to verify RPC connection",
                    "verify_config": "Check config/config.yaml for correct settings"
                }
            },
            "api_reference": {
                "price_sources": {
                    "coingecko": {
                        "url": "https://api.coingecko.com/api/v3/simple/token_price/ethereum",
                        "rate_limit": "10-50 calls/minute",
                        "supports": "USD prices for verified tokens"
                    },
                    "dexscreener": {
                        "url": "https://api.dexscreener.com/latest/dex/tokens/",
                        "rate_limit": "300 calls/minute",
                        "supports": "DEX prices and trading data"
                    },
                    "1inch": {
                        "url": "https://api.1inch.io/v5.0/1/quote",
                        "rate_limit": "100 calls/minute",
                        "supports": "Liquidity-based pricing"
                    },
                    "uniswap": {
                        "method": "Direct pool contract interaction",
                        "rate_limit": "Depends on RPC provider",
                        "supports": "Real-time pool-based pricing"
                    }
                },
                "rpc_endpoints": {
                    "eth_llamarpc": {
                        "url": "https://eth.llamarpc.com",
                        "type": "Public",
                        "rate_limit": "Moderate",
                        "reliability": "Good"
                    },
                    "alchemy": {
                        "url": "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY",
                        "type": "Commercial",
                        "rate_limit": "High",
                        "reliability": "Excellent"
                    }
                }
            }
        }
    
    def get_help(self, section: str = None) -> str:
        """Get help information for a specific section or all sections."""
        if section:
            return self._format_section(section, self.help_data.get(section, {}))
        else:
            return self._format_full_help()
    
    def _format_full_help(self) -> str:
        """Format the complete help information."""
        help_text = f"""
{self.help_data['overview']['title']} v{self.help_data['overview']['version']}
{self.help_data['overview']['description']}

USAGE:
    python run.py [OPTIONS]

OPTIONS:
    -h, --help              Show this help message and exit
    --config CONFIG         Configuration file path (default: config/config.yaml)
    --export FORMATS        Export formats: json, csv (can specify multiple)
    --monitor               Start real-time monitoring
    --interval SECONDS      Monitoring interval in seconds (default: 30)
    --analytics             Include advanced analytics
    --holders               Extract complete token holder data (requires Alchemy API key)
    --historical DAYS       Show historical summary for N days

EXAMPLES:
    # Basic data extraction
    python run.py
    
    # Export to JSON
    python run.py --export json
    
    # Full extraction with analytics
    python run.py --analytics --export json csv
    
    # Extract complete holder data
    python run.py --holders
    
    # Real-time monitoring
    python run.py --monitor --interval 60
    
    # Historical analysis
    python run.py --historical 30

FEATURES:
    • Real-time token data extraction from Ethereum blockchain
    • Multiple price source integration (CoinGecko, DexScreener, 1inch, Uniswap)
    • Uniswap V2/V3 pool detection and analysis
    • Historical data tracking with SQLite database
    • Advanced analytics for token holders and exchange interactions
    • Comprehensive data export (JSON, CSV)
    • Real-time monitoring with configurable intervals

For more detailed information, run:
    python run.py --help detailed
    python run.py --help examples
    python run.py --help configuration
    python run.py --help troubleshooting
"""
        return help_text
    
    def _format_section(self, section: str, data: Dict[str, Any]) -> str:
        """Format a specific help section."""
        if section == "detailed":
            return self._format_detailed_help()
        elif section == "examples":
            return self._format_examples()
        elif section == "configuration":
            return self._format_configuration_help()
        elif section == "troubleshooting":
            return self._format_troubleshooting()
        else:
            return f"Unknown help section: {section}"
    
    def _format_detailed_help(self) -> str:
        """Format detailed help information."""
        return f"""
DETAILED FEATURE OVERVIEW
========================

CORE FEATURES:
{chr(10).join(f"  • {feature}" for feature in self.help_data['features']['core'])}

ANALYTICS FEATURES:
{chr(10).join(f"  • {feature}" for feature in self.help_data['features']['analytics'])}

DATA SOURCES:
{chr(10).join(f"  • {source}" for source in self.help_data['features']['data_sources'])}

OUTPUT FORMATS:
  JSON Export:
    • Location: data/exports/roko_data_TIMESTAMP.json
    • Includes: Complete data structure for programmatic use
    • Contains: Token metadata, pricing, pool data, analytics

  CSV Export:
    • Location: data/exports/roko_token_TIMESTAMP.csv  
    • Includes: Time-series data for analysis
    • Contains: Price history, holder statistics, exchange activity

  Database:
    • Location: data/historical/token_data.db
    • Type: SQLite database
    • Tables: price_history, holder_history, exchange_activity

API REFERENCE:
  Price Sources:
    • CoinGecko: USD prices for verified tokens (10-50 calls/min)
    • DexScreener: DEX prices and trading data (300 calls/min)
    • 1inch: Liquidity-based pricing (100 calls/min)
    • Uniswap: Real-time pool-based pricing (RPC dependent)

  RPC Endpoints:
    • eth.llamarpc.com: Public endpoint, moderate rate limits
    • Alchemy: Commercial endpoint, high rate limits, excellent reliability
"""
    
    def _format_examples(self) -> str:
        """Format examples help."""
        return f"""
USAGE EXAMPLES
=============

BASIC USAGE:
{chr(10).join(self.help_data['examples']['basic_usage'])}

ADVANCED USAGE:
{chr(10).join(self.help_data['examples']['advanced_usage'])}

CONFIGURATION:
{chr(10).join(self.help_data['examples']['configuration'])}

REAL-WORLD SCENARIOS:

1. Daily Price Monitoring:
   python run.py --monitor --interval 3600 --export json
   # Monitor price every hour and export to JSON

2. Research Analysis:
   python run.py --analytics --export json csv --historical 7
   # Full analysis with 7 days of historical data

3. Production Monitoring:
   python run.py --monitor --interval 300 --config config/production.yaml
   # High-frequency monitoring with production settings

4. Data Export for Analysis:
   python run.py --export json csv
   # Export current data for external analysis tools
"""
    
    def _format_configuration_help(self) -> str:
        """Format configuration help."""
        return f"""
CONFIGURATION REFERENCE
======================

Configuration File: {self.help_data['configuration']['file']}

SECTIONS:

Ethereum Settings:
  rpc_url: Ethereum RPC endpoint URL
  api_key: API key for authentication (if required)
  chain_id: Ethereum chain ID (1 for mainnet)
  gas_limit: Gas limit for transactions

ROKO Token Settings:
  address: ROKO token contract address
  name: Token name
  symbol: Token symbol

Monitoring Settings:
  update_interval: Default monitoring interval in seconds
  historical_data_days: Days of historical data to keep
  export_format: Default export formats (json, csv)
  log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

Pool Settings:
  uniswap_v2_factory: Uniswap V2 factory contract address
  uniswap_v3_factory: Uniswap V3 factory contract address
  weth_address: WETH contract address
  usdc_address: USDC contract address

EXAMPLE CONFIGURATION:
```yaml
ethereum:
  # Multiple RPC providers with load balancing
  rpc_providers:
    - name: "eth.llamarpc"
      url: "https://eth.llamarpc.com"
      api_key: ""
      priority: 1
      rate_limit: 100
      timeout: 30
    - name: "alchemy"
      url: "https://eth-mainnet.g.alchemy.com/v2/{API_KEY}"
      api_key: "${ALCHEMY_API_KEY}"
      priority: 2
      rate_limit: 1000
      timeout: 30
    - name: "public"
      url: "https://ethereum.publicnode.com"
      api_key: ""
      priority: 3
      rate_limit: 50
      timeout: 30
  
  # Legacy single RPC (for backward compatibility)
  rpc_url: "https://eth.llamarpc.com"
  api_key: ""
  
  # Chain configuration
  chain_id: 1
  gas_limit: 100000
  
  # Load balancing settings
  load_balancing:
    strategy: "round_robin"  # round_robin, priority, random
    retry_attempts: 3
    retry_delay: 1
    health_check_interval: 60
    max_concurrent_requests: 5

roko_token:
  address: "0x6f222e04f6c53cc688ffb0abe7206aac66a8ff98"
  name: "ROKO"
  symbol: "ROKO"

monitoring:
  update_interval: 30
  historical_data_days: 30
  export_format: ["json", "csv"]
  log_level: "INFO"
```
"""
    
    def _format_troubleshooting(self) -> str:
        """Format troubleshooting help."""
        return f"""
TROUBLESHOOTING GUIDE
====================

COMMON ISSUES:

Rate Limiting (429 Error):
  Symptom: "429 Client Error: Too Many Requests"
  Cause: RPC endpoint rate limiting
  Solution: Wait a few minutes or use a different RPC endpoint

Connection Error:
  Symptom: "Failed to connect to Ethereum node"
  Cause: RPC endpoint unavailable or incorrect URL
  Solution: Check RPC URL in configuration or try a different endpoint

No Pools Found:
  Symptom: "Found 0 ROKO pools"
  Cause: Token may not have active liquidity pools
  Solution: This is normal for new or low-liquidity tokens

Price Data Unavailable:
  Symptom: Price shows as placeholder values
  Cause: Price APIs rate limited or token not supported
  Solution: Check API keys and token address

DEBUGGING STEPS:

1. Enable Debug Logging:
   Set log_level to DEBUG in config.yaml

2. Check Logs:
   View logs/roko_extractor.log for detailed information

3. Test Connection:
   Run: python test_connection.py

4. Verify Configuration:
   Check config/config.yaml for correct settings

5. Test Individual Components:
   Run: python test_pricing.py
   Run: python test_all_features.py

PERFORMANCE OPTIMIZATION:

• Use commercial RPC endpoints for better rate limits
• Increase monitoring intervals for reduced API usage
• Enable caching for frequently accessed data
• Use historical data for analysis instead of real-time queries

SUPPORT:
• Check logs for detailed error information
• Verify all configuration settings
• Test with different RPC endpoints
• Ensure stable internet connection
"""

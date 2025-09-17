#!/usr/bin/env python3
"""
Simple script to update ROKO data for web delivery.
Designed to be called from a cronjob.
"""

import json
import time
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from config.settings import Config

def format_precision(value: float, max_decimals: int = 18) -> str:
    """Format a number with full precision for JSON storage."""
    if value == 0:
        return "0"
    
    # Convert to string with full precision
    formatted = f"{value:.{max_decimals}f}"
    
    # Remove trailing zeros
    formatted = formatted.rstrip('0').rstrip('.')
    
    return formatted

def format_display(value: str, is_currency: bool = False, max_decimals: int = 18) -> str:
    """Format a number for console display with commas and appropriate decimals."""
    try:
        # Convert string back to float for formatting
        num_value = float(value)
        
        if is_currency:
            # For currency, show 2 decimal places with commas
            return f"{num_value:,.2f}"
        else:
            # For other numbers, show full precision with commas
            if '.' in value:
                # Has decimal places
                integer_part, decimal_part = value.split('.')
                # Add commas to integer part
                integer_formatted = f"{int(integer_part):,}"
                return f"{integer_formatted}.{decimal_part}"
            else:
                # No decimal places
                return f"{int(num_value):,}"
    except (ValueError, TypeError):
        return value
from core.enhanced_rpc_client import EnhancedEthereumRPCClient
from core.token_analyzer import ROKOTokenAnalyzer
from core.pool_monitor import UniswapPoolMonitor
from core.price_oracle import PriceOracle

def setup_logging():
    """Setup logging for the script."""
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/roko_update.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def extract_roko_data():
    """Extract comprehensive ROKO data."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting ROKO data extraction...")
        
        # Load configuration
        config = Config("config/config.yaml")
        token_address = config.get_token_address()
        
        # Initialize components
        rpc_client = EnhancedEthereumRPCClient(use_load_balancer=True)
        token_analyzer = ROKOTokenAnalyzer(rpc_client, token_address)
        
        # Pool monitor
        pool_monitor = UniswapPoolMonitor(
            rpc_client=rpc_client,
            roko_address=token_address,
            uniswap_v2_factory=config.get_uniswap_v2_factory(),
            uniswap_v3_factory=config.get_uniswap_v3_factory(),
            weth_address=config.get_weth_address()
        )
        
        # 1. Token metadata and pricing
        logger.info("Extracting token metadata...")
        token_metadata = token_analyzer.get_token_metadata()
        
        # Get comprehensive pricing data (once)
        from core.price_oracle import PriceOracle
        oracle = PriceOracle()
        comprehensive_pricing = oracle.get_comprehensive_pricing(token_address, config.get_weth_address(), rpc_client)
        
        # Get token symbol for display
        token_symbol = config.get_token_symbol()
        
        # Calculate market cap using circulating supply (excluding treasury wallets)
        usd_per_token = comprehensive_pricing.get('usd_per_token', 0)
        circulating_supply = token_analyzer.get_circulating_supply()
        circulating_supply_formatted = circulating_supply / (10 ** token_metadata.get('decimals', 18))
        market_cap = usd_per_token * circulating_supply_formatted if usd_per_token and circulating_supply_formatted else 0
        
        # Calculate treasury holdings for detailed reporting
        total_supply = token_metadata.get('total_supply', 0)
        total_supply_formatted = total_supply / (10 ** token_metadata.get('decimals', 18)) if total_supply > 0 else 0
        treasury_holdings = total_supply_formatted - circulating_supply_formatted if total_supply_formatted > 0 else 0
        
        pricing_data = {
            'token_eth_ratio': comprehensive_pricing.get('token_eth_ratio', 0),
            'eth_per_token': comprehensive_pricing.get('eth_per_token', 0),
            'usd_per_token': comprehensive_pricing.get('usd_per_token', 0),
            'eth_price_usd': comprehensive_pricing.get('eth_price_usd', 0),
            'market_cap_usd': market_cap,
            'price_source': 'chain_data'
        }
        
        # 2. Pool data
        logger.info("Extracting pool data...")
        pools = pool_monitor.find_roko_pools()
        pool_data = []
        total_tvl = 0
        total_volume_24h = 0
        
        # Get ETH price once to avoid redundant calculations
        eth_price = comprehensive_pricing.get('eth_price_usd', 0)
        
        for pool in pools:
            try:
                # Get pool reserves and basic info
                reserves = pool_monitor.get_pool_reserves(pool['address'])
                tvl = pool_monitor.get_pool_tvl(pool['address'])
                volume = pool_monitor.get_pool_volume(pool['address'])
                
                # Get token decimals (assuming 18 for both tokens in Uniswap V2)
                token_decimals = 18
                
                pool_info = {
                    'address': pool['address'],
                    'token0': pool.get('token0', 'N/A'),
                    'token1': pool.get('token1', 'N/A'),
                    'roko_is_token0': pool.get('roko_is_token0', False),
                    'reserves': {
                        'reserve0': reserves['reserve0'] / (10 ** token_decimals),
                        'reserve1': reserves['reserve1'] / (10 ** token_decimals)
                    },
                    'tvl_usd': tvl,
                    'volume_24h_usd': volume.get('volume_24h_usd', 0),
                    'volume_7d_usd': volume.get('volume_7d_usd', 0),
                    'volume_30d_usd': volume.get('volume_30d_usd', 0),
                    'volume_24h_eth': volume.get('volume_24h_eth', 0),
                    'volume_7d_eth': volume.get('volume_7d_eth', 0),
                    'volume_30d_eth': volume.get('volume_30d_eth', 0)
                }
                
                pool_data.append(pool_info)
                total_tvl += tvl
                total_volume_24h += volume.get('volume_24h_usd', 0)
                
            except Exception as e:
                logger.error(f"Error processing pool {pool['address']}: {e}")
                continue
        
        # 3. Compile comprehensive data with full precision
        comprehensive_data = {
            'timestamp': int(time.time()),
            'datetime': datetime.now().isoformat(),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'token': {
                'name': token_metadata.get('name', 'N/A'),
                'symbol': token_metadata.get('symbol', 'N/A'),
                'address': token_metadata.get('address', 'N/A'),
                'decimals': token_metadata.get('decimals', 'N/A'),
                'total_supply': format_precision(total_supply_formatted, 18),
                'circulating_supply': format_precision(circulating_supply_formatted, 18),
                'treasury_holdings': format_precision(treasury_holdings, 18),
                'treasury_percentage': format_precision((treasury_holdings / total_supply_formatted * 100) if total_supply_formatted > 0 else 0, 2)
            },
            'pricing': {
                'token_eth_ratio': format_precision(pricing_data.get('token_eth_ratio', 0), 18),
                'eth_per_token': format_precision(pricing_data.get('eth_per_token', 0), 18),
                'usd_per_token': format_precision(pricing_data.get('usd_per_token', 0), 18),
                'eth_price_usd': format_precision(pricing_data.get('eth_price_usd', 0), 2),
                'market_cap_usd': format_precision(pricing_data.get('market_cap_usd', 0), 2),
                'total_market_cap_usd': format_precision((usd_per_token * total_supply_formatted) if usd_per_token and total_supply_formatted > 0 else 0, 2),
                'price_source': pricing_data.get('price_source', 'unknown')
            },
            'tvl': {
                'total_tvl_usd': format_precision(total_tvl, 2),
                'pools_count': len(pool_data),
                'pools': pool_data
            },
            'volume': {
                'volume_24h_usd': format_precision(total_volume_24h, 2),
                'volume_7d_usd': format_precision(sum(p.get('volume_7d_usd', 0) for p in pool_data), 2),
                'volume_30d_usd': format_precision(sum(p.get('volume_30d_usd', 0) for p in pool_data), 2),
                'volume_24h_eth': format_precision(sum(p.get('volume_24h_eth', 0) for p in pool_data), 18),
                'volume_7d_eth': format_precision(sum(p.get('volume_7d_eth', 0) for p in pool_data), 18),
                'volume_30d_eth': format_precision(sum(p.get('volume_30d_eth', 0) for p in pool_data), 18)
            },
            'summary': {
                'status': 'success',
                'extraction_time': datetime.now().isoformat(),
                'data_quality': 'high' if total_tvl > 0 else 'medium'
            }
        }
        
        logger.info("Data extraction completed successfully")
        return comprehensive_data
        
    except Exception as e:
        logger.error(f"Error in data extraction: {e}")
        return {
            'timestamp': int(time.time()),
            'datetime': datetime.now().isoformat(),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'error': str(e),
            'status': 'error'
        }

def save_web_data(data):
    """Save data to web delivery directory."""
    logger = logging.getLogger(__name__)
    
    try:
        # Create web delivery directory
        web_dir = Path("web_delivery")
        web_dir.mkdir(exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"roko_data_{timestamp}.json"
        filepath = web_dir / filename
        
        # Save main data file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Also save as 'latest.json' for easy access
        latest_filepath = web_dir / "latest.json"
        with open(latest_filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Web data saved to: {filepath}")
        logger.info(f"Latest data saved to: {latest_filepath}")
        
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Error saving web data: {e}")
        return ""

def export_price_data(data: Dict[str, Any], token_symbol: str, logger):
    """Export price data to a dedicated file."""
    try:
        # Create data/exports directory if it doesn't exist
        export_dir = Path("data/exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract pricing data
        pricing = data.get('pricing', {})
        token = data.get('token', {})
        
        # Create price data structure
        price_data = {
            'timestamp': data.get('timestamp', int(time.time())),
            'datetime': data.get('datetime', datetime.now().isoformat()),
            'token': {
                'name': token.get('name', 'N/A'),
                'symbol': token.get('symbol', 'N/A'),
                'address': token.get('address', 'N/A'),
                'decimals': token.get('decimals', 'N/A'),
                'total_supply': token.get('total_supply', 'N/A'),
                'circulating_supply': token.get('circulating_supply', 'N/A'),
                'treasury_holdings': token.get('treasury_holdings', 'N/A'),
                'treasury_percentage': token.get('treasury_percentage', 'N/A')
            },
            'pricing': {
                'token_eth_ratio': pricing.get('token_eth_ratio', 'N/A'),
                'eth_per_token': pricing.get('eth_per_token', 'N/A'),
                'usd_per_token': pricing.get('usd_per_token', 'N/A'),
                'eth_price_usd': pricing.get('eth_price_usd', 'N/A'),
                'market_cap_usd': pricing.get('market_cap_usd', 'N/A'),
                'total_market_cap_usd': pricing.get('total_market_cap_usd', 'N/A'),
                'price_source': pricing.get('price_source', 'unknown')
            }
        }
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"roko_price_data_{timestamp}.json"
        filepath = export_dir / filename
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(price_data, f, indent=2)
        
        logger.info(f"Price data exported to: {filepath}")
        
        # Also create a CSV version for easy viewing
        csv_filename = f"roko_price_data_{timestamp}.csv"
        csv_filepath = export_dir / csv_filename
        
        with open(csv_filepath, 'w') as f:
            f.write("Metric,Value\n")
            f.write(f"Timestamp,{price_data['datetime']}\n")
            f.write(f"Token Name,{price_data['token']['name']}\n")
            f.write(f"Token Symbol,{price_data['token']['symbol']}\n")
            f.write(f"Token Address,{price_data['token']['address']}\n")
            f.write(f"Decimals,{price_data['token']['decimals']}\n")
            f.write(f"Total Supply,{price_data['token']['total_supply']}\n")
            f.write(f"Circulating Supply,{price_data['token'].get('circulating_supply', 'N/A')}\n")
            f.write(f"Treasury Holdings,{price_data['token'].get('treasury_holdings', 'N/A')}\n")
            f.write(f"Treasury Percentage,{price_data['token'].get('treasury_percentage', 'N/A')}%\n")
            f.write(f"{token_symbol}:ETH Ratio,{price_data['pricing']['token_eth_ratio']}\n")
            f.write(f"ETH per {token_symbol},{price_data['pricing']['eth_per_token']}\n")
            f.write(f"USD per {token_symbol},{price_data['pricing']['usd_per_token']}\n")
            f.write(f"ETH Price (USD),{price_data['pricing']['eth_price_usd']}\n")
            f.write(f"Market Cap (USD),{price_data['pricing']['market_cap_usd']}\n")
            f.write(f"Total Market Cap (USD),{price_data['pricing'].get('total_market_cap_usd', 'N/A')}\n")
            f.write(f"Price Source,{price_data['pricing']['price_source']}\n")
        
        logger.info(f"Price data CSV exported to: {csv_filepath}")
        
    except Exception as e:
        logger.error(f"Error exporting price data: {e}")

def main():
    """Main function."""
    logger = setup_logging()
    
    try:
        logger.info("="*60)
        logger.info("ROKO Data Update Script Started")
        logger.info("="*60)
        
        # Get token symbol for display
        config = Config()
        token_symbol = config.get_token_symbol()
        
        # Extract data
        data = extract_roko_data()
        
        # Save to web directory
        filepath = save_web_data(data)
        
        # Export price data
        export_price_data(data, token_symbol, logger)
        
        if filepath:
            logger.info("SUCCESS: Data update completed successfully")
            
            # Log summary
            if 'token' in data and 'error' not in data:
                token = data['token']
                pricing = data.get('pricing', {})
                tvl = data.get('tvl', {})
                volume = data.get('volume', {})
                
                logger.info(f"Token: {token.get('name', 'N/A')} ({token.get('symbol', 'N/A')})")
                logger.info(f"Total Supply: {format_display(token.get('total_supply', '0'))} {token_symbol}")
                logger.info(f"Circulating Supply: {format_display(token.get('circulating_supply', '0'))} {token_symbol}")
                logger.info(f"Treasury Holdings: {format_display(token.get('treasury_holdings', '0'))} {token_symbol} ({token.get('treasury_percentage', '0')}%)")
                logger.info(f"{token_symbol}:ETH Ratio: {format_display(pricing.get('token_eth_ratio', '0'))}")
                logger.info(f"Price: {format_display(pricing.get('eth_per_token', '0'))} ETH per {token_symbol}")
                logger.info(f"Price: ${format_display(pricing.get('usd_per_token', '0'))} USD per {token_symbol}")
                logger.info(f"Market Cap: ${format_display(pricing.get('market_cap_usd', '0'), is_currency=True)}")
                logger.info(f"Total Market Cap: ${format_display(pricing.get('total_market_cap_usd', '0'), is_currency=True)}")
                logger.info(f"TVL: ${format_display(tvl.get('total_tvl_usd', '0'), is_currency=True)}")
                logger.info(f"24h Volume: ${format_display(volume.get('volume_24h_usd', '0'), is_currency=True)}")
                logger.info(f"Pools: {tvl.get('pools_count', 0)}")
            else:
                logger.error("ERROR: Data extraction failed")
        else:
            logger.error("ERROR: Failed to save web data")
        
        logger.info("="*60)
        
        # Exit with appropriate code
        if 'error' in data:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

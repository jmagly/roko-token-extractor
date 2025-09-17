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

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from config.settings import Config
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
        roko_address = config.get_roko_address()
        
        # Initialize components
        rpc_client = EnhancedEthereumRPCClient(use_load_balancer=True)
        token_analyzer = ROKOTokenAnalyzer(rpc_client, roko_address)
        
        # Pool monitor
        pool_monitor = UniswapPoolMonitor(
            rpc_client=rpc_client,
            roko_address=roko_address,
            uniswap_v2_factory="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
            uniswap_v3_factory="0x1F98431c8aD98523631AE4a59f267346ea31F984",
            weth_address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        )
        
        # 1. Token metadata and pricing
        logger.info("Extracting token metadata...")
        token_metadata = token_analyzer.get_token_metadata()
        
        # Get pricing data
        market_cap = token_analyzer.get_market_cap()
        holder_count = token_analyzer.get_holder_count()
        
        # Get comprehensive pricing data
        from core.price_oracle import PriceOracle
        oracle = PriceOracle()
        comprehensive_pricing = oracle.get_comprehensive_pricing(roko_address, "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", rpc_client)
        
        pricing_data = {
            'roko_eth_ratio': comprehensive_pricing.get('roko_eth_ratio', 0),
            'eth_per_roko': comprehensive_pricing.get('eth_per_roko', 0),
            'usd_per_roko': comprehensive_pricing.get('usd_per_roko', 0),
            'eth_price_usd': comprehensive_pricing.get('eth_price_usd', 0),
            'market_cap_usd': market_cap,
            'price_source': comprehensive_pricing.get('price_source', 'unknown')
        }
        
        # 2. Pool data
        logger.info("Extracting pool data...")
        pools = pool_monitor.find_roko_pools()
        pool_data = []
        total_liquidity = 0
        total_volume_24h = 0
        
        for pool in pools:
            try:
                # Get pool reserves and basic info
                reserves = pool_monitor.get_pool_reserves(pool['address'])
                liquidity = pool_monitor.get_pool_liquidity(pool['address'])
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
                    'liquidity_usd': liquidity,
                    'volume_24h_usd': volume.get('volume_24h_usd', 0),
                    'volume_7d_usd': volume.get('volume_7d_usd', 0),
                    'volume_30d_usd': volume.get('volume_30d_usd', 0),
                    'volume_24h_eth': volume.get('volume_24h_eth', 0),
                    'volume_7d_eth': volume.get('volume_7d_eth', 0),
                    'volume_30d_eth': volume.get('volume_30d_eth', 0)
                }
                
                pool_data.append(pool_info)
                total_liquidity += liquidity
                total_volume_24h += volume.get('volume_24h_usd', 0)
                
            except Exception as e:
                logger.error(f"Error processing pool {pool['address']}: {e}")
                continue
        
        # 3. Compile comprehensive data
        comprehensive_data = {
            'timestamp': int(time.time()),
            'datetime': datetime.now().isoformat(),
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'token': {
                'name': token_metadata.get('name', 'N/A'),
                'symbol': token_metadata.get('symbol', 'N/A'),
                'address': token_metadata.get('address', 'N/A'),
                'decimals': token_metadata.get('decimals', 'N/A'),
                'total_supply': token_metadata.get('total_supply', 0) / (10 ** token_metadata.get('decimals', 18)) if token_metadata.get('total_supply', 0) > 0 else 0,
                'holders': holder_count
            },
            'pricing': {
                'roko_eth_ratio': pricing_data.get('roko_eth_ratio', 0),
                'eth_per_roko': pricing_data.get('eth_per_roko', 0),
                'usd_per_roko': pricing_data.get('usd_per_roko', 0),
                'eth_price_usd': pricing_data.get('eth_price_usd', 0),
                'market_cap_usd': pricing_data.get('market_cap_usd', 0),
                'price_source': pricing_data.get('price_source', 'unknown')
            },
            'liquidity': {
                'total_liquidity_usd': total_liquidity,
                'pools_count': len(pool_data),
                'pools': pool_data
            },
            'volume': {
                'volume_24h_usd': total_volume_24h,
                'volume_7d_usd': sum(p.get('volume_7d_usd', 0) for p in pool_data),
                'volume_30d_usd': sum(p.get('volume_30d_usd', 0) for p in pool_data),
                'volume_24h_eth': sum(p.get('volume_24h_eth', 0) for p in pool_data),
                'volume_7d_eth': sum(p.get('volume_7d_eth', 0) for p in pool_data),
                'volume_30d_eth': sum(p.get('volume_30d_eth', 0) for p in pool_data)
            },
            'summary': {
                'status': 'success',
                'extraction_time': datetime.now().isoformat(),
                'data_quality': 'high' if total_liquidity > 0 else 'medium'
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

def main():
    """Main function."""
    logger = setup_logging()
    
    try:
        logger.info("="*60)
        logger.info("ROKO Data Update Script Started")
        logger.info("="*60)
        
        # Extract data
        data = extract_roko_data()
        
        # Save to web directory
        filepath = save_web_data(data)
        
        if filepath:
            logger.info("SUCCESS: Data update completed successfully")
            
            # Log summary
            if 'token' in data and 'error' not in data:
                token = data['token']
                pricing = data.get('pricing', {})
                liquidity = data.get('liquidity', {})
                volume = data.get('volume', {})
                
                logger.info(f"Token: {token.get('name', 'N/A')} ({token.get('symbol', 'N/A')})")
                logger.info(f"ROKO:ETH Ratio: {pricing.get('roko_eth_ratio', 0):.2f}")
                logger.info(f"Price: {pricing.get('eth_per_roko', 0):.10f} ETH per ROKO")
                logger.info(f"Price: ${pricing.get('usd_per_roko', 0):.6f} USD per ROKO")
                logger.info(f"Market Cap: ${pricing.get('market_cap_usd', 0):,.2f}")
                logger.info(f"Holders: {token.get('holders', 'N/A')}")
                logger.info(f"Liquidity: ${liquidity.get('total_liquidity_usd', 0):,.2f}")
                logger.info(f"24h Volume: ${volume.get('volume_24h_usd', 0):,.2f}")
                logger.info(f"Pools: {liquidity.get('pools_count', 0)}")
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

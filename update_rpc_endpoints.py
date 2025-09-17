#!/usr/bin/env python3
"""
Script to update RPC endpoints from ChainList.org
Run this weekly to keep RPC endpoints up to date
"""

import sys
import json
import logging
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.rpc_fetcher import RPCFetcher
from config.settings import Config

def update_rpc_config():
    """Update the RPC configuration with fresh endpoints from ChainList."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting RPC endpoint update...")
        
        # Initialize fetcher
        fetcher = RPCFetcher()
        
        # Get fresh RPC endpoints
        rpcs = fetcher.get_ethereum_rpcs()
        
        if not rpcs:
            logger.error("No RPC endpoints found")
            return False
        
        # Load current config
        config = Config("config/config.yaml")
        
        # Clear ignore list when refreshing RPC endpoints
        from core.rpc_load_balancer import RPCLoadBalancer
        from config.settings import Config as ConfigClass
        
        # Create a temporary load balancer to clear ignore list
        temp_config = ConfigClass("config/config.yaml")
        temp_load_balancer = RPCLoadBalancer(
            [],  # Empty providers list since we're just clearing ignore list
            temp_config.ethereum.get('load_balancing', {})
        )
        temp_load_balancer.clear_ignore_list()
        logger.info("Cleared RPC ignore list due to endpoint refresh")
        
        # Update config with metadata (no need to store providers anymore)
        config_data = config._config.copy()
        
        # Add metadata to chainlist section
        if 'chainlist' not in config_data['ethereum']:
            config_data['ethereum']['chainlist'] = {}
        
        config_data['ethereum']['chainlist']['last_updated'] = fetcher.get_cache_info().get('fetched_at', 'unknown')
        config_data['ethereum']['chainlist']['total_providers'] = len(rpcs)
        config_data['ethereum']['chainlist']['cached_providers'] = len(rpcs)
        
        # Save updated config
        with open("config/config.yaml", 'w') as f:
            import yaml
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        logger.info(f"Updated config with ChainList metadata")
        logger.info(f"Total providers available: {len(rpcs)}")
        logger.info(f"Top providers: {', '.join([rpc['name'] for rpc in rpcs[:5]])}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating RPC config: {e}")
        return False

def main():
    """Main function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/rpc_update.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=" * 60)
        logger.info("RPC Endpoint Update Script")
        logger.info("=" * 60)
        
        success = update_rpc_config()
        
        if success:
            logger.info("SUCCESS: RPC endpoints updated successfully")
        else:
            logger.error("ERROR: Failed to update RPC endpoints")
            sys.exit(1)
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

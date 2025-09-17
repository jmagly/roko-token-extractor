#!/usr/bin/env python3
"""
Script to update RPC endpoints from ChainList.org with health testing and backup
Run this weekly to keep RPC endpoints up to date
"""

import sys
import json
import logging
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.rpc_fetcher import RPCFetcher
from utils.rpc_ignore_list import RPCIgnoreList
from config.settings import Config

def test_rpc_endpoint(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Test an RPC endpoint for basic functionality.
    
    Args:
        url: RPC endpoint URL
        timeout: Request timeout in seconds
        
    Returns:
        Dict with test results including success status, response time, and error details
    """
    test_result = {
        'url': url,
        'success': False,
        'response_time_ms': None,
        'error': None,
        'error_code': None,
        'tested_at': datetime.now().isoformat()
    }
    
    try:
        start_time = time.time()
        
        # Test basic connectivity with eth_chainId
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_chainId",
            "params": [],
            "id": 1
        }
        
        response = requests.post(
            url, 
            json=payload, 
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
        
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        test_result['response_time_ms'] = round(response_time, 2)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if 'result' in data and data['result'] == '0x1':  # Ethereum mainnet
                    test_result['success'] = True
                else:
                    test_result['error'] = f"Invalid chain ID response: {data.get('result', 'unknown')}"
            except json.JSONDecodeError:
                test_result['error'] = "Invalid JSON response"
        else:
            test_result['error'] = f"HTTP {response.status_code}: {response.text[:100]}"
            test_result['error_code'] = response.status_code
            
    except requests.exceptions.Timeout:
        test_result['error'] = f"Request timeout after {timeout}s"
    except requests.exceptions.ConnectionError:
        test_result['error'] = "Connection error"
    except requests.exceptions.RequestException as e:
        test_result['error'] = f"Request error: {str(e)}"
    except Exception as e:
        test_result['error'] = f"Unexpected error: {str(e)}"
    
    return test_result

def backup_chainlist_data(rpcs: List[Dict[str, Any]], backup_dir: str = "data/backups") -> str:
    """
    Create a backup of ChainList data.
    
    Args:
        rpcs: List of RPC endpoints
        backup_dir: Directory to store backups
        
    Returns:
        Path to the backup file
    """
    backup_path = Path(backup_dir)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"chainlist_backup_{timestamp}.json"
    
    backup_data = {
        'fetched_at': datetime.now().isoformat(),
        'total_providers': len(rpcs),
        'providers': rpcs
    }
    
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    return str(backup_file)

def test_all_rpc_endpoints(rpcs: List[Dict[str, Any]], max_concurrent: int = 5) -> Dict[str, Any]:
    """
    Test all RPC endpoints for health and performance.
    
    Args:
        rpcs: List of RPC endpoints
        max_concurrent: Maximum concurrent tests
        
    Returns:
        Dict with test results summary
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Testing {len(rpcs)} RPC endpoints...")
    
    test_results = []
    successful_endpoints = []
    failed_endpoints = []
    
    for i, rpc in enumerate(rpcs):
        logger.info(f"Testing {i+1}/{len(rpcs)}: {rpc['name']} ({rpc['url']})")
        
        result = test_rpc_endpoint(rpc['url'])
        test_results.append(result)
        
        if result['success']:
            successful_endpoints.append(rpc)
            logger.info(f"  [OK] Success ({result['response_time_ms']}ms)")
        else:
            failed_endpoints.append(rpc)
            logger.warning(f"  [FAIL] Failed: {result['error']}")
        
        # Small delay to avoid overwhelming endpoints
        time.sleep(0.1)
    
    # Update ignore list with failed endpoints
    ignore_list = RPCIgnoreList()
    for rpc in failed_endpoints:
        ignore_list.add_failing_endpoint(
            rpc['url'], 
            error_code=500,  # Generic error code for health test failures
            error_message="Health test failed"
        )
    
    summary = {
        'total_tested': len(rpcs),
        'successful': len(successful_endpoints),
        'failed': len(failed_endpoints),
        'success_rate': len(successful_endpoints) / len(rpcs) * 100,
        'test_results': test_results,
        'successful_endpoints': successful_endpoints,
        'failed_endpoints': failed_endpoints
    }
    
    logger.info(f"Health testing complete: {summary['successful']}/{summary['total_tested']} endpoints working ({summary['success_rate']:.1f}%)")
    
    return summary

def update_rpc_config():
    """Update the RPC configuration with fresh endpoints from ChainList, including health testing."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting enhanced RPC endpoint update...")
        
        # Initialize fetcher
        fetcher = RPCFetcher()
        
        # Get fresh RPC endpoints
        rpcs = fetcher.get_ethereum_rpcs()
        
        if not rpcs:
            logger.error("No RPC endpoints found")
            return False
        
        # Create backup of ChainList data
        backup_file = backup_chainlist_data(rpcs)
        logger.info(f"Created backup: {backup_file}")
        
        # Test all RPC endpoints
        test_summary = test_all_rpc_endpoints(rpcs)
        
        # Load current config
        config = Config("config/config.yaml")
        
        # Clear ignore list when refreshing RPC endpoints (but keep health test results)
        from core.rpc_load_balancer import RPCLoadBalancer
        from config.settings import Config as ConfigClass
        
        # Create a temporary load balancer to clear ignore list
        temp_config = ConfigClass("config/config.yaml")
        temp_load_balancer = RPCLoadBalancer(
            [],  # Empty providers list since we're just clearing ignore list
            temp_config.ethereum.get('load_balancing', {})
        )
        temp_load_balancer.clear_ignore_list()
        temp_load_balancer.clear_rate_limit_list()
        logger.info("Cleared RPC ignore list and rate limit list due to endpoint refresh")
        
        # Update config with metadata and test results
        config_data = config._config.copy()
        
        # Add metadata to chainlist section
        if 'chainlist' not in config_data['ethereum']:
            config_data['ethereum']['chainlist'] = {}
        
        config_data['ethereum']['chainlist']['last_updated'] = fetcher.get_cache_info().get('fetched_at', 'unknown')
        config_data['ethereum']['chainlist']['total_providers'] = len(rpcs)
        config_data['ethereum']['chainlist']['cached_providers'] = len(rpcs)
        config_data['ethereum']['chainlist']['health_tested'] = datetime.now().isoformat()
        config_data['ethereum']['chainlist']['successful_providers'] = test_summary['successful']
        config_data['ethereum']['chainlist']['failed_providers'] = test_summary['failed']
        config_data['ethereum']['chainlist']['success_rate'] = round(test_summary['success_rate'], 1)
        config_data['ethereum']['chainlist']['backup_file'] = backup_file
        
        # Save updated config
        with open("config/config.yaml", 'w') as f:
            import yaml
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        # Save detailed test results
        test_results_file = Path("data") / f"rpc_health_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_results_file.parent.mkdir(exist_ok=True)
        
        with open(test_results_file, 'w') as f:
            json.dump(test_summary, f, indent=2)
        
        logger.info(f"Updated config with ChainList metadata and health test results")
        logger.info(f"Total providers available: {len(rpcs)}")
        logger.info(f"Successful providers: {test_summary['successful']}")
        logger.info(f"Failed providers: {test_summary['failed']}")
        logger.info(f"Success rate: {test_summary['success_rate']:.1f}%")
        logger.info(f"Test results saved to: {test_results_file}")
        logger.info(f"Backup saved to: {backup_file}")
        
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

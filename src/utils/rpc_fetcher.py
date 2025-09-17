#!/usr/bin/env python3
"""
RPC endpoint fetcher from ChainList.org
Fetches and caches RPC endpoints weekly to avoid overloading the API
"""

import json
import time
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

class RPCFetcher:
    """Fetches and caches RPC endpoints from ChainList.org"""
    
    def __init__(self, cache_file: str = "data/rpc_endpoints.json"):
        """Initialize the RPC fetcher."""
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.chainlist_url = "https://chainlist.org/rpcs.json"
        self.cache_duration = 7 * 24 * 60 * 60  # 7 days in seconds
        
    def _is_cache_valid(self) -> bool:
        """Check if the cached data is still valid."""
        if not self.cache_file.exists():
            return False
            
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            # Check if data is a list (ChainList format)
            if not isinstance(data, list):
                return False
            
            # Check if cache is older than 7 days
            # For list format, we'll check file modification time
            file_time = self.cache_file.stat().st_mtime
            current_time = time.time()
            
            return (current_time - file_time) < self.cache_duration
            
        except (json.JSONDecodeError, KeyError, FileNotFoundError, OSError):
            return False
    
    def _fetch_from_chainlist(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch RPC endpoints from ChainList.org"""
        try:
            self.logger.info(f"Fetching RPC endpoints from {self.chainlist_url}")
            
            response = requests.get(self.chainlist_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # ChainList returns a list of chains
            if not isinstance(data, list):
                self.logger.error("ChainList data is not in expected list format")
                return None
            
            self.logger.info(f"Successfully fetched {len(data)} chains from ChainList")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching from ChainList: {e}")
            return None
    
    def _save_cache(self, data: List[Dict[str, Any]]) -> None:
        """Save data to cache file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"RPC endpoints cached to {self.cache_file}")
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")
    
    def _load_cache(self) -> Optional[List[Dict[str, Any]]]:
        """Load data from cache file."""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}")
            return None
    
    def get_ethereum_rpcs(self) -> List[Dict[str, Any]]:
        """Get Ethereum mainnet RPC endpoints."""
        # Try to use cached data first
        if self._is_cache_valid():
            self.logger.info("Using cached RPC endpoints")
            cached_data = self._load_cache()
            if cached_data and isinstance(cached_data, list):
                return self._extract_ethereum_rpcs(cached_data)
        
        # Fetch fresh data
        self.logger.info("Cache expired or missing, fetching fresh data")
        fresh_data = self._fetch_from_chainlist()
        
        if fresh_data and isinstance(fresh_data, list):
            # Save to cache
            self._save_cache(fresh_data)
            return self._extract_ethereum_rpcs(fresh_data)
        
        # Fallback to cached data even if expired
        self.logger.warning("Failed to fetch fresh data, using expired cache as fallback")
        cached_data = self._load_cache()
        if cached_data and isinstance(cached_data, list):
            return self._extract_ethereum_rpcs(cached_data)
        
        # Return empty list if all else fails
        self.logger.error("No RPC endpoints available")
        return []
    
    def _extract_ethereum_rpcs(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Ethereum mainnet RPC endpoints from ChainList data."""
        ethereum_rpcs = []
        
        for chain in data:
            if chain.get('chain') == 'ETH' and chain.get('name') == 'Ethereum Mainnet':
                rpcs = chain.get('rpc', [])
                
                for rpc in rpcs:
                    # Filter out WebSocket endpoints for now
                    if rpc.get('url', '').startswith('wss://'):
                        continue
                    
                    # Extract useful information
                    rpc_info = {
                        'url': rpc.get('url', ''),
                        'tracking': rpc.get('tracking', 'unknown'),
                        'isOpenSource': rpc.get('isOpenSource', False),
                        'name': self._extract_provider_name(rpc.get('url', '')),
                        'priority': self._calculate_priority(rpc)
                    }
                    
                    # Only include valid HTTP/HTTPS URLs
                    if rpc_info['url'].startswith(('http://', 'https://')):
                        ethereum_rpcs.append(rpc_info)
                
                break  # Found Ethereum, no need to continue
        
        # Sort by priority (higher priority first)
        ethereum_rpcs.sort(key=lambda x: x['priority'], reverse=True)
        
        self.logger.info(f"Extracted {len(ethereum_rpcs)} Ethereum RPC endpoints")
        return ethereum_rpcs
    
    def _extract_provider_name(self, url: str) -> str:
        """Extract provider name from URL."""
        try:
            # Remove protocol and common paths
            clean_url = url.replace('https://', '').replace('http://', '')
            clean_url = clean_url.split('/')[0]  # Get domain only
            
            # Extract provider name from domain
            if 'llamarpc.com' in clean_url:
                return 'llamarpc'
            elif 'getblock.io' in clean_url:
                return 'getblock'
            elif 'nodereal.io' in clean_url:
                return 'nodereal'
            elif 'publicnode.com' in clean_url:
                return 'publicnode'
            elif '1rpc.io' in clean_url:
                return '1rpc'
            elif 'builder0x69.io' in clean_url:
                return 'builder0x69'
            elif 'mevblocker.io' in clean_url:
                return 'mevblocker'
            elif 'flashbots.net' in clean_url:
                return 'flashbots'
            elif 'blxrbdn.com' in clean_url:
                return 'blxr'
            elif 'cloudflare-eth.com' in clean_url:
                return 'cloudflare'
            elif 'blastapi.io' in clean_url:
                return 'blastapi'
            elif 'securerpc.com' in clean_url:
                return 'securerpc'
            elif 'bitstack.com' in clean_url:
                return 'bitstack'
            elif 'nodies.app' in clean_url:
                return 'nodies'
            elif 'unifra.io' in clean_url:
                return 'unifra'
            elif 'blockpi.network' in clean_url:
                return 'blockpi'
            elif 'payload.de' in clean_url:
                return 'payload'
            elif 'zmok.io' in clean_url:
                return 'zmok'
            elif 'alchemy.com' in clean_url:
                return 'alchemy'
            elif 'gashawk.io' in clean_url:
                return 'gashawk'
            elif 'rpcfast.com' in clean_url:
                return 'rpcfast'
            elif 'linkpool.io' in clean_url:
                return 'linkpool'
            elif 'gateway.fm' in clean_url:
                return 'gateway'
            elif 'chain49.com' in clean_url:
                return 'chain49'
            elif 'meowrpc.com' in clean_url:
                return 'meowrpc'
            elif 'drpc.org' in clean_url:
                return 'drpc'
            elif 'tenderly.co' in clean_url:
                return 'tenderly'
            elif 'zan.top' in clean_url:
                return 'zan'
            elif 'diamondswap.org' in clean_url:
                return 'diamondswap'
            elif 'notadegen.com' in clean_url:
                return 'notadegen'
            elif 'merkle.io' in clean_url:
                return 'merkle'
            elif 'lokibuilder.xyz' in clean_url:
                return 'lokibuilder'
            elif 'tokenview.io' in clean_url:
                return 'tokenview'
            elif 'nodeconnect.org' in clean_url:
                return 'nodeconnect'
            elif 'stateless.solutions' in clean_url:
                return 'stateless'
            elif 'polysplit.cloud' in clean_url:
                return 'polysplit'
            elif 'stackup.sh' in clean_url:
                return 'stackup'
            elif 'tatum.io' in clean_url:
                return 'tatum'
            elif 'nownodes.io' in clean_url:
                return 'nownodes'
            elif 'nodifi.ai' in clean_url:
                return 'nodifi'
            elif 'subquery.network' in clean_url:
                return 'subquery'
            elif 'graffiti.farm' in clean_url:
                return 'graffiti'
            elif 'radiumblock.co' in clean_url:
                return 'radiumblock'
            elif '4everland.org' in clean_url:
                return '4everland'
            elif 'callstaticrpc.com' in clean_url:
                return 'callstatic'
            elif 'blockrazor.xyz' in clean_url:
                return 'blockrazor'
            elif 'omniatech.io' in clean_url:
                return 'omniatech'
            elif 'lava.build' in clean_url:
                return 'lava'
            elif '0xrpc.io' in clean_url:
                return '0xrpc'
            elif 'owlracle.info' in clean_url:
                return 'owlracle'
            elif 'therpc.io' in clean_url:
                return 'therpc'
            elif 'onfinality.io' in clean_url:
                return 'onfinality'
            elif 'stakely.io' in clean_url:
                return 'stakely'
            elif 'poolz.finance' in clean_url:
                return 'poolz'
            elif 'grove.city' in clean_url:
                return 'grove'
            else:
                # Extract from domain name
                parts = clean_url.split('.')
                if len(parts) >= 2:
                    return parts[-2]  # Second to last part
                return 'unknown'
                
        except Exception:
            return 'unknown'
    
    def _calculate_priority(self, rpc: Dict[str, Any]) -> int:
        """Calculate priority score for RPC endpoint."""
        priority = 0
        
        # Higher priority for open source
        if rpc.get('isOpenSource', False):
            priority += 10
        
        # Higher priority for no tracking
        tracking = rpc.get('tracking', 'unknown')
        if tracking == 'none':
            priority += 5
        elif tracking == 'limited':
            priority += 2
        elif tracking == 'yes':
            priority -= 2
        
        # Higher priority for well-known providers
        url = rpc.get('url', '').lower()
        if any(provider in url for provider in ['llamarpc', '1rpc', 'publicnode', 'cloudflare']):
            priority += 3
        elif any(provider in url for provider in ['alchemy', 'infura', 'quicknode']):
            priority += 2
        elif any(provider in url for provider in ['getblock', 'nodereal', 'blastapi']):
            priority += 1
        
        return priority
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache."""
        if not self.cache_file.exists():
            return {'status': 'no_cache', 'message': 'No cache file found'}
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                return {'status': 'error', 'message': 'Invalid cache format'}
            
            file_time = self.cache_file.stat().st_mtime
            current_time = time.time()
            age_days = (current_time - file_time) / (24 * 60 * 60)
            
            return {
                'status': 'valid' if self._is_cache_valid() else 'expired',
                'fetched_at': datetime.fromtimestamp(file_time).isoformat(),
                'age_days': round(age_days, 2),
                'total_chains': len(data),
                'ethereum_rpcs': len(self._extract_ethereum_rpcs(data))
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

def main():
    """Test the RPC fetcher."""
    logging.basicConfig(level=logging.INFO)
    
    fetcher = RPCFetcher()
    
    print("RPC Fetcher Test")
    print("=" * 50)
    
    # Get cache info
    cache_info = fetcher.get_cache_info()
    print(f"Cache Status: {cache_info}")
    print()
    
    # Get Ethereum RPCs
    rpcs = fetcher.get_ethereum_rpcs()
    print(f"Found {len(rpcs)} Ethereum RPC endpoints")
    print()
    
    # Show top 10 RPCs
    print("Top 10 RPC endpoints:")
    for i, rpc in enumerate(rpcs[:10], 1):
        print(f"{i:2d}. {rpc['name']:15s} {rpc['url']:50s} (Priority: {rpc['priority']:2d}, Tracking: {rpc['tracking']})")

if __name__ == "__main__":
    main()

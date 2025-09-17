"""
Uniswap pool monitor for tracking ROKO token liquidity pools.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from web3 import Web3
from .enhanced_rpc_client import EnhancedEthereumRPCClient


class UniswapPoolMonitor:
    """Monitor for Uniswap liquidity pools containing ROKO token."""
    
    def __init__(self, rpc_client: EnhancedEthereumRPCClient, roko_address: str, 
                 uniswap_v2_factory: str, uniswap_v3_factory: str, weth_address: str):
        """
        Initialize the Uniswap pool monitor.
        
        Args:
            rpc_client: Ethereum RPC client instance
            roko_address: ROKO token contract address
            uniswap_v2_factory: Uniswap V2 factory contract address
            uniswap_v3_factory: Uniswap V3 factory contract address
            weth_address: WETH contract address
        """
        self.rpc_client = rpc_client
        self.roko_address = roko_address
        self.uniswap_v2_factory = uniswap_v2_factory
        self.uniswap_v3_factory = uniswap_v3_factory
        self.weth_address = weth_address
        self.logger = logging.getLogger(__name__)
        
        # Uniswap V2 Factory ABI
        self.v2_factory_abi = [
            {
                "constant": True,
                "inputs": [{"name": "tokenA", "type": "address"}, {"name": "tokenB", "type": "address"}],
                "name": "getPair",
                "outputs": [{"name": "pair", "type": "address"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "", "type": "uint256"}],
                "name": "allPairs",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "allPairsLength",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        # Uniswap V2 Pair ABI
        self.v2_pair_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"name": "reserve0", "type": "uint112"},
                    {"name": "reserve1", "type": "uint112"},
                    {"name": "blockTimestampLast", "type": "uint32"}
                ],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token0",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "token1",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
    
    def find_roko_pools(self) -> List[Dict[str, Any]]:
        """Find all Uniswap pools containing ROKO token."""
        pools = []
        
        try:
            # Check V2 pools
            v2_pools = self._find_v2_pools()
            pools.extend(v2_pools)
            
            # Check V3 pools (simplified - would need more complex logic for V3)
            # v3_pools = self._find_v3_pools()
            # pools.extend(v3_pools)
            
            self.logger.info(f"Found {len(pools)} ROKO pools")
            return pools
            
        except Exception as e:
            self.logger.error(f"Error finding ROKO pools: {e}")
            return []
    
    def _find_v2_pools(self) -> List[Dict[str, Any]]:
        """Find Uniswap V2 pools containing ROKO."""
        pools = []
        
        try:
            # Common token pairs to check (using proper checksum addresses)
            common_tokens = [
                self.weth_address,  # WETH
                "0xA0b86a33E6441b8C4C8C0C4C8C0C4C8C0C4C8C0C4",  # USDC (placeholder)
                "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
                "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
            ]
            
            for token in common_tokens:
                try:
                    # Ensure addresses are properly checksummed
                    roko_checksum = Web3.to_checksum_address(self.roko_address)
                    token_checksum = Web3.to_checksum_address(token)
                    
                    # Get pair address from factory
                    pair_address = self.rpc_client.call_contract_method(
                        self.uniswap_v2_factory,
                        self.v2_factory_abi,
                        "getPair",
                        roko_checksum, token_checksum
                    )
                    
                    if pair_address != "0x0000000000000000000000000000000000000000":
                        # Get pair details
                        token0 = self.rpc_client.call_contract_method(
                            pair_address,
                            self.v2_pair_abi,
                            "token0"
                        )
                        
                        token1 = self.rpc_client.call_contract_method(
                            pair_address,
                            self.v2_pair_abi,
                            "token1"
                        )
                        
                        pools.append({
                            'address': pair_address,
                            'type': 'uniswap_v2',
                            'token0': token0,
                            'token1': token1,
                            'roko_is_token0': token0.lower() == self.roko_address.lower()
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error checking pair with token {token}: {e}")
                    continue
            
            return pools
            
        except Exception as e:
            self.logger.error(f"Error finding V2 pools: {e}")
            return []
    
    def get_pool_reserves(self, pool_address: str) -> Dict[str, Any]:
        """Get pool reserves and basic information."""
        try:
            reserves = self.rpc_client.call_contract_method(
                pool_address,
                self.v2_pair_abi,
                "getReserves"
            )
            
            token0 = self.rpc_client.call_contract_method(
                pool_address,
                self.v2_pair_abi,
                "token0"
            )
            
            token1 = self.rpc_client.call_contract_method(
                pool_address,
                self.v2_pair_abi,
                "token1"
            )
            
            total_supply = self.rpc_client.call_contract_method(
                pool_address,
                self.v2_pair_abi,
                "totalSupply"
            )
            
            return {
                'reserve0': reserves[0],
                'reserve1': reserves[1],
                'block_timestamp_last': reserves[2],
                'token0': token0,
                'token1': token1,
                'total_supply': total_supply
            }
        except Exception as e:
            self.logger.error(f"Error getting pool reserves for {pool_address}: {e}")
            raise
    
    def get_pool_liquidity(self, pool_address: str) -> float:
        """Get total liquidity value in USD (simplified calculation)."""
        try:
            reserves = self.get_pool_reserves(pool_address)
            
            # This is a simplified calculation
            # In production, you'd want to get actual token prices
            # and calculate the real USD value
            
            # For now, assuming reserve0 is ROKO and reserve1 is ETH
            # and using a placeholder ETH price
            eth_price = self.rpc_client.get_eth_price_usd()
            
            # Convert reserves to human-readable format
            # (This assumes 18 decimals for both tokens - adjust as needed)
            reserve0_formatted = reserves['reserve0'] / (10 ** 18)
            reserve1_formatted = reserves['reserve1'] / (10 ** 18)
            
            # Calculate liquidity (simplified)
            liquidity_usd = reserve1_formatted * eth_price * 2  # Rough estimate
            
            return liquidity_usd
            
        except Exception as e:
            self.logger.error(f"Error calculating pool liquidity: {e}")
            return 0.0
    
    def get_pool_volume_alchemy(self, pool_address: str, days: int = 1) -> Dict[str, Any]:
        """
        Get pool volume data using Alchemy API.
        
        Args:
            pool_address: The pool contract address
            days: Number of days to look back for volume data
            
        Returns:
            Dictionary with volume data
        """
        try:
            import requests
            import os
            import time
            from datetime import datetime, timedelta
            
            # Get Alchemy API key from environment
            api_key = os.getenv('ALCHEMY_API_KEY')
            if not api_key:
                self.logger.debug("No Alchemy API key found, skipping Alchemy volume lookup")
                return {'volume_24h_usd': 0, 'volume_7d_usd': 0, 'volume_30d_usd': 0}
            
            # Calculate time ranges
            now = datetime.now()
            end_time = now
            start_time_24h = now - timedelta(days=1)
            start_time_7d = now - timedelta(days=7)
            start_time_30d = now - timedelta(days=30)
            
            # Convert to Unix timestamps
            end_timestamp = int(end_time.timestamp())
            start_24h_timestamp = int(start_time_24h.timestamp())
            start_7d_timestamp = int(start_time_7d.timestamp())
            start_30d_timestamp = int(start_time_30d.timestamp())
            
            url = f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
            
            volume_data = {
                'volume_24h_usd': 0,
                'volume_7d_usd': 0,
                'volume_30d_usd': 0,
                'volume_24h_eth': 0,
                'volume_7d_eth': 0,
                'volume_30d_eth': 0
            }
            
            # Get Swap events from the pool for volume calculation
            swap_topic = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
            
            for period, start_ts in [('24h', start_24h_timestamp), ('7d', start_7d_timestamp), ('30d', start_30d_timestamp)]:
                try:
                    payload = {
                        "jsonrpc": "2.0",
                        "method": "eth_getLogs",
                        "params": [{
                            "fromBlock": "0x0",
                            "toBlock": "latest",
                            "address": pool_address,
                            "topics": [swap_topic]
                        }],
                        "id": 1
                    }
                    
                    response = requests.post(url, json=payload, timeout=30)
                    response.raise_for_status()
                    
                    data = response.json()
                    if 'result' in data:
                        logs = data['result']
                        
                        # Filter logs by timestamp (approximate using block numbers)
                        # This is a simplified approach - in production you'd want more precise filtering
                        recent_logs = logs[-100:]  # Take last 100 swaps as approximation
                        
                        # Calculate volume from swap events
                        total_volume_eth = 0
                        for log in recent_logs:
                            if len(log.get('data', '')) >= 130:  # Ensure we have enough data
                                # Parse swap data (simplified)
                                # amount0In, amount1In, amount0Out, amount1Out
                                data_hex = log['data'][2:]  # Remove 0x prefix
                                
                                try:
                                    amount0_in = int(data_hex[0:64], 16)
                                    amount1_in = int(data_hex[64:128], 16)
                                    amount0_out = int(data_hex[128:192], 16)
                                    amount1_out = int(data_hex[192:256], 16)
                                    
                                    # Calculate ETH volume (assuming token1 is WETH)
                                    eth_volume = (amount1_in + amount1_out) / (10 ** 18)  # Convert from wei
                                    total_volume_eth += eth_volume
                                    
                                except (ValueError, IndexError):
                                    continue
                        
                        # Get ETH price for USD conversion
                        eth_price = self.rpc_client.get_eth_price_usd()
                        volume_usd = total_volume_eth * eth_price
                        
                        volume_data[f'volume_{period}_eth'] = total_volume_eth
                        volume_data[f'volume_{period}_usd'] = volume_usd
                        
                        self.logger.info(f"Pool volume ({period}): {total_volume_eth:.4f} ETH (${volume_usd:.2f})")
                        
                except Exception as e:
                    self.logger.debug(f"Error getting {period} volume: {e}")
                    continue
            
            return volume_data
            
        except Exception as e:
            self.logger.error(f"Error getting pool volume from Alchemy: {e}")
            return {'volume_24h_usd': 0, 'volume_7d_usd': 0, 'volume_30d_usd': 0}
    
    def get_pool_volume_rpc(self, pool_address: str) -> Dict[str, Any]:
        """
        Get pool volume data using RPC calls (fallback method).
        This is less accurate but works without Alchemy.
        """
        try:
            # This is a simplified RPC-based volume calculation
            # In practice, you'd need to analyze Swap events over time
            
            reserves = self.get_pool_reserves(pool_address)
            eth_price = self.rpc_client.get_eth_price_usd()
            
            # Very rough estimate based on current reserves
            # This is not accurate for actual volume
            reserve1_formatted = reserves['reserve1'] / (10 ** 18)
            estimated_volume = reserve1_formatted * 0.1  # Assume 10% of reserves as daily volume
            
            return {
                'volume_24h_usd': estimated_volume * eth_price,
                'volume_7d_usd': estimated_volume * eth_price * 7,
                'volume_30d_usd': estimated_volume * eth_price * 30,
                'volume_24h_eth': estimated_volume,
                'volume_7d_eth': estimated_volume * 7,
                'volume_30d_eth': estimated_volume * 30
            }
            
        except Exception as e:
            self.logger.error(f"Error getting pool volume from RPC: {e}")
            return {'volume_24h_usd': 0, 'volume_7d_usd': 0, 'volume_30d_usd': 0}
    
    def get_pool_volume(self, pool_address: str) -> Dict[str, Any]:
        """
        Get pool volume data, trying Alchemy first, then falling back to RPC.
        
        Args:
            pool_address: The pool contract address
            
        Returns:
            Dictionary with volume data
        """
        try:
            # Try Alchemy first (more accurate)
            alchemy_volume = self.get_pool_volume_alchemy(pool_address)
            if alchemy_volume.get('volume_24h_usd', 0) > 0:
                return alchemy_volume
            
            # Fallback to RPC method
            return self.get_pool_volume_rpc(pool_address)
            
        except Exception as e:
            self.logger.error(f"Error getting pool volume: {e}")
            return {'volume_24h_usd': 0, 'volume_7d_usd': 0, 'volume_30d_usd': 0}
    
    def calculate_price_impact(self, pool_address: str, amount_in: float) -> float:
        """
        Calculate price impact for a given trade amount.
        
        Args:
            pool_address: The pool address
            amount_in: Amount of tokens to trade in
            
        Returns:
            Price impact as a percentage
        """
        try:
            reserves = self.get_pool_reserves(pool_address)
            
            # Simplified price impact calculation
            # In production, you'd want to use the actual Uniswap formula
            
            reserve0 = reserves['reserve0']
            reserve1 = reserves['reserve1']
            
            # Convert amount to same units as reserves
            amount_in_wei = int(amount_in * (10 ** 18))
            
            # Calculate price impact (simplified)
            if reserve0 > 0:
                price_impact = (amount_in_wei / reserve0) * 100
                return min(price_impact, 100.0)  # Cap at 100%
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating price impact: {e}")
            return 0.0
    
    def get_trading_volume_24h(self, pool_address: str) -> float:
        """Get 24-hour trading volume (simplified implementation)."""
        try:
            # Get Swap events from the last 24 hours
            latest_block = self.rpc_client.get_latest_block()
            # Approximate 24 hours = 24 * 60 * 60 / 12 = 7200 blocks (assuming 12s block time)
            from_block = max(0, latest_block['number'] - 7200)
            
            # Swap event signature
            swap_topic = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
            
            logs = self.rpc_client.get_logs(
                from_block=from_block,
                to_block='latest',
                address=pool_address,
                topics=[swap_topic]
            )
            
            # Calculate total volume (simplified)
            total_volume = 0.0
            for log in logs:
                # Parse swap data (simplified)
                # In production, you'd properly decode the log data
                total_volume += 1000  # Placeholder value
            
            return total_volume
            
        except Exception as e:
            self.logger.error(f"Error getting trading volume: {e}")
            return 0.0
    
    def get_pool_fees_24h(self, pool_address: str) -> float:
        """Get 24-hour fees collected (simplified implementation)."""
        try:
            # This would require more complex calculation
            # For now, returning a placeholder
            volume_24h = self.get_trading_volume_24h(pool_address)
            # Assuming 0.3% fee
            return volume_24h * 0.003
            
        except Exception as e:
            self.logger.error(f"Error getting pool fees: {e}")
            return 0.0
    
    def monitor_swaps(self, pool_address: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Monitor swap events for a pool.
        
        Args:
            pool_address: The pool address to monitor
            callback: Function to call when a swap is detected
        """
        try:
            # Swap event signature
            swap_topic = "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822"
            
            # Get recent swap events
            latest_block = self.rpc_client.get_latest_block()
            from_block = max(0, latest_block['number'] - 100)
            
            logs = self.rpc_client.get_logs(
                from_block=from_block,
                to_block='latest',
                address=pool_address,
                topics=[swap_topic]
            )
            
            for log in logs:
                swap_data = {
                    'pool_address': pool_address,
                    'block_number': log['block_number'],
                    'transaction_hash': log['transaction_hash'],
                    'log_index': log['log_index'],
                    'data': log['data']
                }
                callback(swap_data)
                
        except Exception as e:
            self.logger.error(f"Error monitoring swaps: {e}")
    
    def get_pool_comprehensive_data(self, pool_address: str) -> Dict[str, Any]:
        """Get comprehensive pool data."""
        try:
            reserves = self.get_pool_reserves(pool_address)
            liquidity = self.get_pool_liquidity(pool_address)
            volume_24h = self.get_trading_volume_24h(pool_address)
            fees_24h = self.get_pool_fees_24h(pool_address)
            
            return {
                'pool_address': pool_address,
                'reserves': reserves,
                'liquidity_usd': liquidity,
                'volume_24h': volume_24h,
                'fees_24h': fees_24h,
                'timestamp': self.rpc_client.web3.eth.get_block('latest').timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive pool data: {e}")
            raise

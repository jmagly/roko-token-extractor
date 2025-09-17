"""
Price oracle for getting real-time token prices
"""

import requests
import logging
import time
from typing import Dict, Any, Optional, List


class PriceOracle:
    """Price oracle for getting real-time token and ETH prices."""
    
    def __init__(self):
        """Initialize the price oracle."""
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ROKO-Token-Extractor/1.0'
        })
        self._eth_price_cache = None
        self._eth_price_cache_time = 0
        self._cache_duration = 300  # 5 minutes
    
    def get_eth_price_usd(self, rpc_client) -> float:
        """Get current ETH price in USD from Uniswap pools (USDC/ETH and USDT/ETH) with caching."""
        current_time = time.time()
        
        # Return cached price if still valid
        if (self._eth_price_cache is not None and 
            current_time - self._eth_price_cache_time < self._cache_duration):
            return self._eth_price_cache
        
        # Get ETH price from Uniswap pools (USDC/ETH and USDT/ETH)
        eth_price = self._get_eth_price_from_uniswap_pools(rpc_client)
        if eth_price is not None:
            self._eth_price_cache = eth_price
            self._eth_price_cache_time = current_time
            self.logger.info(f"ETH price from Uniswap pools: ${eth_price}")
            return eth_price
        
        # If Uniswap pools fail, return a reasonable fallback price
        self.logger.warning("Failed to get ETH price from Uniswap pools, using fallback price")
        return 2000.0
    
    def _get_eth_price_from_uniswap_pools(self, rpc_client) -> Optional[float]:
        """
        Get ETH price from USDC/ETH and USDT/ETH pools on Uniswap.
        
        Args:
            rpc_client: RPC client for blockchain calls
            
        Returns:
            ETH price in USD, or None if calculation fails
        """
        try:
            from .pool_monitor import UniswapPoolMonitor
            
            # Get token addresses from config
            from config.settings import Config
            config = Config()
            usdc_address = config.get_usdc_address()
            usdt_address = config.get_usdt_address()
            weth_address = config.get_weth_address()
            
            # Initialize pool monitor
            pool_monitor = UniswapPoolMonitor(
                rpc_client=rpc_client,
                roko_address=usdc_address,  # We'll use this as a template
                uniswap_v2_factory=config.get_uniswap_v2_factory(),
                uniswap_v3_factory=config.get_uniswap_v3_factory(),
                weth_address=weth_address
            )
            
            eth_prices = []
            
            # Try USDC/ETH pool
            try:
                usdc_eth_pools = self._find_stablecoin_pools(pool_monitor, usdc_address, weth_address)
                for pool in usdc_eth_pools:
                    price = self._calculate_eth_price_from_pool(pool_monitor, pool, usdc_address, weth_address)  # Will fetch decimals automatically
                    if price is not None:
                        eth_prices.append(price)
                        self.logger.info(f"ETH price from USDC/ETH pool: ${price}")
            except Exception as e:
                self.logger.debug(f"Error getting ETH price from USDC/ETH pool: {e}")
            
            # Try USDT/ETH pool
            try:
                usdt_eth_pools = self._find_stablecoin_pools(pool_monitor, usdt_address, weth_address)
                for pool in usdt_eth_pools:
                    price = self._calculate_eth_price_from_pool(pool_monitor, pool, usdt_address, weth_address)  # Will fetch decimals automatically
                    if price is not None:
                        eth_prices.append(price)
                        self.logger.info(f"ETH price from USDT/ETH pool: ${price}")
            except Exception as e:
                self.logger.debug(f"Error getting ETH price from USDT/ETH pool: {e}")
            
            # Filter out unrealistic prices (ETH should be between $1000 and $10000)
            realistic_prices = [price for price in eth_prices if 1000 <= price <= 10000]
            
            if realistic_prices:
                if len(realistic_prices) > 1:
                    avg_price = sum(realistic_prices) / len(realistic_prices)
                    self.logger.info(f"Average ETH price from Uniswap pools: ${avg_price}")
                else:
                    avg_price = realistic_prices[0]
                    self.logger.info(f"ETH price from Uniswap pools: ${avg_price}")
                return avg_price
            elif eth_prices:
                # If no realistic prices, use the first one anyway (better than nothing)
                self.logger.warning(f"Using potentially unrealistic ETH price: ${eth_prices[0]}")
                return eth_prices[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting ETH price from Uniswap pools: {e}")
            return None
    
    def _find_stablecoin_pools(self, pool_monitor, token_address: str, weth_address: str) -> List[Dict[str, Any]]:
        """Find pools for a specific token pair."""
        try:
            # Get pair address from Uniswap V2 factory
            pair_address = pool_monitor.rpc_client.call_contract_method(
                pool_monitor.uniswap_v2_factory,
                pool_monitor.v2_factory_abi,
                'getPair',
                token_address,
                weth_address
            )
            
            if pair_address and pair_address != "0x0000000000000000000000000000000000000000":
                # Determine which token is token0 based on address comparison
                token_is_token0 = token_address.lower() < weth_address.lower()
                
                return [{
                    'address': pair_address,
                    'type': 'uniswap_v2',
                    'token0': token_address if token_is_token0 else weth_address,
                    'token1': weth_address if token_is_token0 else token_address,
                    'token_is_token0': token_is_token0
                }]
            
            return []
            
        except Exception as e:
            self.logger.debug(f"Error finding pools for {token_address}: {e}")
            return []
    
    def _calculate_eth_price_from_pool(self, pool_monitor, pool: Dict[str, Any], token_address: str, weth_address: str, token_decimals: int = None) -> Optional[float]:
        """Calculate ETH price from pool reserves."""
        try:
            reserves = pool_monitor.get_pool_reserves(pool['address'])
            
            # Determine which token is which
            if pool['token_is_token0']:
                token_reserve = reserves['reserve0']
                weth_reserve = reserves['reserve1']
            else:
                token_reserve = reserves['reserve1']
                weth_reserve = reserves['reserve0']
            
            if token_reserve > 0 and weth_reserve > 0:
                # Get token decimals if not provided
                if token_decimals is None:
                    try:
                        # Try to get decimals from the token contract
                        from .enhanced_rpc_client import EnhancedEthereumRPCClient
                        rpc_client = EnhancedEthereumRPCClient()
                        token_info = rpc_client.get_token_info(token_address)
                        token_decimals = token_info.get('decimals', 18)
                    except:
                        token_decimals = 18  # Default fallback
                
                # Convert token reserve to proper decimal places
                token_amount = token_reserve / (10 ** token_decimals)
                weth_amount = weth_reserve / (10 ** 18)  # WETH has 18 decimals
                
                # Calculate ETH price: token_amount / weth_amount = USD per ETH
                # If pool has 1000 USDC and 0.22 ETH, then 1 ETH = 1000/0.22 = 4545 USDC
                if weth_amount > 0:
                    usd_per_eth = token_amount / weth_amount
                    self.logger.debug(f"Pool calculation: {token_amount} {token_address[:8]}... / {weth_amount} WETH = {usd_per_eth} USD per ETH")
                    return usd_per_eth
                
            return None
            
        except Exception as e:
            self.logger.debug(f"Error calculating ETH price from pool: {e}")
            return None
    
    
    
    
    def get_token_price_from_pool(self, token_address: str, weth_address: str, rpc_client) -> Optional[float]:
        """
        Calculate token price directly from pool reserves (ROKO:ETH ratio).
        This is the most accurate method and avoids external API calls.
        
        Args:
            token_address: Token contract address
            weth_address: WETH contract address  
            rpc_client: RPC client for blockchain calls
            
        Returns:
            Token price in ETH, or None if calculation fails
        """
        try:
            from .pool_monitor import UniswapPoolMonitor
            
            # Initialize pool monitor
            pool_monitor = UniswapPoolMonitor(
                rpc_client=rpc_client,
                roko_address=token_address,
                uniswap_v2_factory="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
                uniswap_v3_factory="0x1F98431c8aD98523631AE4a59f267346ea31F984",
                weth_address=weth_address
            )
            
            # Find pools
            pools = pool_monitor.find_roko_pools()
            
            if not pools:
                self.logger.debug("No ROKO pools found for price calculation")
                return None
            
            # Calculate price from the pool with highest liquidity
            best_price = None
            best_liquidity = 0
            
            for pool in pools:
                try:
                    reserves = pool_monitor.get_pool_reserves(pool['address'])
                    
                    # Determine which token is ROKO and which is WETH
                    if pool['roko_is_token0']:
                        roko_reserve = reserves['reserve0']
                        weth_reserve = reserves['reserve1']
                    else:
                        roko_reserve = reserves['reserve1']
                        weth_reserve = reserves['reserve0']
                    
                    # Calculate liquidity (simple: reserve0 * reserve1)
                    liquidity = roko_reserve * weth_reserve
                    
                    if roko_reserve > 0 and weth_reserve > 0 and liquidity > best_liquidity:
                        # Calculate ROKO:ETH ratio (ROKO per ETH)
                        roko_eth_ratio = roko_reserve / weth_reserve
                        best_price = roko_eth_ratio
                        best_liquidity = liquidity
                        
                        self.logger.info(f"Pool price calculation: {roko_reserve:,.0f} ROKO / {weth_reserve:,.0f} WETH = {roko_eth_ratio:.10f} ROKO per ETH")
                        
                except Exception as e:
                    self.logger.debug(f"Error calculating price from pool {pool['address']}: {e}")
                    continue
            
            if best_price is not None:
                self.logger.info(f"Token price from pool calculation: {best_price:.10f} ETH")
            
            return best_price
            
        except Exception as e:
            self.logger.error(f"Error getting token price from pool: {e}")
            return None

    
    
    def get_comprehensive_pricing(self, token_address: str, weth_address: str, rpc_client=None) -> Dict[str, Any]:
        """
        Get comprehensive pricing data from multiple sources.
        
        Args:
            token_address: The token contract address
            weth_address: WETH contract address
            rpc_client: Optional RPC client for Uniswap integration
            
        Returns:
            Dictionary with pricing information
        """
        pricing_data = {
            'eth_price_usd': 0.0,
            'token_price_eth': None,
            'token_price_usd': None,
            'price_sources': [],
            'all_prices': {},
            'timestamp': int(time.time())
        }
        
        try:
            # PRIORITY 1: Pool-based pricing (most accurate, minimal API calls)
            if rpc_client:
                roko_eth_ratio = self.get_token_price_from_pool(token_address, weth_address, rpc_client)
                if roko_eth_ratio is not None:
                    # Get ETH price from Uniswap pools (USDC/ETH, USDT/ETH)
                    eth_price = self.get_eth_price_usd(rpc_client)
                    pricing_data['eth_price_usd'] = eth_price
                    
                    # Calculate prices using ROKO:ETH ratio
                    # If 1 ETH = X ROKO, then 1 ROKO = 1/X ETH
                    eth_per_roko = 1 / roko_eth_ratio if roko_eth_ratio > 0 else 0
                    usd_per_roko = eth_per_roko * eth_price if eth_price > 0 else 0
                    
                    pricing_data['token_eth_ratio'] = roko_eth_ratio
                    pricing_data['eth_per_token'] = eth_per_roko
                    pricing_data['usd_per_token'] = usd_per_roko
                    pricing_data['price_sources'] = ['uniswap_pool']
                    pricing_data['all_prices']['uniswap_pool'] = {
                        'token_eth_ratio': roko_eth_ratio,
                        'eth_per_token': eth_per_roko,
                        'usd_per_token': usd_per_roko
                    }
                    return pricing_data
            
            # If pool pricing failed, we cannot calculate accurate prices
            # Return zero prices with appropriate error message
            self.logger.error("Pool-based pricing failed - cannot calculate accurate token prices without RPC data")
            pricing_data.update({
                'token_eth_ratio': 0.0,
                'eth_per_token': 0.0,
                'usd_per_token': 0.0,
                'price_sources': ['pool_failed']
            })
            
            return pricing_data
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive pricing: {e}")
            return pricing_data

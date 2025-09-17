"""
Price oracle for getting real-time token prices
"""

import requests
import logging
import time
from typing import Dict, Any, Optional


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
    
    def get_eth_price_usd(self) -> float:
        """Get current ETH price in USD from CoinGecko with caching."""
        current_time = time.time()
        
        # Return cached price if still valid
        if (self._eth_price_cache is not None and 
            current_time - self._eth_price_cache_time < self._cache_duration):
            return self._eth_price_cache
        
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'ethereum',
                'vs_currencies': 'usd'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            eth_price = data.get('ethereum', {}).get('usd', 0.0)
            
            # Cache the result
            self._eth_price_cache = float(eth_price)
            self._eth_price_cache_time = current_time
            
            self.logger.info(f"ETH price: ${eth_price}")
            return self._eth_price_cache
            
        except Exception as e:
            self.logger.error(f"Error getting ETH price: {e}")
            # Return cached price if available, otherwise fallback
            if self._eth_price_cache is not None:
                self.logger.warning("Using cached ETH price due to API error")
                return self._eth_price_cache
            return 2000.0
    
    def get_token_price_from_dex(self, token_address: str, weth_address: str) -> Optional[float]:
        """
        Get token price from DEX by finding pools and calculating price.
        This is a simplified implementation.
        """
        try:
            # This would require more complex DEX integration
            # For now, we'll return None to indicate no price found
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting token price from DEX: {e}")
            return None
    
    def get_token_price_coingecko(self, token_address: str) -> Optional[float]:
        """Get token price from CoinGecko if available."""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/token_price/ethereum"
            params = {
                'contract_addresses': token_address,
                'vs_currencies': 'usd'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            token_price = data.get(token_address.lower(), {}).get('usd')
            
            if token_price:
                self.logger.info(f"Token price from CoinGecko: ${token_price}")
                return float(token_price)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting token price from CoinGecko: {e}")
            return None
    
    def get_token_price_1inch(self, token_address: str, weth_address: str) -> Optional[float]:
        """Get token price from 1inch API."""
        try:
            url = "https://api.1inch.io/v5.0/1/quote"
            params = {
                'fromTokenAddress': token_address,
                'toTokenAddress': weth_address,
                'amount': '1000000000000000000'  # 1 token (18 decimals)
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            to_amount = float(data.get('toAmount', 0))
            
            if to_amount > 0:
                # Convert from wei to ETH
                price_eth = to_amount / (10**18)
                self.logger.info(f"Token price from 1inch: {price_eth} ETH")
                return price_eth
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting token price from 1inch: {e}")
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

    def get_token_price_uniswap(self, token_address: str, weth_address: str, rpc_client) -> Optional[float]:
        """Get token price directly from Uniswap pools."""
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
                return None
            
            # Get price from the first pool with liquidity
            for pool in pools:
                try:
                    reserves = pool_monitor.get_pool_reserves(pool['address'])
                    
                    if pool['roko_is_token0']:
                        roko_reserve = reserves['reserve0']
                        weth_reserve = reserves['reserve1']
                    else:
                        roko_reserve = reserves['reserve1']
                        weth_reserve = reserves['reserve0']
                    
                    if roko_reserve > 0 and weth_reserve > 0:
                        # Calculate price: WETH per ROKO
                        price_eth = weth_reserve / roko_reserve
                        self.logger.info(f"Token price from Uniswap: {price_eth} ETH")
                        return price_eth
                        
                except Exception as e:
                    self.logger.debug(f"Error getting price from pool {pool['address']}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting token price from Uniswap: {e}")
            return None
    
    def get_token_price_dexscreener(self, token_address: str) -> Optional[float]:
        """Get token price from DexScreener API."""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            pairs = data.get('pairs', [])
            
            if pairs:
                # Get the first pair with price data
                for pair in pairs:
                    price_usd = pair.get('priceUsd')
                    if price_usd and float(price_usd) > 0:
                        self.logger.info(f"Token price from DexScreener: ${price_usd}")
                        return float(price_usd)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting token price from DexScreener: {e}")
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
                    # Get ETH price only once
                    eth_price = self.get_eth_price_usd()
                    pricing_data['eth_price_usd'] = eth_price
                    
                    # Calculate prices using ROKO:ETH ratio
                    # If 1 ETH = X ROKO, then 1 ROKO = 1/X ETH
                    eth_per_roko = 1 / roko_eth_ratio if roko_eth_ratio > 0 else 0
                    usd_per_roko = eth_per_roko * eth_price if eth_price > 0 else 0
                    
                    pricing_data['roko_eth_ratio'] = roko_eth_ratio
                    pricing_data['eth_per_roko'] = eth_per_roko
                    pricing_data['usd_per_roko'] = usd_per_roko
                    pricing_data['price_sources'] = ['uniswap_pool']
                    pricing_data['all_prices']['uniswap_pool'] = {
                        'roko_eth_ratio': roko_eth_ratio,
                        'eth_per_roko': eth_per_roko,
                        'usd_per_roko': usd_per_roko
                    }
                    return pricing_data
            
            # FALLBACK: External APIs (only if pool pricing fails)
            eth_price = self.get_eth_price_usd()
            pricing_data['eth_price_usd'] = eth_price
            
            # Try external sources as fallback
            sources = [
                ('dexscreener', lambda: self.get_token_price_dexscreener(token_address)),
                ('coingecko', lambda: self.get_token_price_coingecko(token_address)),
                ('1inch', lambda: self.get_token_price_1inch(token_address, weth_address)),
            ]
            
            # Add Uniswap if RPC client is available (fallback)
            if rpc_client:
                sources.append(('uniswap', lambda: self.get_token_price_uniswap(token_address, weth_address, rpc_client)))
            
            best_price_usd = None
            best_price_eth = None
            best_source = None
            
            for source_name, price_func in sources:
                try:
                    price = price_func()
                    if price is not None:
                        if source_name in ['coingecko', 'dexscreener']:
                            # Price is in USD
                            pricing_data['all_prices'][source_name] = {
                                'price_usd': price,
                                'price_eth': price / eth_price if eth_price > 0 else None
                            }
                            if best_price_usd is None or abs(price - 0.000014) < abs(best_price_usd - 0.000014):
                                best_price_usd = price
                                best_price_eth = price / eth_price if eth_price > 0 else None
                                best_source = source_name
                                
                        elif source_name in ['1inch', 'uniswap']:
                            # Price is in ETH
                            pricing_data['all_prices'][source_name] = {
                                'price_eth': price,
                                'price_usd': price * eth_price if eth_price > 0 else None
                            }
                            if best_price_eth is None or abs(price - 0.000000003) < abs(best_price_eth - 0.000000003):
                                best_price_eth = price
                                best_price_usd = price * eth_price if eth_price > 0 else None
                                best_source = source_name
                        
                except Exception as e:
                    self.logger.debug(f"Price source {source_name} failed: {e}")
                    continue
            
            # Use the best price found
            if best_price_usd is not None:
                pricing_data['token_price_usd'] = best_price_usd
                pricing_data['token_price_eth'] = best_price_eth
                pricing_data['price_sources'].append(best_source)
            elif best_price_eth is not None:
                pricing_data['token_price_eth'] = best_price_eth
                pricing_data['token_price_usd'] = best_price_usd
                pricing_data['price_sources'].append(best_source)
            
            # If no price found, use placeholder
            if pricing_data['token_price_eth'] is None:
                pricing_data['token_price_eth'] = 0.000001  # Placeholder
                pricing_data['token_price_usd'] = pricing_data['token_price_eth'] * eth_price
                pricing_data['price_sources'].append('placeholder')
            
            return pricing_data
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive pricing: {e}")
            return pricing_data

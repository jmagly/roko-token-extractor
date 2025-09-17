"""
RPC Load Balancer for managing multiple Ethereum RPC providers with failover and load balancing.
"""

import time
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
from web3 import Web3
from web3.exceptions import ContractLogicError
from utils.rpc_ignore_list import RPCIgnoreList
from utils.rpc_rate_limit_list import RPCRateLimitList


class LoadBalancingStrategy(Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    PRIORITY = "priority"
    RANDOM = "random"


@dataclass
class RPCProvider:
    """RPC provider configuration."""
    name: str
    url: str
    api_key: str
    priority: int
    rate_limit: int  # requests per minute
    timeout: int
    is_healthy: bool = True
    last_used: float = 0.0
    first_request_time: float = 0.0
    request_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


class RPCLoadBalancer:
    """Load balancer for multiple RPC providers with failover and rate limiting."""
    
    def __init__(self, providers: List[Dict[str, Any]], config: Dict[str, Any]):
        """
        Initialize the RPC load balancer.
        
        Args:
            providers: List of RPC provider configurations
            config: Load balancing configuration
        """
        self.logger = logging.getLogger(__name__)
        self.providers = []
        self.current_index = 0
        self.config = config
        self.ignore_list = RPCIgnoreList()
        self.rate_limit_list = RPCRateLimitList()
        
        # Initialize providers
        for provider_config in providers:
            provider = RPCProvider(
                name=provider_config['name'],
                url=provider_config['url'],
                api_key=provider_config.get('api_key', ''),
                priority=provider_config['priority'],
                rate_limit=provider_config['rate_limit'],
                timeout=provider_config['timeout']
            )
            self.providers.append(provider)
        
        # Sort by priority
        self.providers.sort(key=lambda x: x.priority)
        
        # Load balancing settings
        self.strategy = LoadBalancingStrategy(config.get('strategy', 'round_robin'))
        self.retry_attempts = config.get('retry_attempts', 3)
        self.retry_delay = config.get('retry_delay', 1)
        self.health_check_interval = config.get('health_check_interval', 60)
        self.max_concurrent_requests = config.get('max_concurrent_requests', 5)
        
        self.last_health_check = 0
        self.active_requests = 0
        
        self.logger.info(f"Initialized RPC Load Balancer with {len(self.providers)} providers")
        self.logger.info(f"Strategy: {self.strategy.value}")
    
    def get_provider(self) -> Optional[RPCProvider]:
        """Get the next available RPC provider based on the load balancing strategy."""
        # Check if we need to perform health checks
        if time.time() - self.last_health_check > self.health_check_interval:
            self._perform_health_checks()
            self.last_health_check = time.time()
        
        # Filter healthy providers and exclude ignored/rate-limited ones
        healthy_providers = [
            p for p in self.providers 
            if p.is_healthy and not self.ignore_list.is_ignored(p.url) and not self.rate_limit_list.is_rate_limited(p.url)
        ]
        
        if not healthy_providers:
            self.logger.error("No healthy RPC providers available")
            return None
        
        # Select provider based on strategy
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            provider = self._round_robin_selection(healthy_providers)
        elif self.strategy == LoadBalancingStrategy.PRIORITY:
            provider = self._priority_selection(healthy_providers)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            provider = self._random_selection(healthy_providers)
        else:
            provider = healthy_providers[0]
        
        return provider
    
    def clear_ignore_list(self) -> None:
        """Clear the ignore list (called when refreshing RPC endpoints from ChainList)."""
        self.ignore_list.clear_ignore_list()
        self.logger.info("Cleared RPC ignore list due to endpoint refresh")
    
    def clear_rate_limit_list(self) -> None:
        """Clear the rate limit list (called when refreshing RPC endpoints from ChainList)."""
        self.rate_limit_list.clear_rate_limit_list()
        self.logger.info("Cleared RPC rate limit list due to endpoint refresh")
    
    def get_ignore_list_info(self) -> Dict[str, Any]:
        """Get information about the current ignore list."""
        return self.ignore_list.get_ignore_list_info()
    
    def get_rate_limit_list_info(self) -> Dict[str, Any]:
        """Get information about the current rate limit list."""
        return self.rate_limit_list.get_rate_limit_list_info()
    
    def _round_robin_selection(self, providers: List[RPCProvider]) -> RPCProvider:
        """Select provider using round-robin strategy."""
        provider = providers[self.current_index % len(providers)]
        self.current_index = (self.current_index + 1) % len(providers)
        return provider
    
    def _priority_selection(self, providers: List[RPCProvider]) -> RPCProvider:
        """Select provider using priority strategy (lowest priority number first)."""
        return min(providers, key=lambda x: x.priority)
    
    def _random_selection(self, providers: List[RPCProvider]) -> RPCProvider:
        """Select provider using random strategy."""
        return random.choice(providers)
    
    def _perform_health_checks(self):
        """Perform health checks on all providers."""
        self.logger.debug("Performing health checks on RPC providers")
        
        for provider in self.providers:
            try:
                # Simple health check - try to get latest block
                web3 = Web3(Web3.HTTPProvider(provider.url, request_kwargs={'timeout': 5}))
                if web3.is_connected():
                    latest_block = web3.eth.get_block('latest')
                    if latest_block and latest_block.number > 0:
                        provider.is_healthy = True
                        provider.error_count = 0
                        provider.last_error = None
                    else:
                        provider.is_healthy = False
                        provider.last_error = "Invalid block data"
                else:
                    provider.is_healthy = False
                    provider.last_error = "Connection failed"
            except Exception as e:
                provider.is_healthy = False
                provider.error_count += 1
                provider.last_error = str(e)
                self.logger.debug(f"Health check failed for {provider.name}: {e}")
    
    def execute_request(self, request_func, *args, **kwargs) -> Any:
        """
        Execute a request with automatic failover and retry logic.
        
        Args:
            request_func: Function to execute (should accept web3 instance as first arg)
            *args: Arguments to pass to request_func
            **kwargs: Keyword arguments to pass to request_func
            
        Returns:
            Result of request_func execution
        """
        last_error = None
        
        for attempt in range(self.retry_attempts):
            provider = self.get_provider()
            if not provider:
                raise Exception("No healthy RPC providers available")
            
            # Check rate limiting
            if not self._check_rate_limit(provider):
                self.logger.warning(f"Rate limit exceeded for {provider.name}, trying next provider")
                # Add to rate limit list for temporary cooldown
                self.rate_limit_list.add_rate_limited_endpoint(
                    provider.url, 
                    429, 
                    f"Client-side rate limit exceeded for {provider.name}"
                )
                continue
            
            try:
                # Create Web3 instance for this provider
                web3 = self._create_web3_instance(provider)
                
                # Execute the request
                self.active_requests += 1
                provider.request_count += 1
                if provider.first_request_time == 0.0:
                    provider.first_request_time = time.time()
                provider.last_used = time.time()
                
                result = request_func(web3, *args, **kwargs)
                
                # Reset error count on success
                provider.error_count = 0
                provider.last_error = None
                
                return result
                
            except Exception as e:
                last_error = e
                provider.error_count += 1
                provider.last_error = str(e)
                
                self.logger.warning(f"Request failed with {provider.name}: {e}")
                
                # Handle different error types
                error_code = None
                if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    error_code = e.response.status_code
                elif 'Client Error' in str(e):
                    # Extract error code from error message
                    import re
                    match = re.search(r'(\d{3}) Client Error', str(e))
                    if match:
                        error_code = int(match.group(1))
                
                if error_code:
                    if error_code == 429:
                        # Add to rate limit list for temporary cooldown
                        self.rate_limit_list.add_rate_limited_endpoint(
                            provider.url, 
                            error_code, 
                            str(e)
                        )
                    elif error_code != 404:
                        # Add to ignore list for other non-404 errors
                        self.ignore_list.add_failing_endpoint(
                            provider.url, 
                            error_code, 
                            str(e)
                        )
                
                # Mark provider as unhealthy if too many errors
                if provider.error_count >= 5:
                    provider.is_healthy = False
                    self.logger.error(f"Marking {provider.name} as unhealthy due to repeated errors")
                
                # Wait before retry
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
            
            finally:
                self.active_requests = max(0, self.active_requests - 1)
        
        # All attempts failed
        raise Exception(f"All RPC providers failed. Last error: {last_error}")
    
    def _create_web3_instance(self, provider: RPCProvider) -> Web3:
        """Create a Web3 instance for the given provider."""
        # Replace API key placeholder if present
        url = provider.url
        if '{API_KEY}' in url and provider.api_key:
            url = url.replace('{API_KEY}', provider.api_key)
        
        return Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': provider.timeout}))
    
    def _check_rate_limit(self, provider: RPCProvider) -> bool:
        """Check if provider is within rate limits."""
        current_time = time.time()
        
        # Simple rate limiting check (requests per minute)
        if provider.request_count > 0:
            time_since_first = current_time - provider.first_request_time
            if time_since_first < 60:  # Within last minute
                requests_per_minute = provider.request_count / (time_since_first / 60)
                if requests_per_minute > provider.rate_limit:
                    self.logger.debug(f"Rate limit exceeded for {provider.name}: {requests_per_minute:.2f} req/min > {provider.rate_limit}")
                    return False
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of all providers."""
        return {
            'total_providers': len(self.providers),
            'healthy_providers': len([p for p in self.providers if p.is_healthy]),
            'active_requests': self.active_requests,
            'strategy': self.strategy.value,
            'providers': [
                {
                    'name': p.name,
                    'url': p.url,
                    'priority': p.priority,
                    'is_healthy': p.is_healthy,
                    'request_count': p.request_count,
                    'error_count': p.error_count,
                    'last_error': p.last_error,
                    'rate_limit': p.rate_limit
                }
                for p in self.providers
            ]
        }
    
    def reset_provider(self, provider_name: str):
        """Reset a provider's error count and mark as healthy."""
        for provider in self.providers:
            if provider.name == provider_name:
                provider.is_healthy = True
                provider.error_count = 0
                provider.last_error = None
                self.logger.info(f"Reset provider {provider_name}")
                break
    
    def get_health_report(self) -> str:
        """Get a formatted health report."""
        status = self.get_status()
        report = f"RPC Load Balancer Status:\n"
        report += f"Strategy: {status['strategy']}\n"
        report += f"Healthy Providers: {status['healthy_providers']}/{status['total_providers']}\n"
        report += f"Active Requests: {status['active_requests']}\n\n"
        
        for provider in status['providers']:
            health_status = "✅" if provider['is_healthy'] else "❌"
            report += f"{health_status} {provider['name']} (Priority {provider['priority']})\n"
            report += f"   Requests: {provider['request_count']}, Errors: {provider['error_count']}\n"
            if provider['last_error']:
                report += f"   Last Error: {provider['last_error']}\n"
            report += "\n"
        
        return report

"""
Enhanced Ethereum RPC client with load balancing and failover support.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional

from web3 import Web3
from web3.exceptions import ContractLogicError
from eth_typing import ChecksumAddress
from hexbytes import HexBytes

from config.settings import Config
from utils.data_processor import DataProcessor
from core.rpc_load_balancer import RPCLoadBalancer


class EnhancedEthereumRPCClient:
    """Enhanced Ethereum RPC client with load balancing and failover support."""
    
    def __init__(self, rpc_url: str = None, use_load_balancer: bool = True):
        """
        Initialize the enhanced RPC client.
        
        Args:
            rpc_url: Single RPC URL (for legacy mode)
            use_load_balancer: Whether to use load balancer with multiple providers
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.settings = Config()
        
        if use_load_balancer and self.settings.ethereum.get('rpc_providers'):
            # Use load balancer with multiple providers
            self.load_balancer = RPCLoadBalancer(
                self.settings.ethereum['rpc_providers'],
                self.settings.ethereum.get('load_balancing', {})
            )
            self.web3 = None  # Will be created per request
            self.logger.info("Initialized with RPC load balancer")
        else:
            # Use single RPC provider (legacy mode)
            if rpc_url is None:
                rpc_url = self.settings.get_rpc_url()
            
            self.load_balancer = None
            self.web3 = Web3(Web3.HTTPProvider(rpc_url))
            if not self.web3.is_connected():
                raise ConnectionError("Failed to connect to Ethereum node")
            self.logger.info(f"Connected to Ethereum node: {rpc_url}")
    
    def get_latest_block(self) -> Dict[str, Any]:
        """Get the latest block number and hash."""
        def _get_latest_block(web3, *args, **kwargs):
            block = web3.eth.get_block('latest')
            return {
                "number": block.number,
                "hash": block.hash.hex(),
                "timestamp": block.timestamp,
                "gas_limit": getattr(block, 'gasLimit', getattr(block, 'gas_limit', 0)),
                "gas_used": getattr(block, 'gasUsed', getattr(block, 'gas_used', 0)),
            }
        
        try:
            if self.load_balancer:
                return self.load_balancer.execute_request(_get_latest_block)
            else:
                return _get_latest_block(self.web3)
        except Exception as e:
            self.logger.error(f"Error getting latest block: {e}")
            raise
    
    def get_contract_instance(self, address: str, abi: List[Dict[str, Any]], web3: Web3 = None):
        """Get a contract instance."""
        if web3 is None:
            web3 = self.web3
        checksum_address = self._to_checksum_address(address, web3)
        return web3.eth.contract(address=checksum_address, abi=abi)
    
    def call_contract_method(self, contract_address: str, abi: List[Dict[str, Any]], method_name: str, *args: Any, **kwargs: Any) -> Any:
        """Call a contract method."""
        def _call_contract_method(web3, contract_address, abi, method_name, *args, **kwargs):
            contract = self.get_contract_instance(contract_address, abi, web3)
            method = getattr(contract.functions, method_name)
            return method(*args, **kwargs).call()
        
        try:
            if self.load_balancer:
                return self.load_balancer.execute_request(
                    _call_contract_method, contract_address, abi, method_name, *args, **kwargs
                )
            else:
                return _call_contract_method(self.web3, contract_address, abi, method_name, *args, **kwargs)
        except ContractLogicError as e:
            self.logger.error(f"Contract logic error calling {method_name}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error calling contract method {method_name}: {e}")
            raise
    
    def get_token_balance(self, token_address: str, wallet_address: str) -> int:
        """Get token balance for a given wallet address."""
        def _get_token_balance(web3, token_address, wallet_address):
            token_abi = self.settings.contracts.get('erc20_abi', [])
            contract = self.get_contract_instance(token_address, token_abi, web3)
            checksum_wallet_address = self._to_checksum_address(wallet_address, web3)
            return contract.functions.balanceOf(checksum_wallet_address).call()
        
        try:
            if self.load_balancer:
                return self.load_balancer.execute_request(_get_token_balance, token_address, wallet_address)
            else:
                return _get_token_balance(self.web3, token_address, wallet_address)
        except Exception as e:
            self.logger.error(f"Error getting token balance: {e}")
            raise
    
    def get_logs(self, address: str, topics: Optional[List[str]] = None, from_block: int = 0, to_block: str = 'latest') -> List[Dict[str, Any]]:
        """Get logs for a given address and topics."""
        def _get_logs(web3, address, topics, from_block, to_block):
            filter_params = {
                "address": self._to_checksum_address(address, web3),
                "fromBlock": from_block,
                "toBlock": to_block,
            }
            if topics:
                filter_params["topics"] = topics

            logs = web3.eth.get_logs(filter_params)
            return [self._format_log(log) for log in logs]
        
        try:
            if self.load_balancer:
                return self.load_balancer.execute_request(_get_logs, address, topics, from_block, to_block)
            else:
                return _get_logs(self.web3, address, topics, from_block, to_block)
        except Exception as e:
            if "BadResponse" in str(type(e)):
                self.logger.error(f"Error getting logs: {e}")
            else:
                self.logger.error(f"Error getting logs: {e}")
            raise
    
    def _to_checksum_address(self, address: str, web3: Web3 = None) -> ChecksumAddress:
        """Convert address to checksum address."""
        if web3 is None:
            web3 = self.web3
        if not web3.is_checksum_address(address):
            return web3.to_checksum_address(address)
        return ChecksumAddress(address)
    
    def _format_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Format log entry to be more readable."""
        formatted_log = {
            "block_number": log.blockNumber,
            "transaction_hash": log.transactionHash.hex(),
            "address": log.address,
            "topics": [topic.hex() for topic in log.topics],
            "data": log.data,
        }
        return formatted_log
    
    def get_token_info(self, token_address: str) -> Dict[str, Any]:
        """Get token information (name, symbol, decimals, total supply)."""
        def _get_token_info(web3, token_address):
            token_abi = self.settings.contracts.get('erc20_abi', [])
            contract = self.get_contract_instance(token_address, token_abi, web3)
            
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            total_supply = contract.functions.totalSupply().call()
            
            return {
                'name': name,
                'symbol': symbol,
                'decimals': decimals,
                'total_supply': total_supply
            }
        
        try:
            if self.load_balancer:
                return self.load_balancer.execute_request(_get_token_info, token_address)
            else:
                return _get_token_info(self.web3, token_address)
        except Exception as e:
            self.logger.error(f"Error getting token info: {e}")
            raise
    
    def get_eth_price_usd(self) -> float:
        """Get current ETH price in USD using price oracle."""
        try:
            from .price_oracle import PriceOracle
            oracle = PriceOracle()
            return oracle.get_eth_price_usd()
        except Exception as e:
            self.logger.error(f"Error getting ETH price: {e}")
            return 2000.0  # Fallback value
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the RPC client."""
        if self.load_balancer:
            return self.load_balancer.get_status()
        else:
            return {
                'mode': 'single_provider',
                'provider': self.rpc_url if hasattr(self, 'rpc_url') else 'unknown',
                'is_connected': self.web3.is_connected() if self.web3 else False
            }
    
    def get_health_report(self) -> str:
        """Get a formatted health report."""
        if self.load_balancer:
            return self.load_balancer.get_health_report()
        else:
            status = "✅ Connected" if self.web3.is_connected() else "❌ Disconnected"
            return f"RPC Client Status: {status}\nProvider: {getattr(self, 'rpc_url', 'unknown')}"
    
    def reset_provider(self, provider_name: str = None):
        """Reset a specific provider or all providers."""
        if self.load_balancer:
            if provider_name:
                self.load_balancer.reset_provider(provider_name)
            else:
                # Reset all providers
                for provider in self.load_balancer.providers:
                    provider.is_healthy = True
                    provider.error_count = 0
                    provider.last_error = None
                self.logger.info("Reset all RPC providers")
        else:
            self.logger.warning("No load balancer available to reset providers")

"""
ROKO token analyzer for extracting detailed token information and pricing data.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from web3 import Web3
from .enhanced_rpc_client import EnhancedEthereumRPCClient


class ROKOTokenAnalyzer:
    """Analyzer for ROKO token data and pricing information."""
    
    def __init__(self, rpc_client: EnhancedEthereumRPCClient, roko_address: str):
        """
        Initialize the ROKO token analyzer.
        
        Args:
            rpc_client: Ethereum RPC client instance
            roko_address: ROKO token contract address
        """
        self.rpc_client = rpc_client
        self.roko_address = roko_address
        self.logger = logging.getLogger(__name__)
        
        # ERC-20 ABI for token functions
        self.erc20_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "owner",
                "outputs": [{"name": "", "type": "address"}],
                "type": "function"
            }
        ]
    
    def get_token_metadata(self) -> Dict[str, Any]:
        """Get basic token metadata."""
        try:
            token_info = self.rpc_client.get_token_info(self.roko_address)
            
            return {
                'address': self.roko_address,
                'name': token_info['name'],
                'symbol': token_info['symbol'],
                'decimals': token_info['decimals'],
                'total_supply': token_info['total_supply'],
                'total_supply_formatted': token_info['total_supply'] / (10 ** token_info['decimals'])
            }
        except Exception as e:
            self.logger.error(f"Error getting token metadata: {e}")
            raise
    
    def get_current_price_eth(self) -> float:
        """
        Get current ROKO price in ETH using price oracle.
        """
        try:
            from .price_oracle import PriceOracle
            oracle = PriceOracle()
            
            # Get comprehensive pricing data
            pricing_data = oracle.get_comprehensive_pricing(
                self.roko_address, 
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                self.rpc_client
            )
            
            return pricing_data.get('token_price_eth', 0.0)
        except Exception as e:
            self.logger.error(f"Error getting ROKO price in ETH: {e}")
            return 0.0
    
    def get_current_price_usd(self) -> float:
        """Get current ROKO price in USD using price oracle."""
        try:
            from .price_oracle import PriceOracle
            oracle = PriceOracle()
            
            # Get comprehensive pricing data
            pricing_data = oracle.get_comprehensive_pricing(
                self.roko_address, 
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH
                self.rpc_client
            )
            
            return pricing_data.get('usd_per_token', 0.0)
        except Exception as e:
            self.logger.error(f"Error getting ROKO price in USD: {e}")
            return 0.0
    
    def get_market_cap(self) -> float:
        """Get market capitalization in USD."""
        try:
            metadata = self.get_token_metadata()
            price_usd = self.get_current_price_usd()
            total_supply = metadata['total_supply_formatted']
            return price_usd * total_supply
        except Exception as e:
            self.logger.error(f"Error calculating market cap: {e}")
            return 0.0
    
    def get_circulating_supply(self) -> int:
        """Get circulating supply by excluding treasury wallets from total supply."""
        try:
            from config.settings import Config
            config = Config()
            treasury_wallets = config.get_treasury_wallets()
            
            if not treasury_wallets:
                # No treasury wallets configured, return total supply
                metadata = self.get_token_metadata()
                return metadata['total_supply']
            
            # Get total supply
            total_supply = self.get_total_supply()
            
            # Calculate treasury holdings
            treasury_holdings = 0
            for wallet in treasury_wallets:
                try:
                    balance = self.rpc_client.get_token_balance(self.roko_address, wallet)
                    treasury_holdings += balance
                    self.logger.debug(f"Treasury wallet {wallet}: {balance} tokens")
                except Exception as e:
                    self.logger.warning(f"Error getting balance for treasury wallet {wallet}: {e}")
            
            # Calculate circulating supply
            circulating_supply = total_supply - treasury_holdings
            self.logger.info(f"Total supply: {total_supply}, Treasury holdings: {treasury_holdings}, Circulating supply: {circulating_supply}")
            
            return max(0, circulating_supply)  # Ensure non-negative
            
        except Exception as e:
            self.logger.error(f"Error getting circulating supply: {e}")
            # Fallback to total supply
            metadata = self.get_token_metadata()
            return metadata['total_supply']
    
    def get_total_supply(self) -> int:
        """Get total supply."""
        try:
            return self.rpc_client.get_token_supply(self.roko_address)
        except Exception as e:
            self.logger.error(f"Error getting total supply: {e}")
            return 0
    
    def get_holder_count(self) -> int:
        """
        Get holder count using Alchemy API for efficiency.
        Falls back to RPC method if Alchemy is not available.
        """
        try:
            # Try Alchemy first (much faster and more accurate)
            alchemy_count = self._get_holder_count_alchemy()
            if alchemy_count is not None:
                return alchemy_count
            
            # Fallback to RPC method
            return self._get_holder_count_rpc()
            
        except Exception as e:
            self.logger.error(f"Error getting holder count: {e}")
            return 0
    
    def _get_holder_count_alchemy(self) -> Optional[int]:
        """Get holder count using Alchemy API."""
        try:
            import requests
            import os
            
            # Get Alchemy API key from environment
            api_key = os.getenv('ALCHEMY_API_KEY')
            if not api_key:
                self.logger.debug("No Alchemy API key found, skipping Alchemy holder count")
                return None
            
            # Use Alchemy's getOwnersForToken method
            url = f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
            
            payload = {
                "jsonrpc": "2.0",
                "method": "alchemy_getOwnersForToken",
                "params": {
                    "contractAddress": self.roko_address
                },
                "id": 1
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'result' in data and 'owners' in data['result']:
                holder_count = len(data['result']['owners'])
                self.logger.info(f"Holder count from Alchemy: {holder_count}")
                return holder_count
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Alchemy holder count failed: {e}")
            return None
    
    def _get_holder_count_rpc(self) -> int:
        """
        Get approximate holder count by analyzing Transfer events (RPC fallback).
        This is a simplified implementation.
        """
        try:
            # Get Transfer events from the last 1000 blocks
            latest_block = self.rpc_client.get_latest_block()
            from_block = max(0, latest_block['number'] - 1000)
            
            # Transfer event signature: Transfer(address indexed from, address indexed to, uint256 value)
            transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            
            logs = self.rpc_client.get_logs(
                from_block=from_block,
                to_block='latest',
                address=self.roko_address,
                topics=[transfer_topic]
            )
            
            # Count unique addresses from Transfer events
            unique_addresses = set()
            for log in logs:
                if len(log['topics']) >= 3:
                    from_addr = "0x" + log['topics'][1][-40:]  # Extract from address
                    to_addr = "0x" + log['topics'][2][-40:]    # Extract to address
                    unique_addresses.add(from_addr)
                    unique_addresses.add(to_addr)
            
            self.logger.info(f"Holder count from RPC (approximate): {len(unique_addresses)}")
            return len(unique_addresses)
        except Exception as e:
            self.logger.error(f"Error getting holder count from RPC: {e}")
            return 0
    
    def get_transaction_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent transaction history."""
        try:
            latest_block = self.rpc_client.get_latest_block()
            from_block = max(0, latest_block['number'] - 1000)
            
            # Transfer event signature
            transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            
            logs = self.rpc_client.get_logs(
                from_block=from_block,
                to_block='latest',
                address=self.roko_address,
                topics=[transfer_topic]
            )
            
            transactions = []
            for log in logs[:limit]:
                if len(log['topics']) >= 3:
                    from_addr = "0x" + log['topics'][1][-40:]
                    to_addr = "0x" + log['topics'][2][-40:]
                    
                    # Decode the value from the data field
                    value_hex = log['data'][2:]  # Remove '0x' prefix
                    value = int(value_hex, 16) if value_hex else 0
                    
                    transactions.append({
                        'from': from_addr,
                        'to': to_addr,
                        'value': value,
                        'block_number': log['block_number'],
                        'transaction_hash': log['transaction_hash'],
                        'log_index': log['log_index']
                    })
            
            return transactions
        except Exception as e:
            self.logger.error(f"Error getting transaction history: {e}")
            return []
    
    def get_comprehensive_data(self) -> Dict[str, Any]:
        """Get comprehensive token data."""
        try:
            metadata = self.get_token_metadata()
            price_eth = self.get_current_price_eth()
            price_usd = self.get_current_price_usd()
            market_cap = self.get_market_cap()
            holder_count = self.get_holder_count()
            
            return {
                'timestamp': int(time.time()),
                'token_metadata': metadata,
                'pricing': {
                    'eth_per_token': price_eth,
                    'usd_per_token': price_usd,
                    'market_cap_usd': market_cap
                },
                'supply': {
                    'total_supply': metadata['total_supply'],
                    'total_supply_formatted': metadata['total_supply_formatted'],
                    'circulating_supply': self.get_circulating_supply()
                },
                'holders': {
                    'count': holder_count
                },
                'recent_transactions': self.get_transaction_history(10)
            }
        except Exception as e:
            self.logger.error(f"Error getting comprehensive data: {e}")
            raise

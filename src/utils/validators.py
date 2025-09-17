"""
Validation utilities for token and pool data.
"""

import re
import logging
from typing import Any, Dict, List, Optional
from web3 import Web3


class DataValidator:
    """Validator for token and pool data."""
    
    def __init__(self):
        """Initialize the validator."""
        self.logger = logging.getLogger(__name__)
    
    def is_valid_ethereum_address(self, address: str) -> bool:
        """
        Validate Ethereum address format.
        
        Args:
            address: Address to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not address or not isinstance(address, str):
                return False
            
            # Check if it's a valid checksum address
            return Web3.is_address(address)
            
        except Exception as e:
            self.logger.debug(f"Error validating address {address}: {e}")
            return False
    
    def is_valid_contract_address(self, address: str) -> bool:
        """
        Validate that an address is a contract (not EOA).
        
        Args:
            address: Address to validate
            
        Returns:
            True if valid contract address, False otherwise
        """
        try:
            if not self.is_valid_ethereum_address(address):
                return False
            
            # This is a simplified check
            # In production, you'd want to check if the address has code
            return len(address) == 42 and address.startswith('0x')
            
        except Exception as e:
            self.logger.debug(f"Error validating contract address {address}: {e}")
            return False
    
    def validate_token_data(self, token_data: Dict[str, Any]) -> bool:
        """
        Validate token data structure and values.
        
        Args:
            token_data: Token data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            required_fields = ['token_metadata', 'pricing', 'supply']
            
            for field in required_fields:
                if field not in token_data:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate token metadata
            metadata = token_data.get('token_metadata', {})
            if not all(key in metadata for key in ['name', 'symbol', 'address', 'decimals']):
                self.logger.error("Invalid token metadata structure")
                return False
            
            # Validate address
            if not self.is_valid_ethereum_address(metadata.get('address', '')):
                self.logger.error("Invalid token address")
                return False
            
            # Validate pricing data
            pricing = token_data.get('pricing', {})
            if not all(isinstance(pricing.get(key), (int, float)) for key in ['price_eth', 'price_usd', 'market_cap_usd']):
                self.logger.error("Invalid pricing data types")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating token data: {e}")
            return False
    
    def validate_pool_data(self, pool_data: Dict[str, Any]) -> bool:
        """
        Validate pool data structure and values.
        
        Args:
            pool_data: Pool data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            required_fields = ['pool_address', 'reserves', 'tvl_usd']
            
            for field in required_fields:
                if field not in pool_data:
                    self.logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate pool address
            if not self.is_valid_ethereum_address(pool_data.get('pool_address', '')):
                self.logger.error("Invalid pool address")
                return False
            
            # Validate reserves
            reserves = pool_data.get('reserves', {})
            if not all(isinstance(reserves.get(key), int) for key in ['reserve0', 'reserve1']):
                self.logger.error("Invalid reserves data types")
                return False
            
            # Validate numeric values
            numeric_fields = ['tvl_usd', 'volume_24h', 'fees_24h']
            for field in numeric_fields:
                if field in pool_data and not isinstance(pool_data[field], (int, float)):
                    self.logger.error(f"Invalid {field} data type")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating pool data: {e}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration data.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            required_sections = ['ethereum', 'roko_token', 'monitoring', 'pools']
            
            for section in required_sections:
                if section not in config:
                    self.logger.error(f"Missing required config section: {section}")
                    return False
            
            # Validate Ethereum config
            ethereum = config.get('ethereum', {})
            if 'rpc_url' not in ethereum:
                self.logger.error("Missing RPC URL in Ethereum config")
                return False
            
            # Validate ROKO token config
            roko_token = config.get('roko_token', {})
            if not self.is_valid_ethereum_address(roko_token.get('address', '')):
                self.logger.error("Invalid ROKO token address")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating config: {e}")
            return False
    
    def sanitize_string(self, value: str) -> str:
        """
        Sanitize string values for safe display.
        
        Args:
            value: String to sanitize
            
        Returns:
            Sanitized string
        """
        try:
            if not isinstance(value, str):
                return str(value)
            
            # Remove potentially dangerous characters
            sanitized = re.sub(r'[<>"\']', '', value)
            return sanitized.strip()
            
        except Exception as e:
            self.logger.error(f"Error sanitizing string: {e}")
            return str(value) if value else ""
    
    def validate_numeric_range(self, value: Any, min_val: float = None, max_val: float = None) -> bool:
        """
        Validate that a numeric value is within a specified range.
        
        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if not isinstance(value, (int, float)):
                return False
            
            if min_val is not None and value < min_val:
                return False
            
            if max_val is not None and value > max_val:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating numeric range: {e}")
            return False

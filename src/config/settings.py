"""
Configuration settings and management for the ROKO token data extractor.
"""

import os
import yaml
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration manager for the ROKO token data extractor."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize configuration from YAML file."""
        self.config_path = Path(config_path)
        
        # Load environment variables from .env file
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
        
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with environment variable expansion."""
        try:
            with open(self.config_path, 'r') as file:
                content = file.read()
            
            # Expand environment variables
            content = os.path.expandvars(content)
            
            config = yaml.safe_load(content)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    @property
    def ethereum(self) -> Dict[str, Any]:
        """Get Ethereum configuration."""
        return self._config.get('ethereum', {})
    
    @property
    def token(self) -> Dict[str, Any]:
        """Get token configuration."""
        return self._config.get('token', {})
    
    @property
    def stablecoins(self) -> Dict[str, Any]:
        """Get stablecoins configuration."""
        return self._config.get('stablecoins', {})
    
    @property
    def monitoring(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self._config.get('monitoring', {})
    
    @property
    def pools(self) -> Dict[str, Any]:
        """Get pools configuration."""
        return self._config.get('pools', {})
    
    @property
    def contracts(self) -> Dict[str, Any]:
        """Get contracts configuration."""
        return self._config.get('contracts', {})
    
    def get_rpc_url(self) -> str:
        """Get the RPC URL with API key substitution (legacy mode)."""
        rpc_url = self.ethereum.get('rpc_url', '')
        api_key = os.getenv('ALCHEMY_API_KEY') or self.ethereum.get('api_key', '')

        if '{API_KEY}' in rpc_url and api_key:
            rpc_url = rpc_url.replace('{API_KEY}', api_key)
        elif '{API_KEY}' in rpc_url and not api_key:
            # Use the URL as-is if no API key is provided (for public RPCs)
            pass

        return rpc_url
    
    def get_rpc_providers(self) -> List[Dict[str, Any]]:
        """Get the list of RPC providers for load balancing."""
        providers = self.ethereum.get('rpc_providers', [])
        
        # Process API key substitution for each provider
        for provider in providers:
            # Handle API key substitution
            api_key_var = provider.get('api_key', '')
            if api_key_var.startswith('${') and api_key_var.endswith('}'):
                env_var = api_key_var[2:-1]  # Remove ${ and }
                api_key = os.getenv(env_var, '')
                provider['api_key'] = api_key
            
            # Handle URL API key substitution
            if '{API_KEY}' in provider.get('url', ''):
                if provider.get('api_key'):
                    provider['url'] = provider['url'].replace('{API_KEY}', provider['api_key'])
                else:
                    # If no API key, remove the placeholder
                    provider['url'] = provider['url'].replace('{API_KEY}', '')
        
        return providers
    
    def get_load_balancing_config(self) -> Dict[str, Any]:
        """Get load balancing configuration."""
        return self.ethereum.get('load_balancing', {})
    
    def get_token_address(self) -> str:
        """Get the token contract address."""
        return self.token.get('address', '0x6f222e04f6c53cc688ffb0abe7206aac66a8ff98')
    
    def get_token_name(self) -> str:
        """Get the token name."""
        return self.token.get('name', 'ROKO')
    
    def get_token_symbol(self) -> str:
        """Get the token symbol."""
        return self.token.get('symbol', 'ROKO')
    
    def get_token_decimals(self) -> int:
        """Get the token decimals."""
        return self.token.get('decimals', 18)
    
    def get_treasury_wallets(self) -> List[str]:
        """Get the list of treasury wallets to exclude from circulating supply."""
        treasury_wallets_str = self.token.get('treasury_wallets', '')
        if treasury_wallets_str:
            # Split by comma and clean up whitespace
            return [wallet.strip() for wallet in treasury_wallets_str.split(',') if wallet.strip()]
        return []
    
    def get_usdc_address(self) -> str:
        """Get the USDC contract address."""
        return self.stablecoins.get('usdc_address', '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48')
    
    def get_usdt_address(self) -> str:
        """Get the USDT contract address."""
        return self.stablecoins.get('usdt_address', '0xdAC17F958D2ee523a2206206994597C13D831ec7')
    
    def get_weth_address(self) -> str:
        """Get the WETH contract address."""
        return self.stablecoins.get('weth_address', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2')
    
    def get_uniswap_v2_factory(self) -> str:
        """Get the Uniswap V2 factory address."""
        return self.pools.get('uniswap_v2_factory', '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f')
    
    def get_uniswap_v3_factory(self) -> str:
        """Get the Uniswap V3 factory address."""
        return self.pools.get('uniswap_v3_factory', '0x1F98431c8aD98523631AE4a59f267346ea31F984')
    
    def get_update_interval(self) -> int:
        """Get the monitoring update interval in seconds."""
        return self.monitoring.get('update_interval', 30)
    
    def get_log_level(self) -> str:
        """Get the logging level."""
        return self.monitoring.get('log_level', 'INFO')
    
    def get_export_formats(self) -> list:
        """Get the export formats."""
        return self.monitoring.get('export_format', ['json', 'csv'])


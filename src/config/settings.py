"""
Configuration settings and management for the ROKO token data extractor.
"""

import os
import yaml
from typing import Dict, Any, List
from pathlib import Path


class Config:
    """Configuration manager for the ROKO token data extractor."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize configuration from YAML file."""
        self.config_path = Path(config_path)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
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
    def roko_token(self) -> Dict[str, Any]:
        """Get ROKO token configuration."""
        return self._config.get('roko_token', {})
    
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
    
    def get_roko_address(self) -> str:
        """Get the ROKO token contract address."""
        return self.roko_token.get('address', '0x6f222e04f6c53cc688ffb0abe7206aac66a8ff98')
    
    def get_update_interval(self) -> int:
        """Get the monitoring update interval in seconds."""
        return self.monitoring.get('update_interval', 30)
    
    def get_log_level(self) -> str:
        """Get the logging level."""
        return self.monitoring.get('log_level', 'INFO')
    
    def get_export_formats(self) -> list:
        """Get the export formats."""
        return self.monitoring.get('export_format', ['json', 'csv'])


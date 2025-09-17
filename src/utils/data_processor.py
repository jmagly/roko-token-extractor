"""
Data processing utilities for token and pool data.
"""

import json
import csv
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path


class DataProcessor:
    """Data processor for handling token and pool data."""
    
    def __init__(self, export_dir: str = "data/exports"):
        """
        Initialize the data processor.
        
        Args:
            export_dir: Directory for data exports
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def export_to_json(self, data: Dict[str, Any], filename: str) -> str:
        """
        Export data to JSON file.
        
        Args:
            data: Data to export
            filename: Output filename
            
        Returns:
            Path to the exported file
        """
        try:
            filepath = self.export_dir / f"{filename}.json"
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Data exported to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error exporting to JSON: {e}")
            raise
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str) -> str:
        """
        Export data to CSV file.
        
        Args:
            data: List of dictionaries to export
            filename: Output filename
            
        Returns:
            Path to the exported file
        """
        try:
            if not data:
                self.logger.warning("No data to export to CSV")
                return ""
            
            filepath = self.export_dir / f"{filename}.csv"
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            self.logger.info(f"Data exported to {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def format_token_data(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format token data for display and export.
        
        Args:
            token_data: Raw token data
            
        Returns:
            Formatted token data
        """
        try:
            formatted = {
                'timestamp': datetime.fromtimestamp(token_data.get('timestamp', 0)).isoformat(),
                'token_info': {
                    'name': token_data.get('token_metadata', {}).get('name', ''),
                    'symbol': token_data.get('token_metadata', {}).get('symbol', ''),
                    'address': token_data.get('token_metadata', {}).get('address', ''),
                    'decimals': token_data.get('token_metadata', {}).get('decimals', 0),
                    'total_supply': token_data.get('token_metadata', {}).get('total_supply_formatted', 0)
                },
                'pricing': {
                    'price_eth': f"{token_data.get('pricing', {}).get('price_eth', 0):.8f}",
                    'price_usd': f"${token_data.get('pricing', {}).get('price_usd', 0):.6f}",
                    'market_cap_usd': f"${token_data.get('pricing', {}).get('market_cap_usd', 0):,.2f}"
                },
                'supply': {
                    'total_supply': f"{token_data.get('supply', {}).get('total_supply_formatted', 0):,.0f}",
                    'circulating_supply': f"{token_data.get('supply', {}).get('circulating_supply', 0):,.0f}"
                },
                'holders': {
                    'count': token_data.get('holders', {}).get('count', 0)
                }
            }
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"Error formatting token data: {e}")
            return token_data
    
    def format_pool_data(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format pool data for display and export.
        
        Args:
            pool_data: Raw pool data
            
        Returns:
            Formatted pool data
        """
        try:
            formatted = {
                'timestamp': datetime.fromtimestamp(pool_data.get('timestamp', 0)).isoformat(),
                'pool_address': pool_data.get('pool_address', ''),
                'reserves': {
                    'token0_reserve': f"{pool_data.get('reserves', {}).get('reserve0', 0):,.0f}",
                    'token1_reserve': f"{pool_data.get('reserves', {}).get('reserve1', 0):,.0f}",
                    'token0_address': pool_data.get('reserves', {}).get('token0', ''),
                    'token1_address': pool_data.get('reserves', {}).get('token1', '')
                },
                'liquidity': {
                    'total_liquidity_usd': f"${pool_data.get('liquidity_usd', 0):,.2f}"
                },
                'trading': {
                    'volume_24h': f"${pool_data.get('volume_24h', 0):,.2f}",
                    'fees_24h': f"${pool_data.get('fees_24h', 0):,.2f}"
                }
            }
            
            return formatted
            
        except Exception as e:
            self.logger.error(f"Error formatting pool data: {e}")
            return pool_data
    
    def create_summary_report(self, token_data: Dict[str, Any], pool_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a summary report combining token and pool data.
        
        Args:
            token_data: Token data
            pool_data: List of pool data
            
        Returns:
            Summary report
        """
        try:
            total_liquidity = sum(pool.get('liquidity_usd', 0) for pool in pool_data)
            total_volume_24h = sum(pool.get('volume_24h', 0) for pool in pool_data)
            total_fees_24h = sum(pool.get('fees_24h', 0) for pool in pool_data)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_pools': len(pool_data),
                    'total_liquidity_usd': total_liquidity,
                    'total_volume_24h_usd': total_volume_24h,
                    'total_fees_24h_usd': total_fees_24h
                },
                'token_data': self.format_token_data(token_data),
                'pool_data': [self.format_pool_data(pool) for pool in pool_data]
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error creating summary report: {e}")
            raise

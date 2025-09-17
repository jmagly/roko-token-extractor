"""
Main script for ROKO token data extractor.
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from config.settings import Config
from core.enhanced_rpc_client import EnhancedEthereumRPCClient
from core.token_analyzer import ROKOTokenAnalyzer
from core.pool_monitor import UniswapPoolMonitor
from core.analytics import TokenAnalytics
from core.historical_tracker import HistoricalTracker
from core.help_system import HelpSystem
from utils.data_processor import DataProcessor
from utils.validators import DataValidator


class ROKODataExtractor:
    """Main class for ROKO token data extraction."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the ROKO data extractor.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = Config(config_path)
        self.validator = DataValidator()
        self.data_processor = DataProcessor()
        
        # Initialize enhanced RPC client with load balancing
        self.rpc_client = EnhancedEthereumRPCClient(use_load_balancer=True)
        
        # Initialize analyzers
        self.token_analyzer = ROKOTokenAnalyzer(
            rpc_client=self.rpc_client,
            roko_address=self.config.get_token_address()
        )
        
        self.pool_monitor = UniswapPoolMonitor(
            rpc_client=self.rpc_client,
            roko_address=self.config.get_token_address(),
            uniswap_v2_factory=self.config.get_uniswap_v2_factory(),
            uniswap_v3_factory=self.config.get_uniswap_v3_factory(),
            weth_address=self.config.get_weth_address()
        )
        
        # Initialize analytics and historical tracking
        self.analytics = TokenAnalytics(
            rpc_client=self.rpc_client,
            token_address=self.config.get_token_address()
        )
        
        self.historical_tracker = HistoricalTracker()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.get_log_level().upper())
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/roko_extractor.log'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("ROKO Data Extractor initialized")
    
    def extract_token_data(self) -> Dict[str, Any]:
        """Extract comprehensive token data."""
        try:
            self.logger.info("Extracting ROKO token data...")
            
            token_data = self.token_analyzer.get_comprehensive_data()
            
            # Validate data
            if not self.validator.validate_token_data(token_data):
                self.logger.error("Token data validation failed")
                return {}
            
            self.logger.info("Token data extracted successfully")
            return token_data
            
        except Exception as e:
            self.logger.error(f"Error extracting token data: {e}")
            return {}
    
    def extract_pool_data(self) -> List[Dict[str, Any]]:
        """Extract TVL pool data."""
        try:
            self.logger.info("Extracting TVL pool data...")
            
            # Find ROKO pools
            pools = self.pool_monitor.find_roko_pools()
            
            if not pools:
                self.logger.warning("No ROKO pools found")
                return []
            
            pool_data = []
            for pool in pools:
                try:
                    pool_info = self.pool_monitor.get_pool_comprehensive_data(pool['address'])
                    
                    # Validate data
                    if self.validator.validate_pool_data(pool_info):
                        pool_data.append(pool_info)
                    else:
                        self.logger.warning(f"Pool data validation failed for {pool['address']}")
                        
                except Exception as e:
                    self.logger.error(f"Error processing pool {pool['address']}: {e}")
                    continue
            
            self.logger.info(f"Extracted data for {len(pool_data)} pools")
            return pool_data
            
        except Exception as e:
            self.logger.error(f"Error extracting pool data: {e}")
            return []
    
    def run_extraction(self, export_formats: List[str] = None, include_analytics: bool = False) -> Dict[str, Any]:
        """
        Run the complete data extraction process.
        
        Args:
            export_formats: List of export formats (json, csv)
            include_analytics: Whether to include advanced analytics
            
        Returns:
            Summary of extracted data
        """
        try:
            self.logger.info("Starting ROKO data extraction...")
            
            # Extract token data
            token_data = self.extract_token_data()
            if not token_data:
                self.logger.error("Failed to extract token data")
                return {}
            
            # Extract pool data
            pool_data = self.extract_pool_data()
            
            # Store historical data
            self._store_historical_data(token_data, pool_data)
            
            # Create summary report
            summary = self.data_processor.create_summary_report(token_data, pool_data)
            
            # Add analytics if requested
            if include_analytics:
                self.logger.info("Running advanced analytics...")
                analytics_data = self.analytics.get_comprehensive_analytics()
                summary['analytics'] = analytics_data
                
                # Store analytics data
                self._store_analytics_data(analytics_data)
            
            # Export data if requested
            if export_formats:
                self._export_data(summary, export_formats)
            
            # Always export price data to a dedicated file
            self._export_price_data(token_data)
            
            self.logger.info("Data extraction completed successfully")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error in data extraction: {e}")
            return {}
    
    def _export_data(self, data: Dict[str, Any], formats: List[str]):
        """Export data in specified formats."""
        try:
            timestamp = data.get('timestamp', '').replace(':', '-').replace('T', '_').split('.')[0]
            
            for format_type in formats:
                if format_type.lower() == 'json':
                    self.data_processor.export_to_json(
                        data, f"roko_data_{timestamp}"
                    )
                elif format_type.lower() == 'csv':
                    # Export token data as CSV
                    token_csv_data = [data.get('token_data', {})]
                    self.data_processor.export_to_csv(
                        token_csv_data, f"roko_token_{timestamp}"
                    )
                    
                    # Export pool data as CSV
                    if data.get('pool_data'):
                        self.data_processor.export_to_csv(
                            data['pool_data'], f"roko_pools_{timestamp}"
                        )
            
            self.logger.info(f"Data exported in formats: {', '.join(formats)}")
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
    
    def _export_price_data(self, token_data: Dict[str, Any]):
        """Export price data to a dedicated file."""
        try:
            import json
            import time
            from pathlib import Path
            
            # Create data/exports directory if it doesn't exist
            export_dir = Path("data/exports")
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract pricing data
            pricing = token_data.get('pricing', {})
            token_metadata = token_data.get('token_metadata', {})
            
            # Create price data structure
            price_data = {
                'timestamp': int(time.time()),
                'datetime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                'token': {
                    'name': token_metadata.get('name', 'N/A'),
                    'symbol': token_metadata.get('symbol', 'N/A'),
                    'address': token_metadata.get('address', 'N/A'),
                    'decimals': token_metadata.get('decimals', 'N/A'),
                    'total_supply': token_metadata.get('total_supply', 'N/A'),
                    'total_supply_formatted': token_metadata.get('total_supply_formatted', 'N/A')
                },
                'pricing': {
                    'price_eth': pricing.get('price_eth', 'N/A'),
                    'price_usd': pricing.get('price_usd', 'N/A'),
                    'eth_price_usd': pricing.get('eth_price_usd', 'N/A'),
                    'price_source': pricing.get('price_source', 'N/A'),
                    'market_cap_usd': pricing.get('market_cap_usd', 'N/A')
                },
                'all_prices': pricing.get('all_prices', {}),
                'price_sources': pricing.get('price_sources', [])
            }
            
            # Generate filename with timestamp
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"roko_price_data_{timestamp}.json"
            filepath = export_dir / filename
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(price_data, f, indent=2)
            
            self.logger.info(f"Price data exported to: {filepath}")
            
            # Also create a CSV version for easy viewing
            csv_filename = f"roko_price_data_{timestamp}.csv"
            csv_filepath = export_dir / csv_filename
            
            with open(csv_filepath, 'w') as f:
                f.write("Metric,Value\n")
                f.write(f"Timestamp,{price_data['datetime']}\n")
                f.write(f"Token Name,{price_data['token']['name']}\n")
                f.write(f"Token Symbol,{price_data['token']['symbol']}\n")
                f.write(f"Token Address,{price_data['token']['address']}\n")
                f.write(f"Decimals,{price_data['token']['decimals']}\n")
                f.write(f"Total Supply,{price_data['token']['total_supply_formatted']}\n")
                f.write(f"Price (ETH),{price_data['pricing']['price_eth']}\n")
                f.write(f"Price (USD),{price_data['pricing']['price_usd']}\n")
                f.write(f"ETH Price (USD),{price_data['pricing']['eth_price_usd']}\n")
                f.write(f"Price Source,{price_data['pricing']['price_source']}\n")
                f.write(f"Market Cap (USD),{price_data['pricing']['market_cap_usd']}\n")
            
            self.logger.info(f"Price data CSV exported to: {csv_filepath}")
            
        except Exception as e:
            self.logger.error(f"Error exporting price data: {e}")
    
    def monitor_real_time(self, interval: int = None):
        """
        Start real-time monitoring.
        
        Args:
            interval: Monitoring interval in seconds
        """
        try:
            if interval is None:
                interval = self.config.get_update_interval()
            
            self.logger.info(f"Starting real-time monitoring (interval: {interval}s)")
            
            import time
            
            while True:
                try:
                    # Run extraction
                    summary = self.run_extraction(['json'])
                    
                    # Display summary
                    self._display_summary(summary)
                    
                    # Wait for next interval
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("Monitoring stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in monitoring cycle: {e}")
                    time.sleep(interval)
                    
        except Exception as e:
            self.logger.error(f"Error in real-time monitoring: {e}")
    
    def _display_summary(self, summary: Dict[str, Any]):
        """Display a summary of the extracted data."""
        try:
            print("\n" + "="*60)
            print("ROKO TOKEN DATA SUMMARY")
            print("="*60)
            
            # Token info
            token_info = summary.get('token_data', {}).get('token_info', {})
            print(f"Token: {token_info.get('name', 'N/A')} ({token_info.get('symbol', 'N/A')})")
            print(f"Address: {token_info.get('address', 'N/A')}")
            
            # Pricing
            pricing = summary.get('token_data', {}).get('pricing', {})
            price_eth = pricing.get('price_eth', 'N/A')
            price_usd = pricing.get('price_usd', 'N/A')
            market_cap = pricing.get('market_cap_usd', 'N/A')
            
            if isinstance(price_eth, (int, float)):
                print(f"Price (ETH): {price_eth:.8f} ETH")
            else:
                print(f"Price (ETH): {price_eth}")
                
            if isinstance(price_usd, (int, float)):
                print(f"Price (USD): ${price_usd:.6f}")
            else:
                print(f"Price (USD): {price_usd}")
                
            if isinstance(market_cap, (int, float)):
                print(f"Market Cap: ${market_cap:,.2f}")
            else:
                print(f"Market Cap: {market_cap}")
            
            # Supply
            supply = summary.get('token_data', {}).get('supply', {})
            total_supply_formatted = supply.get('total_supply_formatted', supply.get('total_supply', 'N/A'))
            if isinstance(total_supply_formatted, (int, float)):
                print(f"Total Supply: {total_supply_formatted:,.2f} ROKO")
            else:
                print(f"Total Supply: {total_supply_formatted}")
            print(f"Holders: {summary.get('token_data', {}).get('holders', {}).get('count', 'N/A')}")
            
            # Pool summary
            pool_summary = summary.get('summary', {})
            print(f"\nPools: {pool_summary.get('total_pools', 0)}")
            print(f"Total TVL: {pool_summary.get('total_tvl_usd', 0):,.2f} USD")
            print(f"24h Volume: {pool_summary.get('total_volume_24h_usd', 0):,.2f} USD")
            
            print("="*60)
            
        except Exception as e:
            self.logger.error(f"Error displaying summary: {e}")
    
    def _store_historical_data(self, token_data: Dict[str, Any], pool_data: List[Dict[str, Any]]):
        """Store data in historical database."""
        try:
            # Store price data
            pricing = token_data.get('pricing', {})
            if pricing.get('price_usd'):
                price_data = {
                    'timestamp': token_data.get('timestamp', int(time.time())),
                    'token_price_eth': pricing.get('price_eth'),
                    'token_price_usd': pricing.get('price_usd'),
                    'market_cap_usd': pricing.get('market_cap_usd'),
                    'price_sources': ['coingecko']  # Default source
                }
                self.historical_tracker.store_price_data(self.config.get_roko_address(), price_data)
            
            self.logger.info("Historical data stored successfully")
            
        except Exception as e:
            self.logger.error(f"Error storing historical data: {e}")
    
    def _store_analytics_data(self, analytics_data: Dict[str, Any]):
        """Store analytics data in historical database."""
        try:
            # Store holder data
            holders_data = analytics_data.get('token_holders', {})
            if holders_data:
                self.historical_tracker.store_holder_data(self.config.get_roko_address(), holders_data)
            
            # Store exchange data
            exchange_data = analytics_data.get('exchange_interactions', {})
            if exchange_data:
                self.historical_tracker.store_exchange_data(self.config.get_roko_address(), exchange_data)
            
            self.logger.info("Analytics data stored successfully")
            
        except Exception as e:
            self.logger.error(f"Error storing analytics data: {e}")
    
    def get_historical_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get historical data summary."""
        try:
            return self.historical_tracker.get_summary_statistics(self.config.get_roko_address(), days)
        except Exception as e:
            self.logger.error(f"Error getting historical summary: {e}")
            return {}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='ROKO Token Data Extractor')
    parser.add_argument('--config', default='config/config.yaml', help='Configuration file path')
    parser.add_argument('--export', nargs='+', choices=['json', 'csv'], help='Export formats')
    parser.add_argument('--monitor', action='store_true', help='Start real-time monitoring')
    parser.add_argument('--interval', type=int, help='Monitoring interval in seconds')
    parser.add_argument('--analytics', action='store_true', help='Include advanced analytics')
    parser.add_argument('--holders', action='store_true', help='Extract complete holder data (requires Alchemy API key)')
    parser.add_argument('--historical', type=int, metavar='DAYS', help='Show historical summary for N days')
    parser.add_argument('--help-detailed', nargs='?', const='basic', choices=['basic', 'detailed', 'examples', 'configuration', 'troubleshooting'], 
                       help='Show detailed help information (basic, detailed, examples, configuration, troubleshooting)')
    
    args = parser.parse_args()
    
    # Handle help requests
    if hasattr(args, 'help_detailed') and args.help_detailed is not None:
        help_system = HelpSystem()
        if args.help_detailed == 'basic':
            print(help_system.get_help())
        else:
            print(help_system.get_help(args.help_detailed))
        return
    
    try:
        # Initialize extractor
        extractor = ROKODataExtractor(args.config)
        
        if args.historical:
            # Show historical summary
            summary = extractor.get_historical_summary(args.historical)
            print("\n" + "="*60)
            print(f"HISTORICAL SUMMARY ({args.historical} days)")
            print("="*60)
            print(json.dumps(summary, indent=2, default=str))
            return
        
        if args.holders:
            # Run holder extraction
            print("🔍 Starting complete ROKO holder extraction...")
            print("This will extract all token holders using Alchemy API")
            print("="*60)
            
            import subprocess
            import sys
            
            try:
                # Run the holder extraction script
                result = subprocess.run([sys.executable, 'extract_holders.py'], 
                                      capture_output=False, text=True, check=True)
                print("\n✅ Holder extraction completed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Holder extraction failed: {e}")
                sys.exit(1)
            except FileNotFoundError:
                print("\n❌ Holder extraction script not found. Please ensure extract_holders.py is in the root directory.")
                sys.exit(1)
            return
        
        if args.monitor:
            # Start real-time monitoring
            extractor.monitor_real_time(args.interval)
        else:
            # Run single extraction
            summary = extractor.run_extraction(args.export, args.analytics)
            extractor._display_summary(summary)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

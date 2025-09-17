"""
Historical data tracking module for price and volume data.
"""

import json
import logging
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import time


class HistoricalTracker:
    """Track and store historical token data."""
    
    def __init__(self, db_path: str = "data/historical/token_data.db"):
        """
        Initialize the historical tracker.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create price history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS price_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_address TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        price_eth REAL,
                        price_usd REAL,
                        market_cap_usd REAL,
                        volume_24h REAL,
                        price_source TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create holder history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS holder_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_address TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        total_holders INTEGER,
                        top_10_percentage REAL,
                        top_100_percentage REAL,
                        gini_coefficient REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create exchange activity table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS exchange_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        token_address TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        exchange_name TEXT NOT NULL,
                        transaction_count INTEGER,
                        volume REAL,
                        unique_users INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_token_timestamp ON price_history(token_address, timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_holder_token_timestamp ON holder_history(token_address, timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange_token_timestamp ON exchange_activity(token_address, timestamp)')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def store_price_data(self, token_address: str, price_data: Dict[str, Any]) -> bool:
        """
        Store price data in the database.
        
        Args:
            token_address: Token contract address
            price_data: Price data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO price_history 
                    (token_address, timestamp, price_eth, price_usd, market_cap_usd, volume_24h, price_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    token_address,
                    price_data.get('timestamp', int(time.time())),
                    price_data.get('token_price_eth'),
                    price_data.get('token_price_usd'),
                    price_data.get('market_cap_usd'),
                    price_data.get('volume_24h'),
                    ','.join(price_data.get('price_sources', []))
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error storing price data: {e}")
            return False
    
    def store_holder_data(self, token_address: str, holder_data: Dict[str, Any]) -> bool:
        """
        Store holder data in the database.
        
        Args:
            token_address: Token contract address
            holder_data: Holder data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                concentration = holder_data.get('concentration_metrics', {})
                
                cursor.execute('''
                    INSERT INTO holder_history 
                    (token_address, timestamp, total_holders, top_10_percentage, top_100_percentage, gini_coefficient)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    token_address,
                    holder_data.get('scan_range', {}).get('to_block', int(time.time())),
                    holder_data.get('total_holders'),
                    concentration.get('top_10_percentage'),
                    concentration.get('top_100_percentage'),
                    concentration.get('gini_coefficient')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error storing holder data: {e}")
            return False
    
    def store_exchange_data(self, token_address: str, exchange_data: Dict[str, Any]) -> bool:
        """
        Store exchange activity data in the database.
        
        Args:
            token_address: Token contract address
            exchange_data: Exchange data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                exchange_breakdown = exchange_data.get('exchange_breakdown', {})
                timestamp = exchange_data.get('scan_range', {}).get('to_block', int(time.time()))
                
                for exchange_name, data in exchange_breakdown.items():
                    cursor.execute('''
                        INSERT INTO exchange_activity 
                        (token_address, timestamp, exchange_name, transaction_count, volume, unique_users)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        token_address,
                        timestamp,
                        exchange_name,
                        data.get('transaction_count'),
                        data.get('total_volume'),
                        data.get('unique_users')
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error storing exchange data: {e}")
            return False
    
    def get_price_history(self, token_address: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical price data.
        
        Args:
            token_address: Token contract address
            days: Number of days to retrieve
            
        Returns:
            List of price data dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Calculate timestamp for days ago
                cutoff_timestamp = int(time.time()) - (days * 24 * 60 * 60)
                
                cursor.execute('''
                    SELECT timestamp, price_eth, price_usd, market_cap_usd, volume_24h, price_source
                    FROM price_history
                    WHERE token_address = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                ''', (token_address, cutoff_timestamp))
                
                rows = cursor.fetchall()
                
                return [
                    {
                        'timestamp': row[0],
                        'price_eth': row[1],
                        'price_usd': row[2],
                        'market_cap_usd': row[3],
                        'volume_24h': row[4],
                        'price_source': row[5].split(',') if row[5] else []
                    }
                    for row in rows
                ]
                
        except Exception as e:
            self.logger.error(f"Error getting price history: {e}")
            return []
    
    def get_holder_history(self, token_address: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical holder data.
        
        Args:
            token_address: Token contract address
            days: Number of days to retrieve
            
        Returns:
            List of holder data dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_timestamp = int(time.time()) - (days * 24 * 60 * 60)
                
                cursor.execute('''
                    SELECT timestamp, total_holders, top_10_percentage, top_100_percentage, gini_coefficient
                    FROM holder_history
                    WHERE token_address = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                ''', (token_address, cutoff_timestamp))
                
                rows = cursor.fetchall()
                
                return [
                    {
                        'timestamp': row[0],
                        'total_holders': row[1],
                        'top_10_percentage': row[2],
                        'top_100_percentage': row[3],
                        'gini_coefficient': row[4]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            self.logger.error(f"Error getting holder history: {e}")
            return []
    
    def get_exchange_history(self, token_address: str, days: int = 30) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get historical exchange activity data.
        
        Args:
            token_address: Token contract address
            days: Number of days to retrieve
            
        Returns:
            Dictionary with exchange activity data by exchange
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_timestamp = int(time.time()) - (days * 24 * 60 * 60)
                
                cursor.execute('''
                    SELECT timestamp, exchange_name, transaction_count, volume, unique_users
                    FROM exchange_activity
                    WHERE token_address = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                ''', (token_address, cutoff_timestamp))
                
                rows = cursor.fetchall()
                
                # Group by exchange
                exchange_data = {}
                for row in rows:
                    exchange_name = row[1]
                    if exchange_name not in exchange_data:
                        exchange_data[exchange_name] = []
                    
                    exchange_data[exchange_name].append({
                        'timestamp': row[0],
                        'transaction_count': row[2],
                        'volume': row[3],
                        'unique_users': row[4]
                    })
                
                return exchange_data
                
        except Exception as e:
            self.logger.error(f"Error getting exchange history: {e}")
            return {}
    
    def get_summary_statistics(self, token_address: str, days: int = 30) -> Dict[str, Any]:
        """
        Get summary statistics for the specified period.
        
        Args:
            token_address: Token contract address
            days: Number of days to analyze
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            price_history = self.get_price_history(token_address, days)
            holder_history = self.get_holder_history(token_address, days)
            exchange_history = self.get_exchange_history(token_address, days)
            
            if not price_history:
                return {'error': 'No historical data available'}
            
            # Calculate price statistics
            prices = [p['price_usd'] for p in price_history if p['price_usd']]
            if prices:
                price_stats = {
                    'current_price': prices[-1],
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'avg_price': sum(prices) / len(prices),
                    'price_change_24h': ((prices[-1] - prices[-2]) / prices[-2] * 100) if len(prices) > 1 else 0,
                    'volatility': self._calculate_volatility(prices)
                }
            else:
                price_stats = {}
            
            # Calculate holder statistics
            holders = [h['total_holders'] for h in holder_history if h['total_holders']]
            holder_stats = {
                'current_holders': holders[-1] if holders else 0,
                'min_holders': min(holders) if holders else 0,
                'max_holders': max(holders) if holders else 0,
                'avg_holders': sum(holders) / len(holders) if holders else 0,
                'holder_growth': ((holders[-1] - holders[0]) / holders[0] * 100) if len(holders) > 1 and holders[0] > 0 else 0
            }
            
            return {
                'period_days': days,
                'data_points': len(price_history),
                'price_statistics': price_stats,
                'holder_statistics': holder_stats,
                'exchange_activity': {
                    name: len(data) for name, data in exchange_history.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting summary statistics: {e}")
            return {'error': str(e)}
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility (standard deviation of returns)."""
        if len(prices) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        if not returns:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return variance ** 0.5

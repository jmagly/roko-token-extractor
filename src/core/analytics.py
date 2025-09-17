"""
Advanced analytics module for token holder analysis and exchange interactions.
"""

import logging
from typing import Dict, Any, List, Set, Optional, Tuple
from collections import defaultdict, Counter
from web3 import Web3
import time


class TokenAnalytics:
    """Advanced analytics for token holders and exchange interactions."""
    
    def __init__(self, rpc_client, token_address: str):
        """
        Initialize the analytics module.
        
        Args:
            rpc_client: Ethereum RPC client instance
            token_address: Token contract address
        """
        self.rpc_client = rpc_client
        self.token_address = token_address
        self.logger = logging.getLogger(__name__)
        
        # Known exchange contract addresses
        self.exchange_contracts = {
            'uniswap_v2_router': '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
            'uniswap_v3_router': '0xE592427A0AEce92De3Edee1F18E0157C05861564',
            'sushiswap_router': '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
            '1inch_router': '0x1111111254EEB25477B68fb85Ed929f73A960582',
            'paraswap_router': '0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57',
            'zerox_router': '0xDef1C0ded9bec7F1a1670819833240f027b25EfF',
        }
        
        # DEX factory addresses for pool detection
        self.dex_factories = {
            'uniswap_v2': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f',
            'uniswap_v3': '0x1F98431c8aD98523631AE4a59f267346ea31F984',
            'sushiswap': '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
        }
    
    def get_token_holders_from_events(self, from_block: int = None, to_block: int = 'latest', 
                                    max_holders: int = 1000) -> Dict[str, Any]:
        """
        Extract token holders from Transfer events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number
            max_holders: Maximum number of holders to return
            
        Returns:
            Dictionary with holder information
        """
        try:
            if from_block is None:
                # Get events from last 10000 blocks (approximately 1.5 days)
                latest_block = self.rpc_client.get_latest_block()
                from_block = max(0, latest_block['number'] - 10000)
            
            self.logger.info(f"Scanning Transfer events from block {from_block} to {to_block}")
            
            # Transfer event signature: Transfer(address indexed from, address indexed to, uint256 value)
            transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            
            # Get Transfer events
            logs = self.rpc_client.get_logs(
                from_block=from_block,
                to_block=to_block,
                address=self.token_address,
                topics=[transfer_topic]
            )
            
            # Process events to build holder balances
            holder_balances = defaultdict(int)
            total_transfers = 0
            
            for log in logs:
                if len(log['topics']) >= 3:
                    from_addr = "0x" + log['topics'][1][-40:]  # Extract from address
                    to_addr = "0x" + log['topics'][2][-40:]    # Extract to address
                    
                    # Decode the value from the data field
                    value_hex = log['data'][2:]  # Remove '0x' prefix
                    value = int(value_hex, 16) if value_hex else 0
                    
                    # Update balances
                    if from_addr != "0x0000000000000000000000000000000000000000":  # Not a mint
                        holder_balances[from_addr] -= value
                    if to_addr != "0x0000000000000000000000000000000000000000":  # Not a burn
                        holder_balances[to_addr] += value
                    
                    total_transfers += 1
            
            # Filter out zero balances and sort by balance
            active_holders = {
                addr: balance for addr, balance in holder_balances.items() 
                if balance > 0
            }
            
            # Sort by balance (descending)
            sorted_holders = sorted(active_holders.items(), key=lambda x: x[1], reverse=True)
            
            # Get top holders
            top_holders = sorted_holders[:max_holders]
            
            # Calculate statistics
            total_holders = len(active_holders)
            total_supply = sum(active_holders.values())
            
            # Calculate concentration metrics
            top_10_balance = sum(balance for _, balance in top_holders[:10])
            top_100_balance = sum(balance for _, balance in top_holders[:100])
            
            concentration_10 = (top_10_balance / total_supply * 100) if total_supply > 0 else 0
            concentration_100 = (top_100_balance / total_supply * 100) if total_supply > 0 else 0
            
            return {
                'total_holders': total_holders,
                'total_transfers_analyzed': total_transfers,
                'total_supply_analyzed': total_supply,
                'top_holders': [
                    {
                        'address': addr,
                        'balance': balance,
                        'balance_formatted': balance / (10**18),  # Assuming 18 decimals
                        'percentage': (balance / total_supply * 100) if total_supply > 0 else 0
                    }
                    for addr, balance in top_holders
                ],
                'concentration_metrics': {
                    'top_10_percentage': concentration_10,
                    'top_100_percentage': concentration_100,
                    'gini_coefficient': self._calculate_gini_coefficient([balance for _, balance in active_holders.values()])
                },
                'scan_range': {
                    'from_block': from_block,
                    'to_block': to_block
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting token holders: {e}")
            return {}
    
    def get_exchange_interactions(self, from_block: int = None, to_block: int = 'latest') -> Dict[str, Any]:
        """
        Analyze interactions with exchange contracts.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number
            
        Returns:
            Dictionary with exchange interaction data
        """
        try:
            if from_block is None:
                latest_block = self.rpc_client.get_latest_block()
                from_block = max(0, latest_block['number'] - 10000)
            
            self.logger.info(f"Analyzing exchange interactions from block {from_block} to {to_block}")
            
            # Transfer event signature
            transfer_topic = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
            
            # Get Transfer events
            logs = self.rpc_client.get_logs(
                from_block=from_block,
                to_block=to_block,
                address=self.token_address,
                topics=[transfer_topic]
            )
            
            # Analyze interactions
            exchange_interactions = defaultdict(list)
            user_interactions = defaultdict(lambda: {
                'exchanges_used': set(),
                'total_volume': 0,
                'transaction_count': 0
            })
            
            for log in logs:
                if len(log['topics']) >= 3:
                    from_addr = "0x" + log['topics'][1][-40:]
                    to_addr = "0x" + log['topics'][2][-40:]
                    
                    # Decode value
                    value_hex = log['data'][2:]
                    value = int(value_hex, 16) if value_hex else 0
                    
                    # Check if interaction involves exchange contracts
                    for exchange_name, exchange_addr in self.exchange_contracts.items():
                        if from_addr.lower() == exchange_addr.lower() or to_addr.lower() == exchange_addr.lower():
                            exchange_interactions[exchange_name].append({
                                'block_number': log['block_number'],
                                'transaction_hash': log['transaction_hash'],
                                'from': from_addr,
                                'to': to_addr,
                                'value': value,
                                'value_formatted': value / (10**18)
                            })
                            
                            # Track user interactions
                            user_addr = to_addr if from_addr.lower() == exchange_addr.lower() else from_addr
                            user_interactions[user_addr]['exchanges_used'].add(exchange_name)
                            user_interactions[user_addr]['total_volume'] += value
                            user_interactions[user_addr]['transaction_count'] += 1
            
            # Calculate statistics
            total_exchange_transactions = sum(len(interactions) for interactions in exchange_interactions.values())
            unique_users = len(user_interactions)
            
            # Get top users by volume
            top_users = sorted(
                user_interactions.items(),
                key=lambda x: x[1]['total_volume'],
                reverse=True
            )[:50]
            
            return {
                'total_exchange_transactions': total_exchange_transactions,
                'unique_users_interacting': unique_users,
                'exchange_breakdown': {
                    name: {
                        'transaction_count': len(interactions),
                        'total_volume': sum(tx['value'] for tx in interactions),
                        'total_volume_formatted': sum(tx['value_formatted'] for tx in interactions),
                        'unique_users': len(set(tx['from'] if tx['from'].lower() != exchange_addr.lower() else tx['to'] 
                                               for tx in interactions))
                    }
                    for name, exchange_addr in self.exchange_contracts.items()
                    for interactions in [exchange_interactions[name]]
                },
                'top_users': [
                    {
                        'address': addr,
                        'exchanges_used': list(data['exchanges_used']),
                        'total_volume': data['total_volume'],
                        'total_volume_formatted': data['total_volume'] / (10**18),
                        'transaction_count': data['transaction_count']
                    }
                    for addr, data in top_users
                ],
                'scan_range': {
                    'from_block': from_block,
                    'to_block': to_block
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing exchange interactions: {e}")
            return {}
    
    def get_liquidity_providers(self, from_block: int = None, to_block: int = 'latest') -> Dict[str, Any]:
        """
        Identify liquidity providers by analyzing pool interactions.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number
            
        Returns:
            Dictionary with liquidity provider data
        """
        try:
            if from_block is None:
                latest_block = self.rpc_client.get_latest_block()
                from_block = max(0, latest_block['number'] - 10000)
            
            # This would require more complex analysis of pool contracts
            # For now, return a placeholder structure
            return {
                'message': 'Liquidity provider analysis requires pool contract integration',
                'scan_range': {
                    'from_block': from_block,
                    'to_block': to_block
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing liquidity providers: {e}")
            return {}
    
    def get_comprehensive_analytics(self, from_block: int = None, to_block: int = 'latest') -> Dict[str, Any]:
        """
        Get comprehensive analytics combining all analysis methods.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number
            
        Returns:
            Dictionary with comprehensive analytics
        """
        try:
            self.logger.info("Starting comprehensive analytics analysis")
            
            # Get all analytics data
            holders_data = self.get_token_holders_from_events(from_block, to_block)
            exchange_data = self.get_exchange_interactions(from_block, to_block)
            liquidity_data = self.get_liquidity_providers(from_block, to_block)
            
            return {
                'timestamp': int(time.time()),
                'analysis_range': {
                    'from_block': from_block,
                    'to_block': to_block
                },
                'token_holders': holders_data,
                'exchange_interactions': exchange_data,
                'liquidity_providers': liquidity_data,
                'summary': {
                    'total_holders': holders_data.get('total_holders', 0),
                    'total_exchange_transactions': exchange_data.get('total_exchange_transactions', 0),
                    'unique_users_interacting': exchange_data.get('unique_users_interacting', 0)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive analytics: {e}")
            return {}
    
    def _calculate_gini_coefficient(self, values: List[int]) -> float:
        """Calculate Gini coefficient for wealth distribution analysis."""
        if not values:
            return 0.0
        
        values = sorted(values)
        n = len(values)
        cumsum = [0] + list(accumulate(values))
        
        return (n + 1 - 2 * sum((n + 1 - i) * y for i, y in enumerate(cumsum[1:], 1))) / (n * sum(values))


def accumulate(iterable):
    """Accumulate function for Gini coefficient calculation."""
    it = iter(iterable)
    total = next(it)
    yield total
    for element in it:
        total += element
        yield total

"""
RPC Rate Limit List - Manages temporarily rate-limited RPC endpoints.
"""

import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional


class RPCRateLimitList:
    """Manages a list of RPC endpoints that are temporarily rate limited."""
    
    def __init__(self, rate_limit_file: str = "data/rpc_rate_limit_list.json", cooldown_minutes: int = 5):
        """
        Initialize the RPC rate limit list.
        
        Args:
            rate_limit_file: Path to the JSON file storing rate-limited endpoints.
            cooldown_minutes: How long to keep an endpoint in rate limit list (in minutes).
        """
        self.rate_limit_file = Path(rate_limit_file)
        self.rate_limit_file.parent.mkdir(parents=True, exist_ok=True)
        self.cooldown_seconds = cooldown_minutes * 60
        self.logger = logging.getLogger(__name__)
        self._rate_limited_endpoints: Dict[str, Dict[str, Any]] = self._load_rate_limit_list()
        self.logger.info(f"Loaded {len(self._rate_limited_endpoints)} rate-limited RPC endpoints")
    
    def _load_rate_limit_list(self) -> Dict[str, Dict[str, Any]]:
        """Load the rate limit list from a JSON file."""
        if not self.rate_limit_file.exists():
            self.logger.info("No rate limit list found, starting fresh")
            return {}
        
        try:
            with open(self.rate_limit_file, 'r') as f:
                data = json.load(f)
                # Filter out expired entries
                current_time = time.time()
                active_rate_limited = {
                    url: info for url, info in data.get('rate_limited_endpoints', {}).items()
                    if (current_time - info.get('timestamp', 0)) < self.cooldown_seconds
                }
                return active_rate_limited
        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            self.logger.error(f"Error loading rate limit list: {e}")
            return {}
    
    def _save_rate_limit_list(self) -> None:
        """Save the current rate limit list to a JSON file."""
        try:
            data = {
                'rate_limited_endpoints': self._rate_limited_endpoints,
                'last_updated': datetime.now().isoformat(),
                'total_rate_limited': len(self._rate_limited_endpoints),
                'cooldown_minutes': self.cooldown_seconds / 60
            }
            with open(self.rate_limit_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving rate limit list: {e}")
    
    def add_rate_limited_endpoint(self, url: str, error_code: Optional[int] = None, error_message: Optional[str] = None) -> None:
        """Add a rate-limited RPC endpoint to the rate limit list."""
        self.logger.warning(f"Added rate-limited RPC endpoint to cooldown list: {url}")
        if error_code:
            self.logger.warning(f"  Error code: {error_code}")
        if error_message:
            self.logger.warning(f"  Error message: {error_message}")
        
        self._rate_limited_endpoints[url] = {
            'timestamp': time.time(),
            'rate_limited_at': datetime.now().isoformat(),
            'error_code': error_code,
            'error_message': error_message,
            'cooldown_until': time.time() + self.cooldown_seconds
        }
        self._save_rate_limit_list()
    
    def is_rate_limited(self, url: str) -> bool:
        """Check if an RPC endpoint is currently rate limited."""
        if url in self._rate_limited_endpoints:
            # Check if the cooldown period has passed
            rate_limited_time = self._rate_limited_endpoints[url].get('timestamp', 0)
            if (time.time() - rate_limited_time) < self.cooldown_seconds:
                return True
            else:
                # Remove expired entry
                del self._rate_limited_endpoints[url]
                self._save_rate_limit_list()
        return False
    
    def clear_rate_limit_list(self) -> None:
        """Clear all entries from the rate limit list."""
        self._rate_limited_endpoints = {}
        self._save_rate_limit_list()
        self.logger.info("Cleared RPC rate limit list")
    
    def get_rate_limit_list_info(self) -> Dict[str, Any]:
        """Get information about the current rate limit list."""
        self._load_rate_limit_list()  # Ensure expired entries are removed
        return {
            'total_rate_limited': len(self._rate_limited_endpoints),
            'last_updated': datetime.now().isoformat(),
            'cooldown_minutes': self.cooldown_seconds / 60,
            'rate_limited_endpoints': list(self._rate_limited_endpoints.keys())
        }
    
    def get_cooldown_remaining(self, url: str) -> Optional[int]:
        """Get remaining cooldown time in seconds for a rate-limited endpoint."""
        if url in self._rate_limited_endpoints:
            rate_limited_time = self._rate_limited_endpoints[url].get('timestamp', 0)
            remaining = self.cooldown_seconds - (time.time() - rate_limited_time)
            return max(0, int(remaining))
        return None


def main():
    """Test the RPC rate limit list manager."""
    logging.basicConfig(level=logging.INFO)
    rate_limit_manager = RPCRateLimitList(cooldown_minutes=1)  # Short cooldown for testing
    
    print("RPC Rate Limit List Manager Test")
    print("========================================")
    
    # Test adding rate-limited endpoints
    rate_limit_manager.add_rate_limited_endpoint("https://rate-limited-rpc.com", 429, "Too Many Requests")
    rate_limit_manager.add_rate_limited_endpoint("https://another-rate-limited.com", 429, "Rate limit exceeded")
    
    # Test checking rate-limited endpoints
    print(f"Is https://rate-limited-rpc.com rate limited? {rate_limit_manager.is_rate_limited('https://rate-limited-rpc.com')}")
    print(f"Is https://not-rate-limited.com rate limited? {rate_limit_manager.is_rate_limited('https://not-rate-limited.com')}")
    
    # Test rate limit list info
    print("\nRate limit list info:", rate_limit_manager.get_rate_limit_list_info())
    
    # Test cooldown remaining
    cooldown = rate_limit_manager.get_cooldown_remaining("https://rate-limited-rpc.com")
    print(f"\nCooldown remaining for rate-limited-rpc.com: {cooldown} seconds")
    
    # Test clearing rate limit list
    print(f"\nRate limited count before clear: {rate_limit_manager.get_rate_limit_list_info()['total_rate_limited']}")
    rate_limit_manager.clear_rate_limit_list()
    print(f"Rate limited count after clear: {rate_limit_manager.get_rate_limit_list_info()['total_rate_limited']}")


if __name__ == "__main__":
    main()

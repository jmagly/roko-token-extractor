#!/usr/bin/env python3
"""
RPC Ignore List Manager
Manages a list of failing RPC endpoints to avoid repeatedly hitting broken services
"""

import json
import time
import logging
from pathlib import Path
from typing import Set, Dict, Any, Optional
from datetime import datetime, timedelta

class RPCIgnoreList:
    """Manages RPC endpoints that should be temporarily ignored due to failures."""
    
    def __init__(self, ignore_file: str = "data/rpc_ignore_list.json"):
        """Initialize the RPC ignore list manager."""
        self.ignore_file = Path(ignore_file)
        self.ignore_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.ignore_duration = 24 * 60 * 60  # 24 hours in seconds
        self._ignored_endpoints: Set[str] = set()
        self._load_ignore_list()
    
    def _load_ignore_list(self) -> None:
        """Load the ignore list from file."""
        try:
            if self.ignore_file.exists():
                with open(self.ignore_file, 'r') as f:
                    data = json.load(f)
                
                # Filter out expired entries
                current_time = time.time()
                valid_entries = []
                
                for entry in data.get('ignored_endpoints', []):
                    if current_time - entry.get('timestamp', 0) < self.ignore_duration:
                        valid_entries.append(entry)
                        self._ignored_endpoints.add(entry['url'])
                
                # Update file with only valid entries
                if len(valid_entries) != len(data.get('ignored_endpoints', [])):
                    self._save_ignore_list()
                
                self.logger.info(f"Loaded {len(self._ignored_endpoints)} ignored RPC endpoints")
            else:
                self.logger.info("No ignore list found, starting fresh")
                
        except Exception as e:
            self.logger.error(f"Error loading ignore list: {e}")
            self._ignored_endpoints = set()
    
    def _save_ignore_list(self) -> None:
        """Save the ignore list to file."""
        try:
            # Convert set to list of entries with timestamps
            entries = []
            for url in self._ignored_endpoints:
                entries.append({
                    'url': url,
                    'timestamp': time.time(),
                    'ignored_at': datetime.now().isoformat()
                })
            
            data = {
                'ignored_endpoints': entries,
                'last_updated': datetime.now().isoformat(),
                'total_ignored': len(entries)
            }
            
            with open(self.ignore_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.debug(f"Saved {len(entries)} ignored RPC endpoints to {self.ignore_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving ignore list: {e}")
    
    def add_failing_endpoint(self, url: str, error_code: Optional[int] = None, error_message: Optional[str] = None) -> None:
        """
        Add a failing RPC endpoint to the ignore list.
        
        Args:
            url: The RPC endpoint URL that failed
            error_code: HTTP error code (if applicable)
            error_message: Error message for logging
        """
        # Don't ignore 404 errors (endpoint not found) as they might be temporary
        if error_code == 404:
            self.logger.debug(f"Not ignoring 404 error for {url} (temporary issue)")
            return
        
        if url not in self._ignored_endpoints:
            self._ignored_endpoints.add(url)
            self._save_ignore_list()
            
            self.logger.warning(f"Added failing RPC endpoint to ignore list: {url}")
            if error_code:
                self.logger.warning(f"  Error code: {error_code}")
            if error_message:
                self.logger.warning(f"  Error message: {error_message}")
        else:
            self.logger.debug(f"RPC endpoint already in ignore list: {url}")
    
    def is_ignored(self, url: str) -> bool:
        """
        Check if an RPC endpoint is in the ignore list.
        
        Args:
            url: The RPC endpoint URL to check
            
        Returns:
            True if the endpoint should be ignored, False otherwise
        """
        return url in self._ignored_endpoints
    
    def clear_ignore_list(self) -> None:
        """Clear the entire ignore list (called when refreshing from ChainList)."""
        self._ignored_endpoints.clear()
        
        # Remove the ignore file
        if self.ignore_file.exists():
            self.ignore_file.unlink()
        
        self.logger.info("Cleared RPC ignore list (fresh data from ChainList)")
    
    def get_ignored_count(self) -> int:
        """Get the number of currently ignored endpoints."""
        return len(self._ignored_endpoints)
    
    def get_ignored_endpoints(self) -> Set[str]:
        """Get the set of ignored endpoint URLs."""
        return self._ignored_endpoints.copy()
    
    def get_ignore_list_info(self) -> Dict[str, Any]:
        """Get information about the current ignore list."""
        try:
            if self.ignore_file.exists():
                with open(self.ignore_file, 'r') as f:
                    data = json.load(f)
                
                return {
                    'total_ignored': len(self._ignored_endpoints),
                    'last_updated': data.get('last_updated', 'unknown'),
                    'ignore_duration_hours': self.ignore_duration / 3600,
                    'ignored_endpoints': list(self._ignored_endpoints)
                }
            else:
                return {
                    'total_ignored': 0,
                    'last_updated': 'never',
                    'ignore_duration_hours': self.ignore_duration / 3600,
                    'ignored_endpoints': []
                }
        except Exception as e:
            return {
                'total_ignored': 0,
                'last_updated': 'error',
                'ignore_duration_hours': self.ignore_duration / 3600,
                'ignored_endpoints': [],
                'error': str(e)
            }
    
    def remove_endpoint(self, url: str) -> bool:
        """
        Remove a specific endpoint from the ignore list.
        
        Args:
            url: The RPC endpoint URL to remove
            
        Returns:
            True if the endpoint was removed, False if it wasn't in the list
        """
        if url in self._ignored_endpoints:
            self._ignored_endpoints.remove(url)
            self._save_ignore_list()
            self.logger.info(f"Removed RPC endpoint from ignore list: {url}")
            return True
        return False

def main():
    """Test the RPC ignore list manager."""
    logging.basicConfig(level=logging.INFO)
    
    ignore_list = RPCIgnoreList()
    
    print("RPC Ignore List Manager Test")
    print("=" * 40)
    
    # Test adding failing endpoints
    ignore_list.add_failing_endpoint("https://broken-rpc.com", 500, "Internal Server Error")
    ignore_list.add_failing_endpoint("https://rate-limited.com", 429, "Too Many Requests")
    ignore_list.add_failing_endpoint("https://payment-required.com", 402, "Payment Required")
    
    # Test 404 (should not be ignored)
    ignore_list.add_failing_endpoint("https://not-found.com", 404, "Not Found")
    
    # Check if endpoints are ignored
    print(f"Is https://broken-rpc.com ignored? {ignore_list.is_ignored('https://broken-rpc.com')}")
    print(f"Is https://not-found.com ignored? {ignore_list.is_ignored('https://not-found.com')}")
    print(f"Is https://working-rpc.com ignored? {ignore_list.is_ignored('https://working-rpc.com')}")
    
    # Get info
    info = ignore_list.get_ignore_list_info()
    print(f"\nIgnore list info: {info}")
    
    # Test clearing
    print(f"\nIgnored count before clear: {ignore_list.get_ignored_count()}")
    ignore_list.clear_ignore_list()
    print(f"Ignored count after clear: {ignore_list.get_ignored_count()}")

if __name__ == "__main__":
    main()

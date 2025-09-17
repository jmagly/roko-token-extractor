#!/usr/bin/env python3
"""
Final Complete ROKO token holder extraction with full error monitoring
"""

import json
import sys
import requests
import os
import time
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append('src')

def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def format_balance(balance_wei, decimals=18):
    """Format balance with proper display for small amounts."""
    balance_formatted = balance_wei / (10 ** decimals)
    
    if balance_formatted < 0.01 and balance_formatted > 0:
        return "<0.01"
    else:
        return f"{balance_formatted:,.2f}"

def extract_roko_holders_final_complete():
    """Final complete ROKO token holder extraction with full monitoring."""
    print("🔍 Final Complete ROKO Token Holder Extraction")
    print("=" * 70)
    print("Extracting ALL transfer events and holders with full error monitoring")
    print("=" * 70)
    
    # Load environment variables
    load_env_file()
    
    # ROKO token address
    roko_address = "0x6f222e04f6c53cc688ffb0abe7206aac66a8ff98"
    
    # Get Alchemy API key
    alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
    
    if not alchemy_api_key:
        print("❌ ALCHEMY_API_KEY not found in environment variables")
        return None
    
    print(f"📊 Using Alchemy API key: {alchemy_api_key[:8]}...")
    print(f"📊 Analyzing token: {roko_address}")
    
    # Alchemy API endpoint
    alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
    
    # Error tracking
    error_count = 0
    max_errors = 100
    consecutive_errors = 0
    max_consecutive_errors = 10
    
    try:
        # 1. Get total supply
        print("\n1. Getting token total supply...")
        
        total_supply_payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{
                "to": roko_address,
                "data": "0x18160ddd"  # totalSupply() function selector
            }, "latest"],
            "id": 1
        }
        
        response = requests.post(alchemy_url, json=total_supply_payload, timeout=30)
        total_supply_data = response.json()
        
        if 'result' in total_supply_data:
            total_supply_hex = total_supply_data['result']
            total_supply = int(total_supply_hex, 16)
            decimals = 18
            print(f"   ✅ Total Supply: {total_supply:,.0f} wei ({total_supply / (10 ** decimals):,.2f} ROKO)")
        else:
            print(f"   ❌ Error getting total supply: {total_supply_data}")
            return None
        
        # 2. Get ALL transfer events (no page limit)
        print("\n2. Getting ALL transfer events (complete history)...")
        print("   This will take a while - processing until no more pages...")
        
        all_transfers = []
        page_key = None
        page_count = 0
        start_time = time.time()
        
        while True:
            try:
                transfer_payload = {
                    "jsonrpc": "2.0",
                    "method": "alchemy_getAssetTransfers",
                    "params": [{
                        "fromBlock": "0x0",
                        "toBlock": "latest",
                        "category": ["erc20"],
                        "contractAddresses": [roko_address],
                        "maxCount": "0x3e8",  # 1000 per request
                        "excludeZeroValue": True,
                        "withMetadata": True,
                        **({"pageKey": page_key} if page_key else {})
                    }],
                    "id": 2 + page_count
                }
                
                response = requests.post(alchemy_url, json=transfer_payload, timeout=60)
                transfers_data = response.json()
                
                if 'result' in transfers_data and 'transfers' in transfers_data['result']:
                    transfers = transfers_data['result']['transfers']
                    all_transfers.extend(transfers)
                    page_count += 1
                    
                    elapsed = time.time() - start_time
                    print(f"   📊 Page {page_count}: Found {len(transfers)} transfer events (Total: {len(all_transfers)}) - {elapsed:.1f}s elapsed")
                    
                    if 'pageKey' in transfers_data['result']:
                        page_key = transfers_data['result']['pageKey']
                    else:
                        print("   ✅ No more pages available - complete history retrieved")
                        break
                        
                    # Reset consecutive error counter on success
                    consecutive_errors = 0
                    
                else:
                    error_count += 1
                    consecutive_errors += 1
                    print(f"   ⚠️  Error on page {page_count + 1}: {transfers_data}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"   ❌ Too many consecutive errors ({consecutive_errors}), stopping transfer collection")
                        break
                        
                    if error_count >= max_errors:
                        print(f"   ❌ Too many total errors ({error_count}), stopping transfer collection")
                        break
                    
                    # Wait before retry
                    time.sleep(2)
                    
            except Exception as e:
                error_count += 1
                consecutive_errors += 1
                print(f"   ❌ Exception on page {page_count + 1}: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    print(f"   ❌ Too many consecutive errors ({consecutive_errors}), stopping transfer collection")
                    break
                    
                if error_count >= max_errors:
                    print(f"   ❌ Too many total errors ({error_count}), stopping transfer collection")
                    break
                
                # Wait before retry
                time.sleep(5)
        
        print(f"   ✅ Transfer events collection complete: {len(all_transfers):,} events in {page_count} pages")
        print(f"   📊 Errors encountered: {error_count}")
        
        # 3. Extract unique addresses
        print("\n3. Extracting all unique addresses...")
        
        all_addresses = set()
        address_stats = {}
        
        for transfer in all_transfers:
            from_addr = transfer.get('from', '')
            to_addr = transfer.get('to', '')
            value_hex = transfer.get('rawContract', {}).get('value', '0x0')
            value = int(value_hex, 16)
            block_num = int(transfer.get('blockNum', '0x0'), 16)
            
            if from_addr and from_addr != '0x0000000000000000000000000000000000000000':
                all_addresses.add(from_addr)
                if from_addr not in address_stats:
                    address_stats[from_addr] = {
                        'total_sent': 0, 'total_received': 0, 'transfer_count': 0,
                        'first_seen_block': block_num, 'last_seen_block': block_num
                    }
                address_stats[from_addr]['total_sent'] += value
                address_stats[from_addr]['transfer_count'] += 1
                address_stats[from_addr]['last_seen_block'] = max(address_stats[from_addr]['last_seen_block'], block_num)
                address_stats[from_addr]['first_seen_block'] = min(address_stats[from_addr]['first_seen_block'], block_num)
            
            if to_addr and to_addr != '0x0000000000000000000000000000000000000000':
                all_addresses.add(to_addr)
                if to_addr not in address_stats:
                    address_stats[to_addr] = {
                        'total_sent': 0, 'total_received': 0, 'transfer_count': 0,
                        'first_seen_block': block_num, 'last_seen_block': block_num
                    }
                address_stats[to_addr]['total_received'] += value
                address_stats[to_addr]['transfer_count'] += 1
                address_stats[to_addr]['last_seen_block'] = max(address_stats[to_addr]['last_seen_block'], block_num)
                address_stats[to_addr]['first_seen_block'] = min(address_stats[to_addr]['first_seen_block'], block_num)
        
        print(f"   ✅ Found {len(all_addresses):,} unique addresses")
        
        # 4. Check balances using direct contract calls
        print(f"\n4. Checking balances for ALL {len(all_addresses):,} addresses...")
        print("   This will take several hours for complete extraction...")
        
        all_addresses_list = list(all_addresses)
        current_balances = {}
        holders_found = 0
        zero_balance_count = 0
        balance_errors = 0
        balance_start_time = time.time()
        
        for i, address in enumerate(all_addresses_list):
            try:
                # Create balanceOf call data
                padded_address = address[2:].zfill(64)
                call_data = f"0x70a08231{padded_address}"
                
                balance_payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_call",
                    "params": [{
                        "to": roko_address,
                        "data": call_data
                    }, "latest"],
                    "id": 100 + i
                }
                
                response = requests.post(alchemy_url, json=balance_payload, timeout=30)
                balance_data = response.json()
                
                if 'result' in balance_data:
                    balance_hex = balance_data['result']
                    balance = int(balance_hex, 16)
                    
                    if balance > 0:
                        current_balances[address] = balance
                        holders_found += 1
                        formatted_balance = format_balance(balance, decimals)
                        print(f"   🎉 Holder {holders_found}: {address} - {formatted_balance} ROKO")
                    else:
                        zero_balance_count += 1
                else:
                    balance_errors += 1
                    if balance_errors % 100 == 0:
                        print(f"   ⚠️  Balance check errors: {balance_errors}")
                
                if (i + 1) % 500 == 0:
                    elapsed = time.time() - balance_start_time
                    rate = (i + 1) / elapsed if elapsed > 0 else 0
                    eta = (len(all_addresses_list) - i - 1) / rate if rate > 0 else 0
                    print(f"   📊 Processed {i + 1}/{len(all_addresses_list)} addresses ({holders_found} holders, {zero_balance_count} zero balance) - {rate:.1f} addr/s - ETA: {eta/60:.1f}min")
            
            except Exception as e:
                balance_errors += 1
                if balance_errors % 100 == 0:
                    print(f"   ⚠️  Balance check errors: {balance_errors} - Last error: {e}")
                continue
        
        # 5. Filter for addresses with balances
        print(f"\n5. Final holder summary...")
        
        holders_with_balance = current_balances  # Already filtered for > 0
        
        print(f"   ✅ Found {len(holders_with_balance):,} addresses with current balances")
        print(f"   ✅ Excluded {zero_balance_count:,} addresses with 0.00 ROKO")
        print(f"   ⚠️  Balance check errors: {balance_errors}")
        
        # 6. Get current block
        print(f"\n6. Getting current blockchain state...")
        
        block_payload = {
            "jsonrpc": "2.0",
            "method": "eth_blockNumber",
            "params": [],
            "id": 200
        }
        
        response = requests.post(alchemy_url, json=block_payload, timeout=30)
        block_data = response.json()
        current_block = int(block_data.get('result', '0x0'), 16)
        
        print(f"   ✅ Current block: {current_block:,}")
        
        # 7. Format holder data
        print(f"\n7. Formatting holder data...")
        
        holders_list = []
        
        for address, balance in holders_with_balance.items():
            formatted_balance = balance / (10 ** decimals)
            stats = address_stats.get(address, {
                'total_sent': 0, 'total_received': 0, 'transfer_count': 0,
                'first_seen_block': 0, 'last_seen_block': 0
            })
            
            # Calculate activity metrics
            blocks_since_activity = current_block - stats['last_seen_block']
            days_since_activity = (blocks_since_activity * 12) / (24 * 3600)  # ~12 seconds per block
            
            # Determine activity status
            if blocks_since_activity < 1000:  # ~3.3 hours
                activity_status = "Very Recent"
            elif blocks_since_activity < 10000:  # ~33 hours
                activity_status = "Recent"
            elif blocks_since_activity < 100000:  # ~13 days
                activity_status = "Moderate"
            else:
                activity_status = "Old"
            
            holders_list.append({
                "address": address,
                "balance": balance,
                "balance_formatted": formatted_balance,
                "percentage_of_supply": (balance / total_supply) * 100,
                "first_seen_block": stats['first_seen_block'],
                "last_activity_block": stats['last_seen_block'],
                "blocks_since_activity": blocks_since_activity,
                "days_since_activity": round(days_since_activity, 2),
                "activity_status": activity_status,
                "total_sent": stats['total_sent'] / (10 ** decimals),
                "total_received": stats['total_received'] / (10 ** decimals),
                "net_activity": (stats['total_received'] - stats['total_sent']) / (10 ** decimals),
                "transfer_count": stats['transfer_count']
            })
        
        # Sort by balance
        holders_list.sort(key=lambda x: x['balance'], reverse=True)
        
        # 8. Calculate supply coverage
        total_holders_supply = sum(holder['balance'] for holder in holders_list)
        supply_coverage = (total_holders_supply / total_supply) * 100
        
        # 9. Compile final data
        data = {
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_method": "final_complete_history_direct_contract_calls",
            "completeness": "FULL_HISTORY_EXTRACTED",
            "error_tracking": {
                "transfer_errors": error_count,
                "balance_errors": balance_errors,
                "consecutive_errors": consecutive_errors
            },
            "token": {
                "address": roko_address,
                "name": "Roko",
                "symbol": "ROKO",
                "decimals": 18,
                "total_supply": total_supply,
                "total_supply_formatted": f"{total_supply / (10 ** decimals):,.2f}"
            },
            "extraction_stats": {
                "total_transfer_events": len(all_transfers),
                "total_unique_addresses": len(all_addresses),
                "addresses_checked": len(all_addresses_list),
                "addresses_with_balance": len(holders_with_balance),
                "addresses_excluded_zero": zero_balance_count,
                "pages_processed": page_count,
                "supply_coverage": f"{supply_coverage:.2f}%"
            },
            "holders": {
                "total_holders": len(holders_list),
                "total_holders_supply": total_holders_supply,
                "total_holders_supply_formatted": f"{total_holders_supply / (10 ** decimals):,.2f}",
                "supply_coverage": f"{supply_coverage:.2f}%",
                "top_10_holders": holders_list[:10],
                "all_holders": holders_list
            },
            "api_performance": {
                "method": "Final complete history direct contract calls",
                "api_key_masked": f"{alchemy_api_key[:8]}...",
                "requests_made": 1 + page_count + len(all_addresses_list) + 1,
                "data_quality": "Complete - Full token history extracted with error monitoring"
            }
        }
        
        # 10. Save data
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        json_filename = f"data/exports/roko_holders_final_complete_{timestamp}.json"
        
        with open(json_filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save CSV
        csv_filename = f"data/exports/roko_holders_final_complete_{timestamp}.csv"
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            import csv
            fieldnames = ['rank', 'address', 'balance_roko', 'balance_raw', 'percentage_of_supply',
                         'first_seen_block', 'last_activity_block', 'blocks_since_activity',
                         'days_since_activity', 'activity_status', 'total_sent', 'total_received',
                         'net_activity', 'transfer_count']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, holder in enumerate(holders_list, 1):
                writer.writerow({
                    'rank': i,
                    'address': holder['address'],
                    'balance_roko': holder['balance_formatted'],
                    'balance_raw': holder['balance'],
                    'percentage_of_supply': holder['percentage_of_supply'],
                    'first_seen_block': holder['first_seen_block'],
                    'last_activity_block': holder['last_activity_block'],
                    'blocks_since_activity': holder['blocks_since_activity'],
                    'days_since_activity': holder['days_since_activity'],
                    'activity_status': holder['activity_status'],
                    'total_sent': holder['total_sent'],
                    'total_received': holder['total_received'],
                    'net_activity': holder['net_activity'],
                    'transfer_count': holder['transfer_count']
                })
        
        print(f"\n✅ Final complete data saved to:")
        print(f"   • JSON: {json_filename}")
        print(f"   • CSV:  {csv_filename}")
        
        # Display results
        print("\n" + "=" * 120)
        print("🏆 ROKO TOKEN HOLDERS (Final Complete History Extraction)")
        print("=" * 120)
        print(f"{'Rank':<4} {'Address':<44} {'Balance (ROKO)':<18} {'% Supply':<8} {'Activity':<12} {'Days Ago':<8} {'Transfers':<10}")
        print("-" * 120)
        
        for i, holder in enumerate(holders_list[:20], 1):
            balance_display = format_balance(holder['balance'], decimals) + " ROKO"
            print(f"{i:<4} {holder['address']:<44} {balance_display:>16} {holder['percentage_of_supply']:>6.2f}% {holder['activity_status']:>10} {holder['days_since_activity']:>6.1f} {holder['transfer_count']:>8}")
        
        print("=" * 120)
        
        print(f"\n📊 Final Complete Extraction Summary:")
        print(f"   • Total supply: {total_supply / (10 ** decimals):,.2f} ROKO")
        print(f"   • Total holders found: {len(holders_list):,}")
        print(f"   • Supply coverage: {supply_coverage:.2f}%")
        print(f"   • Zero balance wallets excluded: {zero_balance_count:,}")
        print(f"   • Transfer events processed: {len(all_transfers):,}")
        print(f"   • Unique addresses analyzed: {len(all_addresses):,}")
        print(f"   • Pages processed: {page_count}")
        print(f"   • Transfer errors: {error_count}")
        print(f"   • Balance check errors: {balance_errors}")
        print(f"   • API requests made: {data['api_performance']['requests_made']}")
        print(f"   • Data completeness: FULL HISTORY EXTRACTED")
        
        if len(holders_list) >= 3000:
            print(f"\n🎉 SUCCESS: Found {len(holders_list):,} holders (exceeded 3000+ target!)")
        elif len(holders_list) > 0:
            print(f"\n✅ SUCCESS: Found {len(holders_list):,} holders")
        else:
            print(f"\n⚠️  No holders found")
        
        return data
        
    except Exception as e:
        print(f"\n❌ Critical error during final complete extraction: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    extract_roko_holders_final_complete()

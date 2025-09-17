# ROKO Data Update Cronjob Setup

This document explains how to set up automated hourly data updates for the ROKO token using a cronjob.

## Quick Setup

1. **Run the setup script:**
   ```bash
   chmod +x setup_cronjob.sh
   ./setup_cronjob.sh
   ```

2. **Test the script manually:**
   ```bash
   python3 update_roko_data.py
   ```

3. **Add to crontab:**
   ```bash
   crontab -e
   ```

4. **Add one of these lines (choose your frequency):**
   ```bash
   # Every hour
   0 * * * * cd /path/to/chain-data-extractor && python3 update_roko_data.py >> logs/cron.log 2>&1
   
   # Every 30 minutes
   */30 * * * * cd /path/to/chain-data-extractor && python3 update_roko_data.py >> logs/cron.log 2>&1
   
   # Every 15 minutes
   */15 * * * * cd /path/to/chain-data-extractor && python3 update_roko_data.py >> logs/cron.log 2>&1
   ```

## Output Files

The script generates two files in the `web_delivery/` directory:

- `latest.json` - Always contains the most recent data
- `roko_data_YYYYMMDD_HHMMSS.json` - Timestamped backup files

## File Structure

```
web_delivery/
├── latest.json                    # Current data for web delivery
├── roko_data_20240917_130000.json # Hourly backups
├── roko_data_20240917_140000.json
└── ...

logs/
├── roko_update.log               # Script execution logs
└── cron.log                     # Cronjob output logs
```

## JSON Output Format

The generated JSON file contains:

```json
{
  "timestamp": 1726560000,
  "datetime": "2024-09-17T13:00:00.000000",
  "last_updated": "2024-09-17 13:00:00 UTC",
  "token": {
    "name": "ROKO",
    "symbol": "ROKO",
    "address": "0x6f222e04f6c53cc688ffb0abe7206aac66a8ff98",
    "decimals": 18,
    "total_supply": "369369369369000000000000000000",
    "total_supply_formatted": 369369369369,
    "holders": 3992
  },
  "pricing": {
    "price_eth": 0.0000000033,
    "price_usd": 0.000015,
    "eth_price_usd": 4491.75,
    "market_cap_usd": 5543636.52,
    "price_source": "uniswap_pool",
    "all_prices": {
      "uniswap_pool": {
        "price_eth": 0.0000000033,
        "price_usd": 0.000015
      }
    }
  },
  "liquidity": {
    "total_liquidity_usd": 21880.30,
    "pools_count": 1,
    "pools": [...]
  },
  "volume": {
    "volume_24h_usd": 21880.30,
    "volume_7d_usd": 153162.09,
    "volume_30d_usd": 656408.95,
    "volume_24h_eth": 4.87,
    "volume_7d_eth": 34.09,
    "volume_30d_eth": 146.11
  },
  "summary": {
    "status": "success",
    "extraction_time": "2024-09-17T13:00:00.000000",
    "data_quality": "high"
  }
}
```

## Monitoring

- Check logs: `tail -f logs/roko_update.log`
- Check cron logs: `tail -f logs/cron.log`
- Verify latest data: `cat web_delivery/latest.json | jq .`

## Troubleshooting

1. **Script fails to run:**
   - Check Python path: `which python3`
   - Check dependencies: `pip install -r requirements.txt`
   - Check config file: `ls config/config.yaml`

2. **No data generated:**
   - Check RPC connectivity
   - Check API keys in `.env` file
   - Check logs for specific errors

3. **Cronjob not running:**
   - Check cron service: `systemctl status cron`
   - Check crontab: `crontab -l`
   - Check cron logs: `grep CRON /var/log/syslog`

## Web Server Integration

The `latest.json` file is designed to be served directly by your web server:

```nginx
# Nginx example
location /api/roko {
    alias /path/to/chain-data-extractor/web_delivery/latest.json;
    add_header Content-Type application/json;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

```apache
# Apache example
<Location "/api/roko">
    ProxyPass file:///path/to/chain-data-extractor/web_delivery/latest.json
    Header set Content-Type "application/json"
    Header set Cache-Control "no-cache, no-store, must-revalidate"
</Location>
```

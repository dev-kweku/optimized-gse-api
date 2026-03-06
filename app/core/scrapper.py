import cloudscraper
import re
import logging
import json
import time
from datetime import datetime
from .models import TradeSchema, StockHistory
from .redis_cache import RedisCache
from app.utils.helpers import clean_currency_string, format_db_id, is_market_open

logger = logging.getLogger("GSE_SCRAPER")

class GSEEngine:
    def __init__(self, db_session):
        # Using a higher-level browser fingerprint
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        
        # Standard browser headers
        self.browser_header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://gse.com.gh",
            "Referer": "https://gse.com.gh/trading-and-data/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        self.session.headers.update(self.browser_header)
        
        self.db = db_session
        self.cache = RedisCache()
        self.base_url = "https://gse.com.gh/trading-and-data/"
        self.ajax_url = "https://gse.com.gh/wp-admin/admin-ajax.php"

    def get_nonce(self):
        """Step 1: Extract the nonce with a behavioral delay."""
        try:
            logger.info("Performing session handshake...")
            r = self.session.get(self.base_url, timeout=30)
            r.raise_for_status()
            
            # Pattern matching for wpDataTables security nonce
            patterns = [
                r'"wdtNonce"\s*:\s*"([a-f0-9]+)"',
                r'wdtNonce["\']\s*:\s*["\']([a-f0-9]+)["\']',
                r'nonce["\']\s*:\s*["\']([a-f0-9]+)["\']'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, r.text)
                if match:
                    nonce = match.group(1)
                    logger.info(f"Dynamic Nonce Found: {nonce}")
                    return nonce

            logger.error("Nonce not found in HTML source.")
            return None

        except Exception as e:
            logger.error(f"Handshake failed: {e}")
            return None

    def sync(self):
        """Step 2: Scrape Table 39 with behavioral simulation."""
        nonce = self.get_nonce()
        if not nonce:
            return

        # VITAL: Wait 5 seconds to mimic a human 'reading' the page before the table loads
        # This is the most common reason Cloudflare blocks the subsequent POST
        logger.info("Simulating human dwell time (5s)...")
        time.sleep(5)

        payload = {
            "action": "get_wdtable",
            "table_id": "39",
            "draw": "1",
            "start": "0",
            "length": "100", 
            "wdtNonce": nonce,
            "order[0][column]": "0",
            "order[0][dir]": "desc"
        }

        try:
            logger.info(f"Requesting data sync for Table 39...")
            response = self.session.post(
                self.ajax_url, 
                data=payload, 
                timeout=30
            )

            # Check for generic failure or HTML (Cloudflare Challenge)
            raw_text = response.text.strip()
            if not raw_text or raw_text == "0" or raw_text.startswith("<!"):
                logger.error("Verification failed: Server returned non-JSON response.")
                with open("error_response.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
                return

            json_data = response.json()
            data = json_data.get('data', [])
            
            if not data:
                logger.warning("Successful connection, but Table 39 returned 0 rows.")
                return

            synced_count = 0
            for row in data:
                # Basic column validation (Index 2 is Symbol, Index 1 is Date)
                if len(row) < 13 or not is_market_open(row[2]):
                    continue
                
                try:
                    # Clean and validate row data
                    valid = TradeSchema(**{str(i): val for i, val in enumerate(row)})
                    dt = datetime.strptime(valid.daily_date, '%d/%m/%Y').date()
                    
                    # 1. Update PostgreSQL Persistence
                    record = StockHistory(
                        id=format_db_id(valid.symbol, dt),
                        symbol=valid.symbol.strip().upper(),
                        trade_date=dt,
                        close_price=clean_currency_string(valid.close_price),
                        volume=clean_currency_string(valid.volume)
                    )
                    self.db.merge(record)

                    # 2. Update Redis Cache
                    self.cache.set_latest_price(valid.symbol, {
                        "price": clean_currency_string(valid.close_price),
                        "volume": clean_currency_string(valid.volume),
                        "date": valid.daily_date,
                    })
                    synced_count += 1
                except Exception:
                    continue

            self.db.commit()
            logger.info(f"Pipeline Success: {synced_count} records synchronized.")

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            # Final fallback: log what we got
            if 'response' in locals():
                with open("error_response.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
            self.db.rollback()
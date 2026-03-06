import requests
import re
import logging
from datetime import datetime
from .models import TradeSchema, StockHistory
from .redis_cache import RedisCache
from app.utils.helpers import clean_currency_string, format_db_id, is_market_open

logger = logging.getLogger("GSE_SCRAPER")

class GSEEngine:
    def __init__(self, db_session):
        self.session = requests.Session()
        self.db = db_session
        self.cache = RedisCache()  # Performance Layer: Redis
        self.base_url = "https://gse.com.gh/trading-and-data/"
        self.ajax_url = "https://gse.com.gh/wp-admin/admin-ajax.php"
        
        # Set standard headers to mimic a browser
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        })

    def get_nonce(self):
        """Step 1: The Handshake - Extract Security Token from the page source."""
        try:
            logger.info("Initiating handshake to fetch security nonce...")
            r = self.session.get(self.base_url, timeout=15)
            r.raise_for_status()
            
            # Find the wdtNonce in the script tags
            match = re.search(r'"wdtNonce":"([a-f0-9]+)"', r.text)
            if match:
                nonce = match.group(1)
                logger.info(f"Handshake successful. Nonce: {nonce}")
                return nonce
            
            logger.error("Handshake failed: Nonce not found in page source.")
            return None
        except Exception as e:
            logger.error(f"Handshake error: {e}")
            return None

    def sync(self):
        """Step 2: Scrape from AJAX API, Filter, and Dual-Write (SQL + Redis)."""
        nonce = self.get_nonce()
        if not nonce:
            return

        payload = {
            "action": "get_wdtable", 
            "table_id": "47", 
            "length": "100",  # Fetch up to 100 stocks in one request
            "wdtNonce": nonce
        }
        
        try:
            logger.info("Fetching data from GSE Internal API...")
            response = self.session.post(self.ajax_url, data=payload, timeout=20)
            response.raise_for_status()
            
            json_res = response.json()
            data = json_res.get('data', [])
            
            if not data:
                logger.warning("No trading data returned from API.")
                return

            records_synced = 0
            for row in data:
                # 1. Market Open Filter (Logic from helpers.py)
                date_raw = row[0]
                if not is_market_open(date_raw):
                    continue
                
                # 2. Validation & Mapping (Logic from models.py)
                try:
                    raw_dict = {str(i): val for i, val in enumerate(row)}
                    valid = TradeSchema(**raw_dict)
                    dt = datetime.strptime(valid.date_str, '%d/%m/%Y').date()
                    
                    # 3. Persistent Storage (PostgreSQL)
                    record = StockHistory(
                        id=format_db_id(valid.symbol, dt),
                        symbol=valid.symbol.strip().upper(),
                        trade_date=dt,
                        close_price=clean_currency_string(valid.close_price),
                        volume=clean_currency_string(valid.volume)
                    )
                    self.db.merge(record) 
                    
                    # 4. Performance Layer (Redis Push)
                    # We cache the clean values for immediate API delivery
                    self.cache.set_latest_price(valid.symbol, {
                        "symbol": valid.symbol.strip().upper(),
                        "price": clean_currency_string(valid.close_price),
                        "volume": clean_currency_string(valid.volume),
                        "date": valid.date_str,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    records_synced += 1
                except Exception as row_err:
                    logger.error(f"Error processing ticker {row[1] if len(row)>1 else 'unknown'}: {row_err}")
            
            # Commit all changes to DB at once for performance
            self.db.commit()
            logger.info(f"Sync complete. {records_synced} records updated in SQL and Redis.")

        except requests.exceptions.RequestException as req_err:
            logger.error(f"API Request failed: {req_err}")
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            self.db.rollback()
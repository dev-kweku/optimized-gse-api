from datetime import datetime
from app.utils.helpers import clean_currency_string,format_db_id,is_market_open

import requests
import re
from .models import TradeSchema, StockHistory

class GSEEngine:
    def __init__(self, db_session):
        self.session = requests.Session()
        self.db = db_session
        self.base_url = "https://gse.com.gh/trading-and-data/"
        self.ajax_url = "https://gse.com.gh/wp-admin/admin-ajax.php"

    def get_nonce(self):
        """Step 1: The Handshake - Get Security Token."""
        r = self.session.get(self.base_url)
        match = re.search(r'"wdtNonce":"([a-f0-9]+)"', r.text)
        return match.group(1) if match else None

    def sync(self):
        """Step 2: Scrape & Store."""
        nonce = self.get_nonce()
        payload = {"action": "get_wdtable", "table_id": "47", "length": "100", "wdtNonce": nonce}
        
        data = self.session.post(self.ajax_url, data=payload).json().get('data', [])
        
        for row in data:
            date_raw=row[0]
            if not is_market_open(date_raw):
                continue
            
            valid = TradeSchema(**{str(i): val for i, val in enumerate(row)})
            dt = datetime.strptime(valid.date_str, '%d/%m/%Y').date()
            
            
            record = StockHistory(
                id=format_db_id(valid.symbol,dt),
                symbol=valid.symbol.strip(),
                trade_date=dt,
                close_price=clean_currency_string(valid.close_price),
                volume=clean_currency_string(valid.volumn)
            )
            self.db.merge(record) 
  
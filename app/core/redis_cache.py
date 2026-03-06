import redis
import json
import os
import logging

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class RedisCache:
    def __init__(self):
        self.client = redis.from_url(REDIS_URL, decode_responses=True)
        self.logger = logging.getLogger("REDIS_CACHE")

    def set_latest_price(self, symbol: str, data: dict):
        """
        Stores the latest stock data. 
        We use a hash or a JSON string for instant retrieval.
        """
        try:
            # Key format: gse:latest:MTNGH
            key = f"gse:latest:{symbol.upper()}"
            self.client.set(key, json.dumps(data))
            
            # Also add to a 'all_tickers' set for easy dashboard listing
            self.client.sadd("gse:tickers", symbol.upper())
        except Exception as e:
            self.logger.error(f"Redis Set Error: {e}")

    def get_latest_price(self, symbol: str):
        """Used by the API to get data instantly."""
        data = self.client.get(f"gse:latest:{symbol.upper()}")
        return json.loads(data) if data else None
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL=os.getenv("DATABASE_URL")
BASE_URL="https://gse.com.gh/wp-admin/admin-ajax.php"

HEADERS={
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Origin": "https://gse.com.gh",
    "Referer": "https://gse.com.gh/trading-and-data/"

}
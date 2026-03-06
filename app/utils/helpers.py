import re
from datetime import datetime

def clean_currency_string(value: str) -> float:
    """
    Highly performant regex to strip HTML tags, currency symbols (GH¢), 
    and commas, returning a clean float.
    """
    if not value or value.strip() == "":
        return 0.0
    
    # Remove HTML tags if any (sometimes API returns <span>Value</span>)
    clean_html = re.sub(r'<[^>]*>', '', str(value))
    
    # Extract only numbers and the decimal point
    numeric_string = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", clean_html.replace(',', '')))
    
    try:
        return float(numeric_string)
    except ValueError:
        return 0.0

def calculate_percentage_change(current: float, previous: float) -> float:
    """Calculates price movement percentage."""
    if not previous or previous == 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 2)

def format_db_id(symbol: str, date_obj: datetime.date) -> str:
    """Generates a consistent primary key for PostgreSQL (e.g., MTNGH_20240520)."""
    clean_symbol = re.sub(r'[^A-Z0-9]', '', symbol.upper())
    return f"{clean_symbol}_{date_obj.strftime('%Y%m%d')}"

def is_market_open(date_str: str) -> bool:
    """
    Architecture Feature: Filter Scraped Data on Daily Available Opened Market.
    Checks if the date provided by the GSE API is valid for trading.
    """
    try:
        dt = datetime.strptime(date_str, '%d/%m/%Y')
        # Simple check: GSE usually doesn't trade on weekends (Saturday=5, Sunday=6)
        if dt.weekday() >= 5:
            return False
        return True
    except ValueError:
        return False
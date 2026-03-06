from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, String, Float, Date, DateTime
from sqlalchemy.orm import declarative_base
import re

Base = declarative_base()

class TradeSchema(BaseModel):
    """Pydantic Filter: Validates API data before it touches the DB."""
    # Note: We use the indices as aliases to match the GSE AJAX response
    date_str: str = Field(..., alias="0")
    symbol: str = Field(..., alias="1")
    close_price: str = Field("0", alias="6")
    volume: str = Field("0", alias="10")

    # In Pydantic V2, we list the actual field names defined in the model, 
    # not the aliases, inside the validator.
    @field_validator('close_price', 'volume', mode='before')
    @classmethod
    def clean_val(cls, v):
        if v is None:
            return "0"
        # Remove anything that isn't a digit or a decimal point
        cleaned = re.sub(r'[^\d.]', '', str(v))
        return cleaned if cleaned else "0"

class StockHistory(Base):
    """PostgreSQL Table: Stores historical data for YTR/YTD calcs."""
    __tablename__ = 'stock_history'
    id = Column(String, primary_key=True)
    symbol = Column(String, index=True)
    trade_date = Column(Date, index=True)
    close_price = Column(Float)
    volume = Column(Float)
    scraped_at = Column(DateTime, default=datetime.utcnow)
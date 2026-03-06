from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, String, Float, Date, DateTime
from sqlalchemy.orm import declarative_base
import re

Base = declarative_base()

class TradeSchema(BaseModel):
    # Mapping to the payload indices you provided
    daily_date: str = Field(..., alias="1")
    symbol: str = Field(..., alias="2")
    prev_close: str = Field("0", alias="5")
    open_price: str = Field("0", alias="6")
    last_price: str = Field("0", alias="7")
    close_price: str = Field("0", alias="8")
    volume: str = Field("0", alias="12")
    value: str = Field("0", alias="13")

    @field_validator('prev_close', 'open_price', 'last_price', 'close_price', 'volume', 'value', mode='before')
    @classmethod
    def clean_numeric(cls, v):
        if not v: return "0"
        # Strip everything except numbers and decimals
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
from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True)
    share_code = Column(String, unique=True, nullable=False)


class DailyPrice(Base):
    __tablename__ = "daily_prices"

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    trade_date = Column(Date, nullable=False)

    open = Column(Numeric)
    close = Column(Numeric)
    high = Column(Numeric)
    low = Column(Numeric)
    volume = Column(BigInteger)

    __table_args__ = (
        UniqueConstraint("stock_id", "trade_date"),
    )
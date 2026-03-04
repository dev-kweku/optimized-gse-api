from app.database import SessionLocal
from app.models import Stock,DailyPrice

def load_data(df):
    session=SessionLocal()

    for _,row in df.iterrows():
        stock=session.query(Stock).filter_by(
            share_code=row["Share Code"]
        ).first()

        if not stock:
            stock=Stock(share_code=row["Share Code"])
            session.add(stock)
            session.commit()

        price=DailyPrice(
            stock_id=stock.id,
            trade_date=row["Daily Date"],
            open=row.get("Opening Price (GH¢)"),
            close=row.get("Closing Price - VWAP (GH¢)"),
            high=row.get("Year High (GH¢)"),
            low=row.get("Year Low (GH¢)"),
            volume=row.get("Total Shares Traded")

        )

        session.merge(price)
    session.commit()
    session.close()
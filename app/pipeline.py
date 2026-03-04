from app.extractor import fetch_table
from app.transformer import transform
from app.loader import load_data
from app.database import engine,SessionLocal
from app.models import Base,DailyPrice
from sqlalchemy import func
import pandas as pd
from app.market_calendar import is_market_open

def get_latest_trade_date():
    session=SessionLocal()
    latest=session.query(func.max(DailyPrice.trade_date)).scaler()
    session.close()
    return latest


def run_backfill():
    print("Running full historical backfill...")
    Base.metadata.create_all(bind=engine)


    df=fetch_table(39)
    df=transform(df)
    load_data(df)

    print("Backfill completed ...")

# increamental data pipeline function

def run_increamental():

    print("Checking market status...")

    if not is_market_open():
        print("Skipping incremental run ...")
        return
    print("Running incremental ingestion ...")

    Base.metadata.create_all(bind=engine)

    latest_date=get_latest_trade_date()

    df=fetch_table(39)
    df=transform(df)

    if latest_date:
        df = df[df["Daily Date"] > pd.to_datetime(latest_date)]

        if df.empty:
            print("No new records found.")
            return

    load_data(df)

    print("Incremental ingestion completed.")
from app.extractor import fetch_table
from app.transformer import transform
from app.loader import load_data
from app.database import engine,SessionLocal
from app.models import Base,DailyPrice
from sqlalchemy import func
import pandas as pd

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
    print("Running incremental ingestion ...")

    Base.metadata.create_all(bind=engine)

    latest_date=get_latest_trade_date()

    df=fetch_table(39)
    df=transform(df)

    if latest_date:
        print(f"Latest trade in DB :{latest_date}")
        df=df[df["Daily Date"]>pd.to_datetime(latest_date)]

        if df.empty:
            print("No new record found..")
            return
        print(f"New records found: {len(df)}")

    else:
        print("No existing data found. Performing first time load")

    load_data(df)

    print("Incremental ingestion completed ..")

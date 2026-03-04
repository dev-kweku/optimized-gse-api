from app.extractor import fetch_table
from app.transformer import transform
from app.loader import load_data
from app.database import engine
from app.models import Base


def run_backfill():
    Base.metadata.create_all(bind=engine)


    df=fetch_table(39)
    df=transform(df)
    load_data(df)

# increamental data pipeline function

# def run_increamental():

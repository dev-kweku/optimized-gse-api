import requests
import pandas as pd
from app.config import BASE_URL,HEADERS

session=requests.Session()
session.headers.update(HEADERS)


# function for fetching table from the database
def fetch_table(table_id:int)->pd.DataFrame:
    params={
        "action":"get_wdtable",
        "table_id":table_id
    }

    response=session.post(BASE_URL,params=params,timeout=30)
    response.raise_for_status()

    df=pd.read_html(response.text)[0]
    return df
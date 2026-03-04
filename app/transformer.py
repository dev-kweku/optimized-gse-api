import pandas as pd

# function for data transforming to form an understandable value display
def transform(df:pd.DataFrame)->pd.DataFrame:
    df["Daily Date"]=pd.to_datetime(df["Daily Date"],dayfirst=True)

    numeric_cols=[
        "Opening Price (GH¢)",
        "Closing Price - VWAP (GH¢)",
        "Year High (GH¢)",
        "Year Low (GH¢)",
        "Total Shares Traded"

    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col]=(
                df[col].astype(str).str.replace(",","",regex=False)
                .str.replace("GH¢",regex=False).astype(float)
            )
            

    return df
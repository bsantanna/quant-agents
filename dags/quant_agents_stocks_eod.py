from airflow import DAG
from airflow.decorators import task
from datetime import datetime

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "retries": 0,
}

dag = DAG(
    "quant_agents_stocks_eod",
    default_args=default_args,
    schedule="@daily",
    catchup=False,
)

@task.kubernetes(
    image="bsantanna/compute-document-utils",
    namespace="compute",
)
def load_stocks_eod():
    import os
    import requests
    import json
    import pandas as pd
    from datetime import datetime

    def format_bulk_stocks_eod(ticker: str, df: pd.DataFrame, index_suffix: str) -> bytes:
        index_name = f"quant-agents_stocks-eod_{index_suffix}"
        lines = []

        for _, row in df.iterrows():

            date_reference = row.get('timestamp')
            open_ = row.get('open')
            close = row.get('close')
            high = row.get('high')
            low = row.get('low')
            volume = row.get('volume')

            if open_ is None or close is None:
                continue
            id_str = f"{ticker}_{str(date_reference)}"

            meta = {"index": {"_index": index_name, "_id": id_str}}

            doc = {
                "key_ticker": ticker,
                "date_reference": date_reference,
                "val_open": float(open_),
                "val_close": float(close) if close is not None else None,
                "val_high": float(high) if high is not None else None,
                "val_low": float(low) if low is not None else None,
                "val_volume": int(volume) if volume is not None else None,
            }

            lines.append(json.dumps(meta))
            lines.append(json.dumps(doc))

        return (("\n".join(lines)) + "\n").encode("utf-8")

    def ingest_stocks_eod(ticker: str, index_suffix="latest") -> requests.Response:
        es_url = os.environ.get('ELASTICSEARCH_URL')
        es_api_key = os.environ.get('ELASTICSEARCH_API_KEY')
        alpha_vantage_api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
        alpha_vantage_time_series_url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={alpha_vantage_api_key}&datatype=csv"

        ticker_daily_time_series = pd.read_csv(alpha_vantage_time_series_url)

        return requests.post(
            url=f"{es_url}/_bulk",
            headers={
                'Authorization': f'ApiKey {es_api_key}',
                'Content-Type': 'application/x-ndjson'
            },
            data=format_bulk_stocks_eod(ticker, ticker_daily_time_series, index_suffix)
        )

    symbols = [
        "AAPL", "ASML",
        "GOOG",
        "META", "MSFT",
        "NVDA",
    ]

    for symbol in symbols:
        stocks_eod_response = ingest_stocks_eod(symbol)
        print(f"Ingestion complete stocks EOD for {symbol}: {stocks_eod_response.json()}")


with dag:
    load_stocks_eod


from airflow.sdk import DAG, task
from airflow.providers.cncf.kubernetes.secret import Secret
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
    image="bsantanna/java-python-dev",
    namespace="quant-agents",
    secrets=[Secret('env', None, 'quant-agents-secrets')],
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

            date_reference = row.get('t').split('T')[0]
            open_ = row.get('o')
            close = row.get('c')
            high = row.get('h')
            low = row.get('l')
            volume = row.get('v')

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

        now = datetime.now()
        end = now.replace(day=now.day - 1)
        start = now.replace(year=now.year - 1)
        alpaca_time_series_url = f"https://data.alpaca.markets/v2/stocks/{ticker}/bars?timeframe=1D&start={start.strftime('%Y-%m-%d')}&end={end.strftime('%Y-%m-%d')}&adjustment=all"
        response = requests.get(alpaca_time_series_url, headers={
            "accept": "application/json",
            "APCA-API-KEY-ID": os.environ.get('APCA-API-KEY-ID'),
            "APCA-API-SECRET-KEY": os.environ.get('APCA-API-SECRET-KEY')
        })
        ticker_daily_time_series = pd.json_normalize(response.json().get('bars'))

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
    load_stocks_eod()

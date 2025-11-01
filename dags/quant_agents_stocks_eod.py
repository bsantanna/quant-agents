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

stocks = [
    "AAPL", "ASML",
    "GOOG",
    "META", "MSFT",
    "NVDA",
]

# @task.kubernetes(
#     image="bsantanna/compute-document-utils",
#     namespace="compute",
# )
# def load_stocks_eod():

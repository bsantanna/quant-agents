from typing_extensions import Optional
from elasticsearch import Elasticsearch

class MarketsStatsService:

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    async def get_stats_close(self, index_name: str, key_ticker: str, close_date:Optional[str]) -> dict:

        search_params = {
            "id": "get_stats_close_template",
            "params": {
                "key_ticker": key_ticker,
                "close_date": close_date,
            }
        }

        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['recent_stats']['value']

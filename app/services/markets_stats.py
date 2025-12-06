from typing_extensions import Optional
from elasticsearch import Elasticsearch


class MarketsStatsService:

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    async def get_stats_close(self, index_name: str, key_ticker: str, close_date: Optional[str]) -> dict:
        search_params = {
            "id": "get_stats_close_template",
            "params": {
                "key_ticker": key_ticker,
                "close_date": close_date,
            }
        }

        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['recent_stats']['value']

    async def get_indicator_ad(self, index_name: str, key_ticker: str, start_date: str, end_date: str) -> dict:
        search_params = {
            "id": "get_eod_indicator_ad_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['ad_stats']['value']

    async def get_indicator_adx(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            period: int
    ) -> dict:
        search_params = {
            "id": "get_eod_indicator_adx_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "period": period,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['adx_stats']['value']

    async def get_indicator_cci(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            period: int,
            constant: float
    ) -> dict:
        search_params = {
            "id": "get_eod_indicator_cci_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "period": period,
                "constant": constant,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['cci_stats']['value']

    async def get_indicator_ema(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            short_window: int,
            long_window: int
    ) -> dict:
        search_params = {
            "id": "get_eod_indicator_ema_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "short_window": short_window,
                "long_window": long_window,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['ema_stats']['value']

    async def get_indicator_macd(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            short_window: int,
            long_window: int,
            signal_window: int
    ) -> dict:
        search_params = {
            "id": "get_eod_indicator_macd_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "short_window": short_window,
                "long_window": long_window,
                "signal_window": signal_window,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['macd_stats']['value']

    async def get_indicator_obv(self, index_name: str, key_ticker: str, start_date: str, end_date: str) -> dict:
        search_params = {
            "id": "get_eod_indicator_obv_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['obv_stats']['value']

    async def get_indicator_rsi(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            period: int
    ) -> dict:
        search_params = {
            "id": "get_eod_indicator_rsi_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "period": period,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['rsi_stats']['value']

    async def get_indicator_stoch(
            self,
            index_name: str,
            key_ticker: str,
            start_date: str,
            end_date: str,
            lookback: int,
            smooth_k: int,
            smooth_d: int
    ) -> dict:
        search_params = {
            "id": "get_eod_indicator_stoch_template",
            "params": {
                "key_ticker": key_ticker,
                "date_gte": start_date,
                "date_lte": end_date,
                "lookback": lookback,
                "smooth_k": smooth_k,
                "smooth_d": smooth_d,
            }
        }
        response = self.es.search_template(index=index_name, body=search_params)
        return response['aggregations']['stoch_stats']['value']

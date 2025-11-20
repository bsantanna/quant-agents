from elasticsearch import Elasticsearch


class MarketsStatsService:

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    async def get_stats_close(self, index_name: str, key_ticker: str) -> dict:
        query = {
            "size": 0,
            "query": {
                "term": {
                    "key_ticker": {
                        "value": key_ticker
                    }
                }
            },
            "aggs": {
                "close_info": {
                    "scripted_metric": {
                        "init_script": "state.closes = new ArrayList();",
                        "map_script": """
                            if (doc.containsKey('val_close') && doc['val_close'].size() > 0 &&
                                doc.containsKey('date_reference') && doc['date_reference'].size() > 0) {
                                state.closes.add([
                                    'date': doc['date_reference'].value.millis,
                                    'close': doc['val_close'].value
                                ]);
                            }
                        """,
                        "combine_script": "return state.closes;",
                        "reduce_script": """
                            def all = [];
                            for (s in states) { if (s != null) all.addAll(s); }
                            if (all.isEmpty()) return null;

                            all.sort((a,b) -> Long.compare(b.date, a.date));  // descending by date

                            if (all.size() < 2) return null;

                            def latest = all[0].close;
                            def prev   = all[1].close;
                            def variance = prev == 0 ? 0 : ((latest - prev) / prev) * 100;

                            def formatter = DateTimeFormatter.ofPattern('yyyy-MM-dd').withZone(ZoneId.of('UTC'));
                            def date_str = formatter.format(Instant.ofEpochMilli(all[0].date));

                            return [
                                'most_recent_close': latest,
                                'most_recent_date' : date_str,
                                'percent_variance' : Math.round(variance * 100.0) / 100.0   // round to 2 decimals
                            ];
                        """
                    }
                }
            }
        }

        response = self.es.search(index=index_name, body=query)
        return response['aggregations']['close_info']['value']

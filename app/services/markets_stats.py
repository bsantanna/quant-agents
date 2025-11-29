from typing_extensions import Optional
from elasticsearch import Elasticsearch

class MarketsStatsService:

    def __init__(self, es: Elasticsearch) -> None:
        self.es = es

    async def get_stats_close(self, index_name: str, key_ticker: str, close_date:Optional[str]) -> dict:

        if close_date is not None:
            filter_query = {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "key_ticker": {
                                    "value": key_ticker
                                }
                            }
                        },
                        {
                            "range": {
                                "date_reference": {
                                    "lte": close_date
                                }
                            }
                        }
                    ]
                }
            }
        else:
            filter_query = {
                "term": {
                    "key_ticker": {
                        "value": key_ticker
                    }
                }
            }

        search_query = {
            "size": 0,
            "query": filter_query,
            "aggs": {
                "recent_stats": {
                    "scripted_metric": {
                        "init_script": "state.entries = new ArrayList();",
                        "map_script": """
                                if (doc.containsKey('val_close') && doc['val_close'].size() > 0 && doc['val_close'].value != null &&
                                    doc.containsKey('date_reference') && doc['date_reference'].size() > 0) {
                                    def entry = [
                                        'date': doc['date_reference'].value.millis,
                                        'close': doc['val_close'].value
                                    ];
                                    if (doc.containsKey('val_open') && doc['val_open'].size() > 0) {
                                        entry['open'] = doc['val_open'].value;
                                    }
                                    if (doc.containsKey('val_high') && doc['val_high'].size() > 0) {
                                        entry['high'] = doc['val_high'].value;
                                    }
                                    if (doc.containsKey('val_low') && doc['val_low'].size() > 0) {
                                        entry['low'] = doc['val_low'].value;
                                    }
                                    if (doc.containsKey('val_volume') && doc['val_volume'].size() > 0) {
                                        entry['volume'] = doc['val_volume'].value;
                                    }
                                    state.entries.add(entry);
                                }
                            """,
                        "combine_script": "return state.entries;",
                        "reduce_script": """
                                def all = [];
                                for (s in states) { if (s != null) all.addAll(s); }
                                if (all.isEmpty()) return null;

                                all.sort((a,b) -> Long.compare(b.date, a.date));  // descending by date

                                if (all.size() < 2) return null;

                                def latest = all[0];
                                def prev   = all[1].close;
                                def variance = prev == 0 ? 0 : ((latest.close - prev) / prev) * 100;

                                def formatter = DateTimeFormatter.ofPattern('yyyy-MM-dd').withZone(ZoneId.of('UTC'));
                                def date_str = formatter.format(Instant.ofEpochMilli(latest.date));

                                return [
                                    'most_recent_open': latest.containsKey('open') ? latest.open : null,
                                    'most_recent_high': latest.containsKey('high') ? latest.high : null,
                                    'most_recent_low': latest.containsKey('low') ? latest.low : null,
                                    'most_recent_close': latest.close,
                                    'most_recent_volume': latest.containsKey('volume') ? latest.volume : null,
                                    'most_recent_date' : date_str,
                                    'percent_variance' : Math.round(variance * 100.0) / 100.0   // round to 2 decimals
                                ];
                            """
                    }
                }
            }
        }

        response = self.es.search(index=index_name, body=search_query)
        return response['aggregations']['recent_stats']['value']

from dependency_injector.wiring import inject, Provide
from elasticsearch import Elasticsearch
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.interface.api.markets.schema import StatsMostRecentClose

router = APIRouter()


@router.get(
    path="/stats_close/{index}/{key_ticker}",
    response_model=StatsMostRecentClose,
    operation_id="stats_close",
    summary="Get most recent close stats for a given ticker"
)
@inject
async def get_most_recent_close(
        index_name: str,
        key_ticker: str,
        es: Elasticsearch = Depends(Provide[Container.es])
):
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

    response = es.search(index=index_name, body=query)
    bucket = response['aggregations']['close_info']['value']
    result = StatsMostRecentClose(
        key_ticker=key_ticker,
        most_recent_close=bucket.get('most_recent_close'),
        most_recent_date=bucket.get('most_recent_date'),
        percent_variance=bucket.get('percent_variance'),
    )

    return result

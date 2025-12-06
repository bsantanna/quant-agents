from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends

from app.core.container import Container
from app.interface.api.cache_control import cache_control
from app.interface.api.markets.schema import StatsClose, StatsCloseRequest
from app.services.markets_stats import MarketsStatsService

router = APIRouter()


@router.get(
    path="/stats_close/{index_name}/{key_ticker}",
    response_model=StatsClose,
    operation_id="stats_close",
    summary="Get most recent close stats for a given ticker"
)
@inject
async def get_most_recent_close(
        index_name: str,
        key_ticker: str,
        markets_stats_service: MarketsStatsService = Depends(Provide[Container.markets_stats_service]),
        request: StatsCloseRequest = Depends(),
        _ = cache_control(3600)

):
    result = await markets_stats_service.get_stats_close(index_name, key_ticker, request.close_date)
    response = StatsClose(
        key_ticker=key_ticker,
        most_recent_close=result.get('most_recent_close'),
        most_recent_open=result.get('most_recent_open'),
        most_recent_high=result.get('most_recent_high'),
        most_recent_low=result.get('most_recent_low'),
        most_recent_volume=result.get('most_recent_volume'),
        most_recent_date=result.get('most_recent_date'),
        percent_variance=result.get('percent_variance'),
    )

    return response


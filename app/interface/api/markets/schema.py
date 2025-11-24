from pydantic import BaseModel


class StatsClose(BaseModel):
    key_ticker: str
    most_recent_close: float
    most_recent_open: float
    most_recent_high: float
    most_recent_low: float
    most_recent_volume: float
    most_recent_date: str
    percent_variance: float


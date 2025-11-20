from pydantic import BaseModel


class StatsMostRecentClose(BaseModel):
    key_ticker: str
    most_recent_close: float
    most_recent_date: str
    percent_variance: float


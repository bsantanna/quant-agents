from datetime import datetime, date
from typing_extensions import Optional

from pydantic import BaseModel, field_validator

from app.domain.exceptions.base import InvalidFieldError


class StatsClose(BaseModel):
    key_ticker: str
    most_recent_close: float
    most_recent_open: float
    most_recent_high: float
    most_recent_low: float
    most_recent_volume: float
    most_recent_date: str
    percent_variance: float


class StatsCloseRequest(BaseModel):
    close_date: Optional[str] = None

    @field_validator('close_date')
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v

        try:
            # Validate the date format
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise InvalidFieldError('close_date', 'Date must be in yyyy-mm-dd format')


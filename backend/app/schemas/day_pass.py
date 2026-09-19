from datetime import date

from pydantic import BaseModel, Field


class DayPassConfig(BaseModel):
    day: date
    cap: float = Field(gt=0)
    enabled: bool = False

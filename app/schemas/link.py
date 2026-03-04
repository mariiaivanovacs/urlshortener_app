from datetime import datetime

from pydantic import BaseModel, HttpUrl



# Pydantic models for request and response validation
class ShortenRequest(BaseModel):
    url: HttpUrl

    # model_config = {
    #     "json_schema_extra": {"example": {"url": "https://www.example.com/very/long/path"}}
    # }


class ShortenResponse(BaseModel):
    short_id: str
    short_url: str
    original_url: str


class StatsResponse(BaseModel):
    short_id: str
    original_url: str
    clicks: int
    created_at: datetime

    model_config = {"from_attributes": True}

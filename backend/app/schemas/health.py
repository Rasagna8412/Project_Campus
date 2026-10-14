"""Health check schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Core application health response schema."""

    status: str = Field(..., description="Application operational status")
    version: str = Field(..., description="Application software version")
    database: Optional[str] = Field(
        None, description="Database connectivity status (if checked)"
    )

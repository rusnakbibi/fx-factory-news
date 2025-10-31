# app/core/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

@dataclass
class FFEvent:
    date: datetime  # UTC
    title: str
    country: str
    currency: str
    impact: str  # High/Medium/Low/Holiday
    forecast: Optional[str]
    previous: Optional[str]
    actual: Optional[str]
    url: Optional[str]
    raw: Dict[str, Any]

@dataclass
class MMEvent:
    dt_utc: datetime
    time_str: str          # "HH:MM" у 24h
    title: str
    country: str | None = None  # Country code (e.g., "US", "UK", "EZ")
    impact: str | None = None
    actual: str | None = None
    forecast: str | None = None
    previous: str | None = None
    date_label: str = "" 
    source: str = "MetalsMine (offline)"

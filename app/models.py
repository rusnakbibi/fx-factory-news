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

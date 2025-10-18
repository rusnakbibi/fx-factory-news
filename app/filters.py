from typing import Iterable, List
from .models import FFEvent

def filter_events(events: List[FFEvent], impacts: Iterable[str], countries: Iterable[str]) -> List[FFEvent]:
    imp_norm = {i.strip().capitalize() for i in impacts if i and i.strip()}
    cset = {c.strip().upper() for c in countries if c and c.strip()}
    res = []
    for ev in events:
        if imp_norm and ev.impact.capitalize() not in imp_norm:
            continue
        if cset and (ev.currency.upper() not in cset and ev.country.upper() not in cset):
            continue
        res.append(ev)
    return res

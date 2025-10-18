from typing import Any, List

def str_or_none(v: Any):
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None

def csv_to_list(s: str) -> List[str]:
    return [x.strip() for x in (s or "").split(',') if x.strip()]

def chunk(seq: List[Any], n: int) -> List[List[Any]]:
    return [seq[i:i+n] for i in range(0, len(seq), n)]

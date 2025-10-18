# app/db.py
from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Tuple

# --- PG / SQLite autodetect ---
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
USE_PG = bool(DATABASE_URL)

if USE_PG:
    import psycopg  # psycopg v3 (sync)
    PG_CONN_KW = {"autocommit": True}

# ---------- common helpers ----------

def _row_to_dict_pg(row: Tuple, desc) -> Dict[str, Any]:
    """Convert psycopg row tuple + description to dict."""
    cols = [c[0] for c in desc]
    return {cols[i]: row[i] for i in range(len(cols))}

def _row_to_dict_sqlite(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row)

def _dict(row) -> Dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    # sqlite Row?
    try:
        return dict(row)
    except Exception:
        return row

# ---------- schema (both backends) ----------

DDL_SUBS = """
CREATE TABLE IF NOT EXISTS subscriptions (
  user_id        BIGINT NOT NULL,
  chat_id        BIGINT NOT NULL,
  impact_filter  TEXT   NOT NULL DEFAULT 'High,Medium',
  countries_filter TEXT NOT NULL DEFAULT '',
  alert_minutes  INTEGER NOT NULL DEFAULT 30,
  daily_time     TEXT   NOT NULL DEFAULT '09:00',
  lang_mode      TEXT   NOT NULL DEFAULT 'en',
  out_chat_id    BIGINT,
  PRIMARY KEY (user_id, chat_id)
);
"""

DDL_SENT = """
CREATE TABLE IF NOT EXISTS sent_log (
  chat_id     BIGINT NOT NULL,
  ev_hash     TEXT   NOT NULL,
  kind        TEXT   NOT NULL, -- 'alert' | 'digest' | etc
  created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (chat_id, ev_hash, kind)
);
"""

# optional small cache table (kept for API compatibility; not used now)
DDL_CACHE = """
CREATE TABLE IF NOT EXISTS events_cache (
  cache_key  TEXT PRIMARY KEY,
  payload    TEXT NOT NULL,
  expires_at TIMESTAMP NOT NULL
);
"""

def _init_sqlite(path: str = "bot.db"):
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(DDL_SUBS)
    cur.execute(DDL_SENT)
    cur.execute(DDL_CACHE)
    cur.close()
    return conn

def _init_pg(dsn: str):
    conn = psycopg.connect(dsn, **PG_CONN_KW)
    with conn.cursor() as cur:
        # PG flavor: TIMESTAMPTZ for created_at/order
        cur.execute(DDL_SUBS.replace("INTEGER", "INTEGER"))
        cur.execute(DDL_SENT.replace("TIMESTAMP", "TIMESTAMPTZ").replace("CURRENT_TIMESTAMP", "NOW()"))
        cur.execute(DDL_CACHE.replace("TIMESTAMP", "TIMESTAMPTZ"))
    return conn

# keep global single connection (simple & adequate for our light workload)
if USE_PG:
    _CONN = _init_pg(DATABASE_URL)
else:
    _CONN = _init_sqlite(os.getenv("DB_PATH", "bot.db"))

# ---------- public API ----------

def ensure_sub(user_id: int, chat_id: int):
    """
    Insert default subscription if not exists.
    """
    if USE_PG:
        with _CONN.cursor() as cur:
            cur.execute(
                """
                INSERT INTO subscriptions (user_id, chat_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, chat_id) DO NOTHING
                """,
                (user_id, chat_id),
            )
    else:
        _CONN.execute(
            """
            INSERT OR IGNORE INTO subscriptions (user_id, chat_id)
            VALUES (?, ?)
            """,
            (user_id, chat_id),
        )

def get_sub(user_id: int, chat_id: int) -> Dict[str, Any]:
    """
    Return subscription row as dict (or {}).
    """
    if USE_PG:
        with _CONN.cursor() as cur:
            cur.execute(
                "SELECT * FROM subscriptions WHERE user_id=%s AND chat_id=%s",
                (user_id, chat_id),
            )
            row = cur.fetchone()
            return _row_to_dict_pg(row, cur.description) if row else {}
    else:
        cur = _CONN.execute(
            "SELECT * FROM subscriptions WHERE user_id=? AND chat_id=?",
            (user_id, chat_id),
        )
        row = cur.fetchone()
        return _row_to_dict_sqlite(row) if row else {}

def set_sub(user_id: int, chat_id: int, **fields):
    """
    Update provided fields for subscription.
    """
    if not fields:
        return
    cols = sorted(fields.keys())

    if USE_PG:
        # build SET clause
        assigns = ", ".join(f"{c}=%s" for c in cols)
        params = [fields[c] for c in cols] + [user_id, chat_id]
        with _CONN.cursor() as cur:
            cur.execute(
                f"UPDATE subscriptions SET {assigns} WHERE user_id=%s AND chat_id=%s",
                params,
            )
    else:
        assigns = ", ".join(f"{c}=?" for c in cols)
        params = [fields[c] for c in cols] + [user_id, chat_id]
        _CONN.execute(
            f"UPDATE subscriptions SET {assigns} WHERE user_id=? AND chat_id=?",
            params,
        )

def unsubscribe(user_id: int, chat_id: int):
    if USE_PG:
        with _CONN.cursor() as cur:
            cur.execute(
                "DELETE FROM subscriptions WHERE user_id=%s AND chat_id=%s",
                (user_id, chat_id),
            )
    else:
        _CONN.execute(
            "DELETE FROM subscriptions WHERE user_id=? AND chat_id=?",
            (user_id, chat_id),
        )

def get_all_subs() -> List[Dict[str, Any]]:
    """
    Return all subscriptions as list of dicts.
    """
    if USE_PG:
        with _CONN.cursor() as cur:
            cur.execute("SELECT * FROM subscriptions")
            rows = cur.fetchall()
            if not rows:
                return []
            cols = [c[0] for c in cur.description]
            return [{cols[i]: r[i] for i in range(len(cols))} for r in rows]
    else:
        cur = _CONN.execute("SELECT * FROM subscriptions")
        return [_row_to_dict_sqlite(r) for r in cur.fetchall()]

# ---- sent_log (alerts & digests dedupe) ----

def mark_sent(chat_id: int, ev_hash: str, kind: str):
    if USE_PG:
        with _CONN.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sent_log (chat_id, ev_hash, kind)
                VALUES (%s, %s, %s)
                ON CONFLICT (chat_id, ev_hash, kind) DO NOTHING
                """,
                (chat_id, ev_hash, kind),
            )
    else:
        _CONN.execute(
            """
            INSERT OR IGNORE INTO sent_log (chat_id, ev_hash, kind)
            VALUES (?, ?, ?)
            """,
            (chat_id, ev_hash, kind),
        )

def was_sent(chat_id: int, ev_hash: str, kind: str) -> bool:
    if USE_PG:
        with _CONN.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM sent_log WHERE chat_id=%s AND ev_hash=%s AND kind=%s",
                (chat_id, ev_hash, kind),
            )
            return cur.fetchone() is not None
    else:
        cur = _CONN.execute(
            "SELECT 1 FROM sent_log WHERE chat_id=? AND ev_hash=? AND kind=?",
            (chat_id, ev_hash, kind),
        )
        return cur.fetchone() is not None

# ---- optional: cache of actuals (noop for now) ----

def apply_cached_actuals(events):
    """
    API-compat shim (noop). Залишено для сумісності зі старим кодом.
    Просто повертає events як є.
    """
    return events
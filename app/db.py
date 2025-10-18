# app/db.py
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager, closing
from datetime import datetime
from typing import List, Optional, Iterable, Tuple, Dict, Any

from .config import DB_PATH

# ---- налаштування sqlite ----
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # щоб мати доступ по імені колонок
    return conn

@contextmanager
def db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# ---- DDL ----
DDL = [
    """
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER NOT NULL,
        chat_id INTEGER NOT NULL,
        daily_time TEXT NOT NULL DEFAULT '09:00',
        impact_filter TEXT NOT NULL DEFAULT 'High,Medium',
        countries_filter TEXT NOT NULL DEFAULT '',
        alert_minutes INTEGER NOT NULL DEFAULT 30,
        out_chat_id INTEGER,
        lang_mode TEXT NOT NULL DEFAULT 'en',
        PRIMARY KEY (user_id, chat_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS sent_alerts (
        chat_id INTEGER NOT NULL,
        event_hash TEXT NOT NULL,
        kind TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (chat_id, event_hash, kind)
    );
    """,
]

with db() as conn:
    with closing(conn.cursor()) as cur:
        for stmt in DDL:
            cur.execute(stmt)

# ================= SUBSCRIPTIONS =================

def ensure_sub(user_id: int, chat_id: int) -> None:
    with db() as conn:
        with closing(conn.cursor()) as cur:
            cur.execute(
                """
                INSERT OR IGNORE INTO subscriptions (user_id, chat_id)
                VALUES (?, ?)
                """,
                (user_id, chat_id),
            )

def set_sub(user_id: int, chat_id: int, **kwargs) -> None:
    if not kwargs:
        return
    columns = ", ".join(f"{k}=?" for k in kwargs.keys())
    values = list(kwargs.values()) + [user_id, chat_id]
    with db() as conn:
        with closing(conn.cursor()) as cur:
            cur.execute(
                f"UPDATE subscriptions SET {columns} WHERE user_id=? AND chat_id=?",
                values,
            )

def get_sub(user_id: int, chat_id: int) -> Optional[Dict[str, Any]]:
    with db() as conn:
        with closing(conn.cursor()) as cur:
            cur.execute(
                "SELECT * FROM subscriptions WHERE user_id=? AND chat_id=?",
                (user_id, chat_id),
            )
            row = cur.fetchone()
            return dict(row) if row else None

def get_all_subs() -> List[Dict[str, Any]]:
    with db() as conn:
        with closing(conn.cursor()) as cur:
            cur.execute("SELECT * FROM subscriptions")
            rows = cur.fetchall()
            return [dict(r) for r in rows]

def unsubscribe(user_id: int, chat_id: int) -> None:
    with db() as conn:
        with closing(conn.cursor()) as cur:
            cur.execute(
                "DELETE FROM subscriptions WHERE user_id=? AND chat_id=?",
                (user_id, chat_id),
            )

# ================= SENT ALERTS =================

def mark_sent(chat_id: int, ev_hash: str, kind: str) -> None:
    with db() as conn:
        with closing(conn.cursor()) as cur:
            cur.execute(
                """
                INSERT OR IGNORE INTO sent_alerts (chat_id, event_hash, kind, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (chat_id, ev_hash, kind, datetime.utcnow().isoformat()),
            )

def was_sent(chat_id: int, ev_hash: str, kind: str) -> bool:
    with db() as conn:
        with closing(conn.cursor()) as cur:
            cur.execute(
                "SELECT 1 FROM sent_alerts WHERE chat_id=? AND event_hash=? AND kind=? LIMIT 1",
                (chat_id, ev_hash, kind),
            )
            return cur.fetchone() is not None
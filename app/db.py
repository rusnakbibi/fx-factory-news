import sqlite3
from contextlib import closing
from datetime import datetime
from .config import DB_PATH

DDL = [
    '''
    CREATE TABLE IF NOT EXISTS subscriptions (
        user_id INTEGER NOT NULL,
        chat_id INTEGER NOT NULL,
        daily_time TEXT NOT NULL DEFAULT '09:00',
        impact_filter TEXT NOT NULL DEFAULT 'High,Medium',
        countries_filter TEXT NOT NULL DEFAULT '',
        alert_minutes INTEGER NOT NULL DEFAULT 30,
        out_chat_id INTEGER,   -- куди слати (канал/група/той самий чат)
        lang_mode TEXT NOT NULL DEFAULT 'en', -- en|uk|auto
        PRIMARY KEY (user_id, chat_id)
    );
    ''',
    '''
    CREATE TABLE IF NOT EXISTS sent_alerts (
        chat_id INTEGER NOT NULL,
        event_hash TEXT NOT NULL,
        kind TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (chat_id, event_hash, kind)
    );
    '''
]

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

with closing(db()) as conn:
    cur = conn.cursor()
    for stmt in DDL:
        cur.executescript(stmt)
    conn.commit()

def ensure_sub(user_id: int, chat_id: int):
    with closing(db()) as conn:
        conn.execute("INSERT OR IGNORE INTO subscriptions (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
        conn.commit()

def set_sub(user_id: int, chat_id: int, **kwargs):
    ensure_sub(user_id, chat_id)
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [user_id, chat_id]
    with closing(db()) as conn:
        conn.execute(f"UPDATE subscriptions SET {sets} WHERE user_id=? AND chat_id=?", vals)
        conn.commit()

def get_sub(user_id: int, chat_id: int):
    with closing(db()) as conn:
        cur = conn.execute("SELECT * FROM subscriptions WHERE user_id=? AND chat_id=?", (user_id, chat_id))
        return cur.fetchone()

def get_all_subs():
    with closing(db()) as conn:
        cur = conn.execute("SELECT * FROM subscriptions")
        return cur.fetchall()

def mark_sent(chat_id: int, event_hash: str, kind: str):
    with closing(db()) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_alerts (chat_id, event_hash, kind, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, event_hash, kind, datetime.utcnow().isoformat()),
        )
        conn.commit()

def was_sent(chat_id: int, event_hash: str, kind: str) -> bool:
    with closing(db()) as conn:
        cur = conn.execute("SELECT 1 FROM sent_alerts WHERE chat_id=? AND event_hash=? AND kind=?", (chat_id, event_hash, kind))
        return cur.fetchone() is not None

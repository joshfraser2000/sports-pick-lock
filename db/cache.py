import sqlite3
import json
import time
import os
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "cache.db")


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT,
            expires_at REAL
        )"""
    )
    conn.commit()
    return conn


def cache_key(namespace: str, *args) -> str:
    raw = namespace + "|" + "|".join(str(a) for a in args)
    return hashlib.md5(raw.encode()).hexdigest()


def get(key: str):
    conn = _conn()
    row = conn.execute(
        "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    if row and row[1] > time.time():
        return json.loads(row[0])
    return None


def set(key: str, value, ttl: int):
    conn = _conn()
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
        (key, json.dumps(value, default=str), time.time() + ttl),
    )
    conn.commit()
    conn.close()


def clear_expired():
    conn = _conn()
    conn.execute("DELETE FROM cache WHERE expires_at <= ?", (time.time(),))
    conn.commit()
    conn.close()

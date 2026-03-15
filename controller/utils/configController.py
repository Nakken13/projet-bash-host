#!/usr/bin/python3

import sqlite3
import os

DB_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
DB_NAME = f"{DB_DIR}/monitor.db"

CONFIGS = {
    "history_size":   "1440",
    "alert_cpu":  "90",
    "alert_ram":  "90",
    "alert_disk": "90",
    "server_response_dead":    "1800",
    "graph_history":  "100",
    "mail_to":        "nahel.taqui@alumni.univ-avignon.fr",
    "mail_from":      "nahel.taqui@alumni.univ-avignon.fr",
    "smtp_host":      "partage.univ-avignon.fr",
    "smtp_port":      "25",
}


def setup_config():
    os.makedirs(DB_DIR, exist_ok=True)
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    for key, value in CONFIGS.items():
        cur.execute("INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)", (key, value))
    con.commit()
    con.close()


def get(key, cast=str):
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = cur.fetchone()
    con.close()
    raw = row[0] if row else CONFIGS.get(key)
    if raw is None:
        return None
    try:
        return cast(raw)
    except (ValueError, TypeError):
        return cast(CONFIGS[key])


def set(key, value):
    if key not in CONFIGS:
        raise ValueError(f"Clé de config inconnue : '{key}'")
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("UPDATE config SET value = ? WHERE key = ?", (str(value), key))
    if cur.rowcount == 0:
        cur.execute("INSERT INTO config (key, value) VALUES (?, ?)", (key, str(value)))
    con.commit()
    con.close()


def show():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("SELECT key, value FROM config ORDER BY key")
    rows = cur.fetchall()
    con.close()
    return {k: v for k, v in rows}


if __name__ == "__main__":
    setup_config()
    print("Configuration actuelle :\n")
    for key, value in show().items():
        print(f"  {key:<20} = {value}")

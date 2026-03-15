#!/usr/bin/python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import time
from datetime import datetime

import configController

DB_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
DB_NAME = f"{DB_DIR}/monitor.db"

METRICS = ["cpu", "ram", "disk"]


def detect_crises():

    if not os.path.exists(DB_NAME):
        print(f"[criseDetect] Base introuvable : {DB_NAME}")
        return []

    crises = []
    now = int(time.time())

    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()

    for metric in METRICS:
        seuil = configController.get(f"alert_{metric}", cast=float)
        max_silence = configController.get("server_response_dead", cast=int)

        cur.execute(f"""
            SELECT server, val, temps
            FROM {metric}
            WHERE temps IN (
                SELECT MAX(temps) FROM {metric} GROUP BY server
            )
        """)
        for server, val, temps in cur.fetchall():
            if val >= seuil:
                crises.append({
                    "type":      "seuil_alert",
                    "metric":    metric,
                    "server":    server,
                    "value":     round(val, 1),
                    "seuil_alert": seuil,
                    "timestamp": temps,
                    "message": (
                        f"[ALERTE SEUIL] {server} — {metric.upper()} "
                        f"à {val:.1f}% (seuil : {seuil:.0f}%)"
                    ),
                })

        cur.execute(f"""
            SELECT server, MAX(temps) AS last_seen
            FROM {metric}
            GROUP BY server
        """)
        for server, last_seen in cur.fetchall():
            if last_seen is None:
                continue
            silence_sec = now - last_seen
            if silence_sec > max_silence:
                silence_min = silence_sec // 60
                crises.append({
                    "type":      "silence",
                    "metric":    metric,
                    "server":    server,
                    "value":     None,
                    "seuil_alert": None,
                    "timestamp": last_seen,
                    "message": (
                        f"[ALERTE SILENCE] {server} — aucune donnée "
                        f"{metric.upper()} depuis {silence_min} min"
                    ),
                })

    con.close()
    return crises


def print_crises(crises_actuelles):
    print(f"\n{'='*62}")
    if not crises_actuelles:
        print("  [OK] Aucune situation de crise détectée.")
    else:
        print(f"  /!\\ {len(crises_actuelles)} SITUATION(S) DE CRISE DÉTECTÉE(S)")
        print(f"{'─'*62}")
        for c in crises_actuelles:
            ts = datetime.fromtimestamp(c["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {c['message']}")
            print(f"      Dernière donnée : {ts}")
    print(f"{'='*62}\n")


if __name__ == "__main__":
    crises = detect_crises()
    print_crises(crises)

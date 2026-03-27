#!/usr/bin/python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
#ajoute le dossier où se trouve le script aux chemins de recherche de Python. pour pouvoir importer config meme depuis un import de ce fichier

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

    max_silence = configController.get("server_response_dead", cast=int)

    # Alertes seuil — une par métrique (données récentes uniquement)
    for metric in METRICS:
        seuil = configController.get(f"alert_{metric}", cast=float)
        cur.execute(f"""
            SELECT server, val, temps
            FROM {metric}
            WHERE temps IN (
                SELECT MAX(temps) FROM {metric} GROUP BY server
            )
            AND temps > ?
        """, (now - max_silence,))
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
                        f"à {val:.1f}% (seuil : {seuil:.0f}%)"# arrondi aux dixieme pour val et aucun pour le seuil
                    ),
                })

    #cas du server silence
    cur.execute("SELECT server, MAX(temps) FROM cpu GROUP BY server")
    last_seen_map = {row[0]: row[1] for row in cur.fetchall()}

    # Ajoute les serveurs enregistrés mais sans aucune donnée
    cur.execute("SELECT server FROM server")
    for (srv,) in cur.fetchall():
        if srv not in last_seen_map:
            last_seen_map[srv] = None

    for server, last_seen in last_seen_map.items():
        silence_sec = now - last_seen if last_seen else max_silence + 1
        if silence_sec > max_silence:
            silence_min = silence_sec // 60
            crises.append({
                "type":      "silence",
                "metric":    "réseau",
                "server":    server,
                "value":     None,
                "seuil_alert": None,
                "timestamp": now,
                "last_seen": last_seen,
                "message": (
                    f"[ALERTE SILENCE] {server} — aucune donnée "
                    f"depuis {silence_min} min"
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
            ts = datetime.fromtimestamp(c["timestamp"]).strftime("%Y-%m-%d %H:%M:%S") if c["timestamp"] else "inconnue"
            print(f"  {c['message']}")
            print(f"      Dernière donnée : {ts}")
    print(f"{'='*62}\n")


if __name__ == "__main__":#sera run uniquement si pas importé
    crises = detect_crises()
    print_crises(crises)

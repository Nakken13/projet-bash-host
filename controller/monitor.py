#!/usr/bin/python3
import json
import os
from datetime import datetime

from utils import emailSender, criseDetect

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "db", "log_notif_email.json")
LOG_FILE   = os.path.join(BASE_DIR, "logs", "monitor.log")


def log(msg):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def crise_key(c):
    return f"{c['server']}:{c['metric']}:{c['type']}"


def run():
    current_crises = criseDetect.detect_crises()
    current_keys   = {crise_key(c): c for c in current_crises}
    previous_state = load_state()

    new_crises    = [c for k, c in current_keys.items() if k not in previous_state]
    resolved_keys = [k for k in previous_state if k not in current_keys]

    failed_keys = set()

    if new_crises:
        log(f"[monitor] {len(new_crises)} nouvelle(s) crise(s) détectée(s) :")
        for c in new_crises:
            log(f"  {c['message']}")
        ok = emailSender.send_alert(new_crises, log)
        if not ok:
            failed_keys = {crise_key(c) for c in new_crises}
            log("[monitor] Échec mail — ces crises seront renvoyées au prochain passage.")
    else:
        log("[monitor] Aucune nouvelle crise.")

    if resolved_keys:
        log(f"[monitor] {len(resolved_keys)} crise(s) résolue(s).")
        resolved = []
        for k in resolved_keys:
            server, metric, crisis_type = k.split(":", 2)
            if crisis_type == "silence":
                msg = f"[RÉSOLU] {server} — serveur de nouveau joignable"
            else:
                msg = f"[RÉSOLU] {server} — {metric.upper()} est revenu à la normale"
            log(f"  Résolu : {server} — {msg}")
            resolved.append({
                "type":      "resolved",
                "metric":    metric,
                "server":    server,
                "value":     None,
                "threshold": None,
                "timestamp": int(datetime.now().timestamp()),
                "message":   msg,
            })
        emailSender.send_alert(resolved, log)

    new_state = {
        k: {"ts": c["timestamp"]}
        for k, c in current_keys.items()
        if k not in failed_keys
    }
    save_state(new_state)


if __name__ == "__main__":
    run()

#!/usr/bin/python3
import json
import os
from datetime import datetime

from utils import emailSender, criseDetect

STATE_FILE = os.path.join(os.path.dirname(__file__), "db", "log_notif_email.json")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def crisis_key(c):
    """Clé unique identifiant une crise (server + metric + type)."""
    return f"{c['server']}:{c['metric']}:{c['type']}"


def run():
    current_crises = criseDetect.detect_crises()
    current_keys   = {crisis_key(c): c for c in current_crises}
    previous_state = load_state()

    new_crises      = [c for k, c in current_keys.items() if k not in previous_state]
    resolved_keys   = [k for k in previous_state if k not in current_keys]

    if new_crises:
        print(f"[monitor] {len(new_crises)} nouvelle(s) crise(s) — envoi du mail.")
        emailSender.send_alert(new_crises)
    else:
        print("[monitor] Aucune nouvelle crise.")

    if resolved_keys:
        print(f"[monitor] {len(resolved_keys)} crise(s) résolue(s).")
        resolved = []
        for k in resolved_keys:
            server, metric, crisis_type = k.split(":", 2)
            resolved.append({
                "type":      "resolved",
                "metric":    metric,
                "server":    server,
                "value":     None,
                "threshold": None,
                "timestamp": int(datetime.now().timestamp()),
                "message":   f"[RÉSOLU] {server} — {metric.upper()} est revenu à la normale",
            })
        emailSender.send_alert(resolved)

    new_state = {k: {"ts": c["timestamp"]} for k, c in current_keys.items()}
    save_state(new_state)


if __name__ == "__main__":
    run()

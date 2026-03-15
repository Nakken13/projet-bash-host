#!/usr/bin/python3

import sqlite3
import os

DB_DIR     = "../db"
DB_MONITOR = f"{DB_DIR}/monitor.db"
DB_ALERTS  = f"{DB_DIR}/alertes.db"

TABLES_MONITOR = ["ram", "cpu", "disk", "config", "server"]
TABLES_ALERTS  = ["alert"]


def drop_all():
    for db_path, tables in [(DB_MONITOR, TABLES_MONITOR), (DB_ALERTS, TABLES_ALERTS)]:
        if not os.path.exists(db_path):
            print(f"[cleanSql] {db_path} introuvable, ignoré.")
            continue
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        for table in tables:
            cur.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"[cleanSql] DROP TABLE {table} ({db_path})")
        con.commit()
        con.close()

    state = f"{DB_DIR}/log_notif_email.json"
    if os.path.exists(state):
        os.remove(state)
        print(f"[cleanSql] Supprimé : {state}")

    print("[cleanSql] Nettoyage terminé.")


if __name__ == "__main__":
    confirm = input("Supprimer toutes les tables ? (oui/non) : ").strip().lower()
    if confirm == "oui":
        drop_all()
    else:
        print("[cleanSql] Annulé.")

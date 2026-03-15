#!/usr/bin/python3

import sqlite3
import subprocess
import os
import json

import configController

DB_DIR  = "./db"
DB_NAME = f"{DB_DIR}/monitor.db"
os.makedirs(DB_DIR, exist_ok=True)
if not os.path.exists(DB_NAME):
    open(DB_NAME, 'w').close()
configController.setup_config()


def verif_table():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS ram(temps integer primary key, number_of_users int, user VARCHAR(20), server VARCHAR(20), val double)")
    cur.execute("CREATE TABLE IF NOT EXISTS cpu(temps integer primary key, number_of_users int, user VARCHAR(20), server VARCHAR(20), val double)")
    cur.execute("CREATE TABLE IF NOT EXISTS disk(temps integer primary key, number_of_users int, user VARCHAR(20), server VARCHAR(20), val double)")
    con.commit()
    con.close()


def setup_db_host():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS server(server VARCHAR(20) PRIMARY KEY, ip VARCHAR(15))")
    con.commit()
    con.close()
    return 
    

def get_guests():
    verif_table()
    setup_db_host()

    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("SELECT server, ip FROM server")
    rows = cur.fetchall()
    con.close()
    
    return {row[0]: row[1] for row in rows}



def recup_infos(ip):
    return subprocess.run(["ssh", f"collect@{ip}", "~/projet-bash-guests/sondes/sonde.sh"],capture_output=True, text=True)

def delete_old():
    history_size = configController.get("history_size", cast=int)
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    for table in ["ram", "cpu", "disk"]:
        cur.execute(f"DELETE FROM {table} WHERE temps NOT IN "
                    f"(SELECT temps FROM {table} ORDER BY temps DESC LIMIT {history_size})")
    con.commit()
    con.close()

def save_sql(data):
    delete_old()

    time = data["data"][0]["timestamp"]
    user = data["user"]
    server = data["server"]
    info_ram = data["data"][0]["sondes"]["ram"]
    info_cpu = data["data"][0]["sondes"]["cpu"]
    info_disk = data["data"][0]["sondes"]["disk"]
    number_of_users = data["number_of_users"]
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("INSERT INTO ram (temps, number_of_users, user, server, val) VALUES (?, ?, ?, ?, ?)", (time, number_of_users, user, server, info_ram))
    cur.execute("INSERT INTO cpu (temps, number_of_users, user, server, val) VALUES (?, ?, ?, ?, ?)", (time, number_of_users, user, server, info_cpu))
    cur.execute("INSERT INTO disk (temps, number_of_users, user, server, val) VALUES (?, ?, ?, ?, ?)", (time, number_of_users, user, server, info_disk))
    con.commit()
    con.close()

def save_all(serv):
    for server,ip in serv.items():
        data = json.loads(recup_infos(ip).stdout)
        save_sql(data)

def setup_serv_insert():
    '''guests = {
        "ubuntu-serv": "10.126.3.226",
        "ubuntu-serv2": "192.168.1.26",
        "ubuntu-serv3": "10.126.1.111",
        "ubuntu-serv4": "10.126.3.11"
    }'''
    
    guests = {
        "ubuntu-serv2": "192.168.1.26",
        "ubuntu-serv3": "192.168.1.27",
        "ubuntu-serv4": "192.168.1.26"
    }

    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
 
    for server, ip in guests.items():
        try:
            cur.execute("INSERT INTO server (server, ip) VALUES (?, ?)", (server, ip))
        except sqlite3.IntegrityError:
            pass # Ignore si déjà présent
            
    con.commit()
    con.close()
    print("[+] Données insérées.")

def vider():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS server")
    con.commit()
    con.close()
    print("[+] Table 'server' supprimée.")

def afficher_dernieres_lignes(n=5):
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()

    for table in ["ram", "cpu", "disk"]:
        print(f"\n{'='*60}")
        print(f"  Table : {table.upper()} — {n} dernières lignes")
        print(f"{'='*60}")

        cur.execute(f"""
            SELECT * FROM {table}
            ORDER BY temps DESC
            LIMIT {n}
        """)
        rows = cur.fetchall()

        if not rows:
            print("  (aucune donnée)")
            continue

        # En-têtes
        colonnes = [desc[0] for desc in cur.description]
        print("  " + " | ".join(f"{col:<15}" for col in colonnes))
        print("  " + "-" * (17 * len(colonnes)))

        for row in rows:
            print("  " + " | ".join(f"{str(val):<15}" for val in row))

    con.close()

setup_serv_insert()

guests = get_guests()
save_all(guests)

afficher_dernieres_lignes()
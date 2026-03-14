#!/usr/bin/python3

import feedparser
import sqlite3
import os

DB_DIR = "./db"
os.makedirs(DB_DIR, exist_ok=True)
DB_NAME = f"{DB_DIR}/alertes.db"
if not os.path.exists(DB_NAME):
    open(DB_NAME, 'w').close()

url = "https://www.cert.ssi.gouv.fr/alerte/feed/"
flux = feedparser.parse(url)

for alerte in flux.entries[-1:]:
    print(f"Titre : {alerte.title}")
    print(f"Date  : {alerte.published}")
    print(f"Lien  : {alerte.link}\n")

def verif_table():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS alert(lien TEXT PRIMARY KEY, titre TEXT, date TEXT)")
    con.commit()
    con.close()

def setup_db(flux):
    verif_table()
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    for alerte in flux.entries:
        cur.execute("INSERT OR IGNORE INTO alert(lien, titre, date) VALUES(?, ?, ?)", 
                    (alerte.link, alerte.title, alerte.published))
    con.commit()
    con.close()

def save_alert(flux):
    verif_table()
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    alerte = flux.entries[-1]
    cur.execute("INSERT OR IGNORE INTO alert(lien, titre, date) VALUES(?, ?, ?)", (alerte.link, alerte.title, alerte.published))
    con.commit()
    con.close()

setup_db(flux)
save_alert(flux)
#!/usr/bin/python3

import feedparser
import sqlite3
import os

DB_DIR = "db"
os.makedirs(DB_DIR, exist_ok=True)
DB_NAME = f"{DB_DIR}/alertes.db"
if not os.path.exists(DB_NAME):
    open(DB_NAME, 'w').close()

URL = "https://www.cert.ssi.gouv.fr/alerte/feed/"

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

def fetch_and_store():
    flux = feedparser.parse(URL)
    setup_db(flux)

if __name__ == "__main__":
    fetch_and_store()
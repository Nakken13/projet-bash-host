#!/usr/bin/python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from datetime import datetime

import pygal
from pygal.style import CleanStyle, DarkColorizedStyle
import configController

DB_DIR     = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db")
DB_MONITOR = f"{DB_DIR}/monitor.db"
DB_ALERTS  = f"{DB_DIR}/alertes.db"
OUTPUT_DIR = "./graphs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

METRICS = ["cpu", "ram", "disk"]
LABELS  = {"cpu": "CPU (%)", "ram": "RAM (%)", "disk": "Disque (%)"}
HISTORY_POINTS = lambda: configController.get("graph_history", cast=int)


# ── Requêtes base de données ─────────────────────────────────────────────────

def get_servers():
    if not os.path.exists(DB_MONITOR):
        return []
    con = sqlite3.connect(DB_MONITOR)
    cur = con.cursor()
    cur.execute("SELECT DISTINCT server FROM cpu ORDER BY server")
    servers = [row[0] for row in cur.fetchall()]
    con.close()
    return servers


def get_table_data(table, server):
    if not os.path.exists(DB_MONITOR):
        return []
    con = sqlite3.connect(DB_MONITOR)
    cur = con.cursor()
    cur.execute(f"""
        SELECT temps, val FROM {table}
        WHERE server = ?
        ORDER BY temps DESC
        LIMIT {HISTORY_POINTS()}
    """, (server,))
    rows = list(reversed(cur.fetchall()))
    con.close()
    return rows


def get_cert_alerts():
    if not os.path.exists(DB_ALERTS):
        return []
    con = sqlite3.connect(DB_ALERTS)
    cur = con.cursor()
    cur.execute("SELECT titre, date, lien FROM alert ORDER BY date DESC LIMIT 10")
    rows = cur.fetchall()
    con.close()
    return rows


def get_last_values(server):
    result = {}
    for metric in METRICS:
        rows = get_table_data(metric, server)
        result[metric] = round(rows[-1][1], 1) if rows else None
    return result


def fmt_ts(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M\n%d/%m")


# ── Graphiques Pygal — sauvegarde fichier ────────────────────────────────────

def chart_server(server):
    chart = pygal.Line(
        title=f"Monitoring — {server}",
        x_label_rotation=45,
        legend_at_bottom=True,
        show_dots=False,
        stroke_style={"width": 2},
        style=CleanStyle,
        y_title="Utilisation (%)",
        range=(0, 100),
    )
    labels_set = False
    for metric in METRICS:
        rows = get_table_data(metric, server)
        if not rows:
            continue
        if not labels_set:
            chart.x_labels = [fmt_ts(r[0]) for r in rows]
            labels_set = True
        chart.add(LABELS[metric], [round(r[1], 1) for r in rows])

    if not labels_set:
        print(f"[viz] Aucune donnée pour {server}.")
        return None
    path = os.path.join(OUTPUT_DIR, f"{server}_metrics.svg")
    chart.render_to_file(path)
    print(f"[viz] {path}")
    return path


def chart_comparison(metric):
    servers = get_servers()
    if not servers:
        return None
    chart = pygal.Line(
        title=f"Comparaison {LABELS[metric]} — tous serveurs",
        x_label_rotation=45,
        legend_at_bottom=True,
        show_dots=False,
        stroke_style={"width": 2},
        style=DarkColorizedStyle,
        y_title="Utilisation (%)",
        range=(0, 100),
    )
    labels_set = False
    for server in servers:
        rows = get_table_data(metric, server)
        if not rows:
            continue
        if not labels_set:
            chart.x_labels = [fmt_ts(r[0]) for r in rows]
            labels_set = True
        chart.add(server, [round(r[1], 1) for r in rows])

    if not labels_set:
        print(f"[viz] Aucune donnée pour la comparaison {metric}.")
        return None
    path = os.path.join(OUTPUT_DIR, f"comparison_{metric}.svg")
    chart.render_to_file(path)
    print(f"[viz] {path}")
    return path


def chart_cert_alerts():
    alerts = get_cert_alerts()
    if not alerts:
        print("[viz] Aucune alerte CERT à afficher.")
        return None
    chart = pygal.Bar(
        title="Dernières alertes CERT-SSI",
        x_label_rotation=50,
        style=DarkColorizedStyle,
        show_legend=False,
        print_values=False,
    )
    chart.x_labels = [a[0][:45] + ("…" if len(a[0]) > 45 else "") for a in alerts]
    chart.add("CERT-SSI", [{"value": 1, "xlink": a[2]} for a in alerts])
    path = os.path.join(OUTPUT_DIR, "cert_alerts.svg")
    chart.render_to_file(path)
    print(f"[viz] {path}")
    return path


# ── Rendu SVG en mémoire (pour Flask) ───────────────────────────────────────

def render_server_svg(server):
    chart = pygal.Line(
        title=f"Monitoring — {server}",
        x_label_rotation=45,
        legend_at_bottom=True,
        show_dots=False,
        stroke_style={"width": 2},
        style=CleanStyle,
        y_title="Utilisation (%)",
        range=(0, 100),
        width=800,
        height=350,
    )
    labels_set = False
    for metric in METRICS:
        rows = get_table_data(metric, server)
        if not rows:
            continue
        if not labels_set:
            chart.x_labels = [fmt_ts(r[0]) for r in rows]
            labels_set = True
        chart.add(LABELS[metric], [round(r[1], 1) for r in rows])
    return chart.render(is_unicode=True) if labels_set else None


def render_comparison_svg(metric):
    servers = get_servers()
    chart = pygal.Line(
        title=f"Comparaison {LABELS.get(metric, metric)} — tous serveurs",
        x_label_rotation=45,
        legend_at_bottom=True,
        show_dots=False,
        stroke_style={"width": 2},
        style=DarkColorizedStyle,
        y_title="Utilisation (%)",
        range=(0, 100),
        width=800,
        height=350,
    )
    labels_set = False
    for server in servers:
        rows = get_table_data(metric, server)
        if not rows:
            continue
        if not labels_set:
            chart.x_labels = [fmt_ts(r[0]) for r in rows]
            labels_set = True
        chart.add(server, [round(r[1], 1) for r in rows])
    return chart.render(is_unicode=True) if labels_set else None


# ── Point d'entrée ───────────────────────────────────────────────────────────

def generate_all():
    servers = get_servers()
    if not servers:
        print("[viz] Aucun serveur trouvé dans la base de données.")
        return

    print(f"[viz] Génération des graphiques SVG dans ./{OUTPUT_DIR}/")
    print(f"[viz] {len(servers)} serveur(s) — {HISTORY_POINTS()} points d'historique\n")

    for server in servers:
        chart_server(server)
    for metric in METRICS:
        chart_comparison(metric)
    chart_cert_alerts()

    print(f"\n[viz] Terminé. Ouvrez les fichiers SVG dans un navigateur.")


if __name__ == "__main__":
    generate_all()

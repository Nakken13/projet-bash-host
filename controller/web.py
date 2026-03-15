#!/usr/bin/python3

from flask import Flask, render_template, request, redirect, url_for, flash

import configController
import criseDetect
import visualization

configController.setup_config()

app = Flask(__name__)
app.secret_key = "monitorbgnahel"

METRICS = ["cpu", "ram", "disk"]
METRIC_LABELS = {"cpu": "CPU", "ram": "RAM", "disk": "Disque"}

CONFIG_META = {
    "history_size":        {"label": "Taille de l'historique",          "unit": "mesures",  "type": "int"},
    "alert_cpu":           {"label": "Seuil d'alerte CPU",              "unit": "%",        "type": "float"},
    "alert_ram":           {"label": "Seuil d'alerte RAM",              "unit": "%",        "type": "float"},
    "alert_disk":          {"label": "Seuil d'alerte Disque",           "unit": "%",        "type": "float"},
    "server_response_dead":{"label": "Délai hors-ligne",                "unit": "secondes", "type": "int"},
    "graph_history":       {"label": "Points affichés dans les graphiques", "unit": "points","type": "int"},
    "mail_to":             {"label": "Destinataire des alertes mail",   "unit": "",         "type": "str"},
    "mail_from":           {"label": "Expéditeur",                      "unit": "",         "type": "str"},
    "smtp_host":           {"label": "Serveur SMTP",                    "unit": "",         "type": "str"},
    "smtp_port":           {"label": "Port SMTP",                       "unit": "",         "type": "int"},
}

@app.route("/")
def index():
    servers  = visualization.get_servers()
    crises   = criseDetect.detect_crises()
    alerts   = visualization.get_cert_alerts()[:5]

    # Résumé par serveur : dernières valeurs + statut
    servers_data = []
    crisis_servers = {c["server"] for c in crises}
    for s in servers:
        vals = visualization.get_last_values(s)
        servers_data.append({
            "name":   s,
            "values": vals,
            "crisis": s in crisis_servers,
        })

    return render_template("index.html",
        servers=servers_data,
        crises=crises,
        alerts=alerts,
        metrics=METRICS,
        metric_labels=METRIC_LABELS,
    )

@app.route("/server/<name>")
def server_detail(name):
    servers = visualization.get_servers()
    if name not in servers:
        return render_template("404.html", msg=f"Serveur '{name}' introuvable."), 404

    svg     = visualization.render_server_svg(name)
    vals    = visualization.get_last_values(name)
    crises  = [c for c in criseDetect.detect_crises() if c["server"] == name]

    return render_template("server.html",
        server=name,
        svg=svg,
        values=vals,
        crises=crises,
        metrics=METRICS,
        metric_labels=METRIC_LABELS,
    )
@app.route("/compare/<metric>")
def compare(metric):
    if metric not in METRICS:
        return render_template("404.html", msg=f"Métrique '{metric}' inconnue."), 404

    svg = visualization.render_comparison_svg(metric)
    return render_template("compare.html",
        metric=metric,
        label=METRIC_LABELS.get(metric, metric),
        svg=svg,
        metrics=METRICS,
        metric_labels=METRIC_LABELS,
    )

@app.route("/alerts")
def alerts():
    all_alerts = visualization.get_cert_alerts()
    return render_template("alerts.html",
        alerts=all_alerts,
        metrics=METRICS,
        metric_labels=METRIC_LABELS,
    )

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        errors = []
        for key, meta in CONFIG_META.items():
            val = request.form.get(key, "").strip()
            if not val:
                continue
            try:
                if meta["type"] in ("int", "float"):
                    cast = int if meta["type"] == "int" else float
                    cast(val)   # validation
                configController.set(key, val)
            except ValueError:
                errors.append(f"Valeur invalide pour « {meta['label']} » : {val}")

        if errors:
            for e in errors:
                flash(e, "error")
        else:
            flash("Configuration mise à jour.", "success")
        return redirect(url_for("settings"))

    config = configController.show()
    return render_template("settings.html",
        config=config,
        config_meta=CONFIG_META,
        metrics=METRICS,
        metric_labels=METRIC_LABELS,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)

#!/usr/bin/python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import configController

SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

DEFAULT = """\
Rapport de monitoring automatique
Date : {{ date }}

{{ nb_crises }} situation(s) de crise détectée(s) :

{% for crise in crises %}  [{{ crise.type | upper }}] {{ crise.metric | upper }} — {{ crise.server }}
    {{ crise.message }}
    Horodatage : {{ crise.ts_fmt }}
{% endfor %}
--
Surveillance du parc informatique,
TAQUI Nahel L2G1 - CERI
"""

def _cfg(key, cast=str):
    return configController.get(key, cast=cast)

def render_body(crises):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for c in crises:
        if c.get("timestamp"):
            c["ts_fmt"] = datetime.fromtimestamp(c["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        else:
            c["ts_fmt"] = "inconnu"

    lines = [
        f"Rapport de monitoring — {date_str}",
        f"\n{len(crises)} situation(s) de crise :\n",
    ]
    for c in crises:
        lines.append(f"  - {c['message']}  (détecté le {c['ts_fmt']})")
    lines.append("\n-- Système de monitoring L2S4 CERI")
    return "\n".join(lines)


def send_alert(crises):
    """Envoie un e-mail d'alerte si la liste de crises est non vide."""
    if not crises:
        print("[emailSender] Aucune crise détectée — pas d'e-mail envoyé.")
        return

    smtp_host = _cfg("smtp_host")
    smtp_port = _cfg("smtp_port", cast=int)
    from_addr = _cfg("mail_from")
    to_addr   = _cfg("mail_to")

    body = render_body(crises)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[MONITORING] {len(crises)} alerte(s) détectée(s)"
    msg["From"]    = from_addr
    msg["To"]      = to_addr
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            if SMTP_USER and SMTP_PASS:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        print(f"[emailSender] E-mail envoyé à {to_addr} ({len(crises)} alerte(s)).")
    except ConnectionRefusedError:
        print(f"[emailSender] Connexion refusée par {smtp_host}:{smtp_port}.")
    except smtplib.SMTPException as e:
        print(f"[emailSender] Erreur SMTP : {e}")
    except OSError as e:
        print(f"[emailSender] Erreur réseau : {e}")


if __name__ == "__main__":
    from criseDetect import detect_crises
    crises = detect_crises()

    if crises:
        for c in crises:
            print(f"  {c['message']}")
    else:
        print("[emailSender] Aucune crise — test SMTP ignoré.")

    send_alert(crises)

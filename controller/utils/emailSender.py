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


def render_body(crises):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"Rapport de monitoring — {date_str}\n\n{len(crises)} situation(s) de crise :\n"]
    for c in crises:
        ts = datetime.fromtimestamp(c["timestamp"]).strftime("%Y-%m-%d %H:%M:%S") if c.get("timestamp") else "inconnu"
        lines.append(f"  - {c['message']}  (détecté le {ts})")
    lines.append("\n Système de monitoring L2S4 CERI - TAQUI Nahel Groupe 1")
    return "\n".join(lines)


def send_alert(crises, log=print):
    if not crises:
        log("[emailSender] Aucune crise — pas d'e-mail envoyé.")
        return

    smtp_host = configController.get("smtp_host")
    smtp_port = configController.get("smtp_port", cast=int)
    from_addr = configController.get("mail_from")
    to_addr   = configController.get("mail_to")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[MONITORING] {len(crises)} alerte(s) détectée(s)"
    msg["From"]    = from_addr
    msg["To"]      = to_addr
    msg.attach(MIMEText(render_body(crises), "plain", "utf-8"))

    log(f"[emailSender] Tentative envoi → {to_addr} via {smtp_host}:{smtp_port}")
    try:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
            if SMTP_USER and SMTP_PASS:
                server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(from_addr, [to_addr], msg.as_string())
        log(f"[emailSender] E-mail envoyé à {to_addr} ({len(crises)} alerte(s)).")
    except ConnectionRefusedError:
        log(f"[emailSender] Connexion refusée par {smtp_host}:{smtp_port}.")
    except smtplib.SMTPException as e:
        log(f"[emailSender] Erreur SMTP : {e}")
    except OSError as e:
        log(f"[emailSender] Erreur réseau : {e}")


if __name__ == "__main__":
    from criseDetect import detect_crises
    crises = detect_crises()
    for c in crises:
        print(f"  {c['message']}")
    send_alert(crises)

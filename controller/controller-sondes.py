#!/usr/bin/python3

import subprocess
import json
import os

#guests = {"nt": "10.126.3.11","user2":"10.126.1.111","user3":"10.126.3.226"}

guests = {"user3": "172.20.10.10"}

def recup_log(guests):
    if not os.path.exists("logs"):
        os.makedirs("logs")

    for user, ip in guests.items():
        print(f"[*] Connexion en cours : {user}@{ip}...", flush=True)

        res = subprocess.run(
            ["ssh", f"{user}@{ip}", "~/projet-bash-guests/sondes/sonde.sh"],
            capture_output=True, text=True
        )

        if res.returncode == 0:
            new_entry = json.loads(res.stdout)

            log_path = f"logs/log-{user}.json"
            try:
                with open(log_path) as f:
                    log = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                log = {"logs": []}

            log["logs"].append(new_entry)

            logs_str = ",\n        ".join(json.dumps(e) for e in log["logs"])
            output = '{\n    "logs": [\n        ' + logs_str + '\n    ]\n}'
            with open(log_path, "w") as f:
                f.write(output)

            print(f"[+] Log récupéré -> {log_path}", flush=True)
        else:
            print(f"[-] Échec ssh pour {user} (code: {res.returncode})", flush=True)

def recup_log_os(guests):
    if not os.path.exists("logs"):
        os.system("mkdir logs")

    for user, ip in guests.items():
        print(f"[*] Connexion en cours : {user}@{ip}...", flush=True)
        res = os.system(f"ssh {user}@{ip} '~/projet-bash-guests/sondes/sonde.sh' >> logs/log-{user}.json")
        if res == 0:
            print(f"[+] Log récupéré -> logs/log-{user}.json", flush=True)
        else:
            print(f"[-] Échec ssh pour {user} (code: {res})", flush=True)

def recup_alerts():
    os.system(f"python3 verif_alert.py >> logs/log-alerts/alerts.json")
    


recup_log(guests)


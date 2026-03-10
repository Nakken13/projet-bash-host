#!/bin/python
import os
#ip = os.popen("hostname -I | awk '{print $1}'").read().strip()

guests = {"nt": "172.20.10.2"}

def recup_log(guests):
    if not os.path.exists("logs"):
        os.system("mkdir logs")
        
    for user, ip in guests.items():
        print(f"[*] Connexion en cours : {user}@{ip}...", flush=True)
        res = os.system(f"ssh {user}@{ip} ~/projet-bash-guests/sondes/sonde.sh >> logs/log-{user}.json")
        if res == 0:
            print(f"[+] Log récupéré → logs/log-{user}.json", flush=True)
        else:
            print(f"[-] Échec sshpass pour {user} (code: {res})", flush=True)

recup_log(guests)
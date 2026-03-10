#!/bin/python
import os

guests = {"nt": "azerty","user2":"azerty", "user3":"azerty", "user4":"azerty"}

def recup_log(guests):
    if not os.path.exists("logs"):
        os.system("mkdir logs")
        
    for user, passwd in guests.items():
        print(f"[*] Connexion en cours : {user}@10.0.2.15...", flush=True)
        ret = os.system(f"sshpass -p '{passwd}' ssh -o StrictHostKeyChecking=no -p 22 {user}@10.0.2.15 ~/projet-bash-guests/sondes/sonde.sh >> logs/log-{user}.json 2>&1")
        if ret == 0:
            print(f"[+] Log récupéré → logs/log-{user}.json", flush=True)
        else:
            print(f"[-] Échec sshpass pour {user} (code: {ret})", flush=True)

recup_log(guests)
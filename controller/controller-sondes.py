#!/bin/python
import os

guests = {"nt": "azerty","user2":"azerty", "user3":"azerty", "user4":"azerty"}

def recup_log(guests):
    if not os.path.exists("logs"):
        os.system("mkdir logs")
        
    for user, passwd in guests.items():
        os.system(f"sshpass -p '{passwd}' ssh -o StrictHostKeyChecking=no -p 22 {user}@10.0.2.15 ~/projet-bash-guests/sondes/sonde.sh >> logs/log-{user}.json 2>&1")
recup_log(guests)



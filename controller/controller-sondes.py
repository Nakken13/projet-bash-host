import os

guests = {"nt": "azerty","user2":"azerty", "user3":"azerty", "user4":"azerty", "user5":"azerty"}

def recup_log(guests):
    for user, passwd in guests.items():
        data = os.system(f"sshpass -p '{passwd}' ssh -p 22 {user}@10.0.2.15 ~/sondes/sonde.sh")
        os.system(f"cd logs && {data}>>log-{user}.json && cd ..")

recup_log(guests)
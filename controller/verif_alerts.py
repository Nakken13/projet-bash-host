import feedparser

url = "https://www.cert.ssi.gouv.fr/alerte/feed/"
flux = feedparser.parse(url)

# Affiche les 3 dernières alertes
for alerte in flux.entries[:3]:
    print(f"Titre : {alerte.title}")
    print(f"Lien : {alerte.link}\n")
    print(f"Date : {alerte.date}\n")


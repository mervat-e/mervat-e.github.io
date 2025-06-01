import json
from datetime import datetime

path = "backend/resources/user_data/tiktok/user_data_tiktok_cous.json"

# Charger les données
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Accéder à la liste des vidéos
video_list = data["Your Activity"]["Watch History"]["VideoList"]

# Convertir les dates en objets datetime
for video in video_list:
    video["ParsedDate"] = datetime.strptime(video["Date"], "%Y-%m-%d %H:%M:%S")

# Ajouter la propriété timepertiktok
for i in range(len(video_list)):
    if i == 0 :
        # La première vidéo (la plus nouvelle) n'a pas de vidéo après elle
        video_list[i]["timepertiktok"] = 0
    else:
        # Différence entre vidéo i et la suivante (plus ancienne)
        delta = (video_list[i - 1]["ParsedDate"] - video_list[i]["ParsedDate"]).total_seconds()
        video_list[i]["timepertiktok"] = delta

# Supprimer la clé intermédiaire "ParsedDate"
for video in video_list:
    del video["ParsedDate"]

# Enregistrer dans un nouveau fichier JSON
with open("time_cous_tiktok.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


filtered_video_list = [video_list[0]] + [
    video for video in video_list[1:] if video["timepertiktok"] >= 3.0
]
data["Your Activity"]["Watch History"]["VideoList"] = filtered_video_list

# Enregistrer dans un nouveau fichier JSON
with open("filtered_cous_tiktok.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
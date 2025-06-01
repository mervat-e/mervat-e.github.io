import json
from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
import os

OUTPUT_DIR = "frontend/static/img"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Charger les données
with open("backend/resources/user_data/tiktok/user_data_tiktok_2.json", encoding="utf-8") as f:
    data = json.load(f)

# Extraire les heures
watch_history = data["Your Activity"]["Watch History"]["VideoList"]
hours = []

for item in watch_history:
    dt = datetime.strptime(item["Date"], "%Y-%m-%d %H:%M:%S")
    hours.append(dt.hour)

# === 1. Fréquences par heure avec alertes ===
hour_counts = Counter(hours)
hour_labels = [f"{h:02d}h" for h in range(24)]
hour_values = [hour_counts.get(h, 0) for h in range(24)]

colors = ['indianred' if count > 1000 else 'cornflowerblue' for count in hour_values]

plt.figure(figsize=(12, 5))
bars = plt.bar(hour_labels, hour_values, color=colors)
plt.title("Fréquence de visionnage TikTok par heure")
plt.xlabel("Heure de la journée")
plt.ylabel("Nombre de vidéos vues")
plt.grid(axis="y", linestyle="--", alpha=0.5)

# Ajouter les alertes
for i, value in enumerate(hour_values):
    if value > 1000:
        plt.text(i, value + 10, '⚠️', ha='center', va='bottom', fontsize=14)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "FrequenceVisionnageParHeure.png"))
plt.show()

# === 2. Fréquences par tranche horaire ===
def get_time_slot(hour):
    if 0 <= hour <= 5:
        return "Nuit"
    elif 6 <= hour <= 11:
        return "Matin"
    elif 12 <= hour <= 17:
        return "Après-midi"
    else:
        return "Soir"

slots = [get_time_slot(h) for h in hours]
slot_counts = Counter(slots)
slot_order = ["Nuit", "Matin", "Après-midi", "Soir"]
slot_values = [slot_counts.get(slot, 0) for slot in slot_order]

plt.figure(figsize=(6, 4))
plt.bar(slot_order, slot_values, color="mediumpurple")
plt.title("Fréquence de visionnage TikTok par tranche horaire")
plt.xlabel("Tranche horaire")
plt.ylabel("Nombre de vidéos vues")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "FrequenceVisionnageParTrancheJournee.png"))
plt.show()

# Enregistrer les alertes dans le fichier alerts.json
alerts_path = os.path.join("frontend", "static", "alerts.json")

frequency_alerts = {
    "hourly_alert": [f"{h:02d}h" for h, v in hour_counts.items() if v > 1000],
    "timeslot_alert": [slot for slot, v in slot_counts.items() if v > 6000]
}

# Charger les alertes existantes
if os.path.exists(alerts_path):
    with open(alerts_path, "r", encoding="utf-8") as f:
        try:
            all_alerts = json.load(f)
        except json.JSONDecodeError:
            all_alerts = {}
else:
    all_alerts = {}

# Fusionner les nouvelles alertes
all_alerts["frequency_alerts"] = frequency_alerts

with open(alerts_path, "w", encoding="utf-8") as f:
    json.dump(all_alerts, f, indent=2, ensure_ascii=False)


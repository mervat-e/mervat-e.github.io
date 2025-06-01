import json
from collections import Counter
from datetime import datetime, timezone, timedelta
import matplotlib.pyplot as plt
import os

# === Configurations ===
METADATA_PATH = "backend/resources/tiktok_video/tiktok_metadata.json"
OUTPUT_DIR = "frontend/static/img"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Charger les données ===
with open(METADATA_PATH, encoding="utf-8") as f:
    data = json.load(f)

metadata = data.get("metadata", {})

# === Extraction des heures à partir des timestamps ===
hours = []

for video in metadata.values():
    if not isinstance(video, dict):
        continue
    for comment in video.get("first_comments", []):
        try:
            timestamp = int(comment["timestamp"])
            # Adapter à ton fuseau horaire (UTC+2 pour France en été)
            dt = datetime.fromtimestamp(timestamp, tz=timezone(timedelta(hours=2)))
            hours.append(dt.hour)
        except (KeyError, ValueError, TypeError):
            continue

# === 1. Fréquences par heure ===
hour_counts = Counter(hours)
hour_labels = [f"{h:02d}h" for h in range(24)]
hour_values = [hour_counts.get(h, 0) for h in range(24)]

plt.figure(figsize=(12, 5))
plt.bar(hour_labels, hour_values, color="cornflowerblue")
plt.title("Fréquence des commentaires TikTok par heure (heure locale)")
plt.xlabel("Heure de la journée")
plt.ylabel("Nombre de commentaires")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "comments_by_hour.png"))
plt.close()

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
plt.title("Fréquence des commentaires TikTok par tranche horaire")
plt.xlabel("Tranche horaire")
plt.ylabel("Nombre de commentaires")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "comments_by_timeslot.png"))
plt.close()

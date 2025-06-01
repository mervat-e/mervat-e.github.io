# File: frontend/scripts/analyse_health_content.py

import json
import os
import re
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# === Configuration des chemins ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
metadata_path = os.path.join(BASE_DIR, "..", "..", "backend", "resources", "tiktok_video", "tiktok_metadata.json")
output_dir = os.path.join(BASE_DIR, "..", "static", "img")
os.makedirs(output_dir, exist_ok=True)

# === Chargement des métadonnées TikTok ===
with open(metadata_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

metadata = raw_data.get("metadata", {})

# === Catégories ===
EMOTION_CATS = {
    "happy": [
        "happy", "joy", "smile", "laugh", "lol", "fun", "funny", "happiness", "bliss",
        "cheerful", "comedy", "cute", "adorable", "love", "goodvibes", "positivity",
        "heartwarming", "satisfying", "friendship", "celebration", "grateful"
    ],
    "sad": [
        "sad", "cry", "grief", "tears", "lonely", "depress", "heartbreak", "broken",
        "lost", "trauma", "anxiety", "pain", "stress", "war", "mourning", "melancholy",
        "struggle", "mentalhealth", "burnout", "fear", "emotional"
    ]
}

HEALTH_CATS = {
    "cleaning": [
        "clean", "laundry", "tidy", "organize", "declutter", "sanitize", "disinfect",
        "spotless", "springcleaning", "cleantok"
    ],
    "cooking": [
        "cook", "recipe", "kitchen", "bake", "mealprep", "cooking", "chef", "homemade",
        "instafood", "snacks", "cuisine", "comfortfood"
    ],
    "weight": [
        "weight", "diet", "loseweight", "weightloss", "gainweight", "bodytransformation",
        "fitnessjourney", "scale", "bmi", "bodygoals"
    ],
    "sport": [
        "sport", "exercise", "workout", "gym", "training", "cardio", "running", "yoga",
        "fit", "fitness", "lifting", "stretching", "jogging", "athlete"
    ],
    "food": [
        "food", "burger", "pizza", "salad", "snack", "noodles", "sushi", "dessert",
        "fastfood", "streetfood", "vegan", "vegetarian", "meat", "breakfast", "dinner", "brunch"
    ],
    "calories": [
        "calorie", "calories", "kcal", "macros", "nutrition", "lowcarb", "highprotein",
        "countingcalories", "dieting"
    ],
    "beauty": [
        "beauty", "makeup", "skincare", "glowup", "beautyroutine", "selfcare", "acne",
        "serum", "facemask", "lipstick", "eyeshadow", "hairstyle"
    ],
    "fashion": [
        "fashion", "style", "outfit", "ootd", "wardrobe", "trendy", "clothing", "accessories",
        "streetwear", "runway", "aesthetic", "fashionista"
    ],
    "motivation": [
        "motivation", "inspiration", "grind", "goal", "focus", "nevergiveup", "discipline",
        "success", "growth", "mindset", "ambition", "dailyhabits", "confidence", "determination"
    ]
}

ALL_CATS = {**EMOTION_CATS, **HEALTH_CATS}

# === Fonction de classification ===
def classify_hashtag(tag):
    tag = tag.lower()
    for cat, words in ALL_CATS.items():
        if any(re.search(rf"\b{re.escape(w)}\b", tag) for w in words):
            return cat
    return None

# === Comptage par catégorie ===
category_counts = {}
for video_id, video in metadata.items():
    if not isinstance(video, dict):
        print(f"⚠️ Entrée ignorée (type non valide) : {video_id}")
        continue

    hashtags = video.get("hashtags", [])
    for tag in hashtags:
        category = classify_hashtag(tag)
        if category:
            category_counts[category] = category_counts.get(category, 0) + 1

# === Table et Barplot ===
df = pd.DataFrame.from_dict(category_counts, orient="index", columns=["Hashtag Count"])
df = df.sort_values(by="Hashtag Count", ascending=False)

plt.figure(figsize=(10, 5))
plt.bar(df.index, df["Hashtag Count"], color="skyblue")
plt.title("Hashtag Frequency by Category")
plt.ylabel("Frequency")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "hashtags_barplot.png"))
plt.close()

# === Graphe de relations ===
G = nx.Graph()
for cat, count in category_counts.items():
    G.add_node(cat, size=count)

edges = [
    ("cooking", "food"),
    ("weight", "calories"),
    ("fashion", "beauty"),
    ("sport", "motivation"),
    ("happy", "motivation")
]

for a, b in edges:
    if a in G.nodes and b in G.nodes:
        G.add_edge(a, b)

plt.figure(figsize=(10, 10))
pos = nx.spring_layout(G, k=0.8, iterations=200, seed=42)
sizes = [np.log1p(G.nodes[node]['size']) * 500 + 200 for node in G.nodes()]

node_colors = []
for node in G.nodes():
    if node in EMOTION_CATS:
        node_colors.append('coral')
    elif node in HEALTH_CATS:
        node_colors.append('lightseagreen')
    else:
        node_colors.append('gray')

nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color=node_colors, alpha=0.9)
nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold", font_color="black")
plt.title("Content Category Clustering (Based on Defined Relationships)", fontsize=14)
plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, "category_graph.png"))
plt.close()

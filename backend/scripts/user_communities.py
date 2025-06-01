import sys
import os
import requests
import json
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path
from detoxify import Detoxify
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from sentence_transformers import SentenceTransformer, util
from collections import defaultdict
import numpy as np
import matplotlib.cm as cm
import plotly.express as px
import pandas 
import random
import kaleido

# Get metadata 

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
path = os.path.join(base_dir, "backend", "resources", "tiktok_video", "tiktok_metadata.json")

data = None 

with open(path, "r", encoding="utf-8") as f:

    data = json.load(f)



# Call API to get followings

id_user = 2

url = f"http://localhost:8000/api/v0/user/tiktok/following?id={id_user}"

response = requests.get(url)

following_list = []

if response.status_code == 200:

    following_list = response.json()

else:

    print(f"Erreur {response.status_code}: {response.json()}")



# Find followings in metadata and get description 

model = SentenceTransformer('all-MiniLM-L6-v2')


# Define keywords for communities 

community_keywords = {
    "Fashion": ["fashion", "style", "outfit", "clothes", "aesthetic"],
    "Sport": ["sport", "fit", "gym", "workout"],
    "Food": ["food", "recipe", "ingredient", "snack"],
    "Beauty" : ["beauty", "makeup", "makeup product"]
}

problem_keywords = {

        "ED": ["anorexia", "bulimia", "purge", "noeat"],
        "Body Image": ["skinny", "thin", "weight loss", "fat", "body checking", "beauty standards"]
}

category_totals = defaultdict(float)
category_counts = defaultdict(int)


for following in following_list:

    print(f"\n---------- Analyse compte {following} -------------")

    user_data = data["account_metadata"].get(following)
    if user_data is None:
        continue

    biography = user_data.get("biography", "Pas de bio")
    embedding_bio = model.encode(biography, convert_to_tensor=True)

    for cat_name, keywords in community_keywords.items():
        emb_keywords = model.encode(keywords, convert_to_tensor=True)
        scores = util.cos_sim(embedding_bio, emb_keywords)

        print(f"\n🔍 Catégorie : {cat_name}")
        for idx, (keyword, score) in enumerate(zip(keywords, scores[0])):
            print(f"  - '{keyword}' (index {idx}) → Similarité : {score.item():.4f}")

        score_max = scores[0].max().item()

        category_totals[cat_name] += score_max
        category_counts[cat_name] += 1

category_avg_scores = {
    cat: category_totals[cat] / category_counts[cat]
    for cat in category_totals
    if category_counts[cat] > 0
}


def bubble_chart_plotly(category_scores, title="Patient's social network interests"):

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    save_path = os.path.join(base_dir, "frontend", "static", "img")

    categories = list(category_scores.keys())
    scores = list(category_scores.values())

    x_pos = [random.uniform(-1, 1) for _ in categories]
    y_pos = [random.uniform(-1, 1) for _ in categories]

    df = {
        "Catégorie": categories,
        "Score": scores,
        "Taille": [s ** 2 * 5000 for s in scores],
        "x": x_pos,
        "y": y_pos
    }

    fig = px.scatter(
        df,
        x="x",
        y="y",
        size="Taille",
        color="Catégorie",
        size_max=150,
        title=title,
        hover_name="Catégorie",
        text="Catégorie",
    )

    fig.update_traces(
        marker=dict(opacity=0.7, line=dict(width=2, color='DarkSlateGrey')),
        textposition='middle center',
        textfont_size=12
    )
    fig.update_layout(showlegend=False, xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False))
    fig.show()

    # filename = os.path.join(save_path, f"community_analysis_user{id_user}.png")
    filename = f"community_analysis_user{id_user}.png"
    # fig.write_html("output.html", auto_open=True)
    fig.write_image(filename)

    print(f"✅ Image enregistrée avec succès à : {filename}")
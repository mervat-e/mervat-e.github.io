import json
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path
from detoxify import Detoxify
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from sentence_transformers import SentenceTransformer, util
import os

path = "backend/resources/tiktok_video/tiktok_metadata.json"

data = None 

with open(path, "r", encoding="utf-8") as f:

    data = json.load(f)

def get_popular_users_simple_matching():

    result = []
    colors = []
    account_names = []
    likes_list = []

    for user_url, user_data in data["account_metadata"].items():

        if user_data is None:

            continue  

        account_name = user_data.get("account_name", "")
        bio = user_data.get("biography", "")
        likes = user_data.get("total_likes", 0)

        result.append({
            "account_name": account_name,
            "biography": bio,
            "total_likes": likes
        })

    result_sorted = sorted(result, key=lambda x: x["total_likes"], reverse=True)

    top_20 = result_sorted[:20]

    for i in top_20:

        print(f"---------- Analyse compte {i['account_name']} -------------")

        account_names.append(i["account_name"])

        likes_list.append(i["total_likes"])

        biography_text = i["biography"]

        model = SentenceTransformer('all-MiniLM-L6-v2')

        keywords = [
        "anorexia",
        "bulimia",
        "fasting",
        "thinspo",
        "purge",
        "body checking",
        "calories",
        "weight loss",
        "skinny",
        "body image",
        "diet",
        "mirror",
        "perfect body",
        "fat",
        "beauty standards"
        ]

        embedding1 = model.encode(biography_text, convert_to_tensor=True)
        embedding2 = model.encode(keywords, convert_to_tensor=True)

        scores = util.cos_sim(embedding1, embedding2)

        print(f"SCORE : {scores}")

        if any(score.item() > 0.5 for score in scores[0]):

            colors.append('red')  # Dangereux
        else:
            colors.append('skyblue')  # Sain

        print(f"\n--- Analyse du compte : {i['account_name']} ---")

        for word, score in zip(keywords, scores[0]):

            print(f"{word} → score de similarité : {score.item():.3f}")

    # Tracer le graphique
    plt.figure(figsize=(15, 8))
    plt.bar(account_names, likes, color=colors)
    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Tiktok Users")
    plt.ylabel("Popularity (likes)")
    plt.title("Top 10 Utilisteurs Tiktok du moment (rouge = potentiellement dangereux)")
    plt.tight_layout()
    plt.show()



def get_popular_users_by_bio():

    result = []
    colors = []
    account_names = []
    likes_list = []
    categories = []
    danger_flags = []

    model = SentenceTransformer('all-MiniLM-L6-v2')

    for user_url, user_data in data["account_metadata"].items():

        if user_data is None:
            continue  

        account_name = user_data.get("account_name", "")
        bio = user_data.get("biography", "")
        likes = user_data.get("total_likes", 0)

        result.append({
            "account_name": account_name,
            "biography": bio,
            "total_likes": likes
        })

    result_sorted = sorted(result, key=lambda x: x["total_likes"], reverse=True)
    top_20 = result_sorted[:20]

    community_keywords = {
        "Makeup": ["makeup", "contouring", "nose", "cover", "skin problems", "foundation"],
        "Sport": ["gym", "abs", "lift", "workout"],
        "Food": ["calories", "carbs", "diet", "healthy", "clean eating", "keto", "fasting"],
        "Fashion": ["fashion", "clothes", "style", "fit"]
    }

    problem_keywords = {

        "ED": ["anorexia", "bulimia", "purge", "noeat"],
        "BodyImage": ["skinny", "thin", "weight loss", "fat", "body checking", "beauty standards"]
    }

    for i in top_20:

        print(f"\n---------- Analyse compte {i['account_name']} -------------")

        account_names.append(i["account_name"])
        likes_list.append(i["total_likes"])
        biography_text = i["biography"]

        embedding_bio = model.encode(biography_text, convert_to_tensor=True)

        max_score = -1
        best_category = "Other"
        threshold = 0.25  # threshold score to classify a user in a community

        for cat_name, keywords in community_keywords.items():
            emb_keywords = model.encode(keywords, convert_to_tensor=True)
            scores = util.cos_sim(embedding_bio, emb_keywords)

            print(f"\n🔍 Catégorie : {cat_name}")
            for idx, (keyword, score) in enumerate(zip(keywords, scores[0])):
                print(f"  - '{keyword}' (index {idx}) → Similarité : {score.item():.4f}")
            
            score_max = scores[0].max().item() # we the single word that has the highest score among the list of keywords 

            print(f"{cat_name} → score max : {score_max:.3f}")

            if score_max > max_score:
                max_score = score_max
                best_category = cat_name

        if max_score < threshold:
            best_category = "Other"

        categories.append(best_category)

        is_dangerous = False

        for label, keywords in problem_keywords.items():
            emb_keywords = model.encode(keywords, convert_to_tensor=True)
            scores = util.cos_sim(embedding_bio, emb_keywords)

            if any(score.item() > 0.5 for score in scores[0]):
                is_dangerous = True
                print(f"Problème détecté ({label})")

        danger_flags.append(is_dangerous)

        print(f"Catégorie assignée : {best_category} | Dangereux : {is_dangerous}")

        color_map = {
            "Makeup": "violet",
            "Sport": "green",
            "Food": "orange",
            "Fashion": "blue",
            "Other": "gray"
        }

        # Si dangereux, ajouter une couleur foncée ou un contour spécial
        if is_dangerous:
            colors.append("red")
        else:
            colors.append(color_map.get(best_category, "gray"))

    plt.figure(figsize=(15, 8))
    bars = plt.bar(account_names, likes_list, color=colors)

    for idx, (bar, danger) in enumerate(zip(bars, danger_flags)):
        if danger:
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5000, '⚠️', ha='center', fontsize=14)

    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Tiktok Users")
    plt.ylabel("Popularity (likes)")
    plt.title("Top 20 Utilisateurs TikTok (par catégorie et dangerosité)")
    plt.tight_layout()
    plt.show()
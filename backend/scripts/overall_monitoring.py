import json
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path
from detoxify import Detoxify
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer, util
import os
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D 

model = SentenceTransformer('all-MiniLM-L6-v2')

trends_alert = []

influencers_alert = []

path = "backend/resources/tiktok_video/tiktok_metadata.json"

data = None 

with open(path, "r", encoding="utf-8") as f:

    data = json.load(f)


def hashtags_to_likes(data):

    result = {}

    for video_url, video_data in data["metadata"].items():

        if video_data is None:
            continue  

        hashtags = video_data.get("hashtags", [])
        likes = video_data.get("likes", 0)

        for tag in hashtags:
            tag = tag.lower()
            result[tag] = result.get(tag, 0) + likes

    sorted_result = dict(sorted(result.items(), key=lambda item: item[1], reverse=True))

    return sorted_result


def get_popular_trends():

    res = hashtags_to_likes(data)

    # put the unrelevant hashtags here

    excluded_hashtags = {
        "fyp", "foryou", "foryoupage", "viral", "trending", "edit",
        "fy", "real", "trend", "xyzbca", "fypppppp", "viralvideos", "fypage", "relatable",
        "capcut", "foru"
    }

    def is_generic(tag):
        tag = tag.lower()
        if tag in excluded_hashtags:
            return True
        if len(tag) <= 3:
            return True
        if any(sub in tag for sub in ["fyp", "fy", "viral", "trend", "xyz"]):
            return True
        return False
    
    filtered_res = {tag: score for tag, score in res.items() if not is_generic(tag)}


    for tag, score in filtered_res.items():

        print("Hashtag :", tag, "| Score :", score)

    top_20 = list(filtered_res.items())[:20]
    hashtags = [tag for tag, _ in top_20]
    likes = [score for _, score in top_20]

    colors = []

    for hash in hashtags:

        # --------- TEST AVEC DETOXIFY ------------

        '''toxicity_analysis = Detoxify('original').predict(hash)

        print(f"Hashtag : {hash}, predict : {toxicity_analysis}")

        colors = []
        for tag in hashtags:
            if toxicity_scores['toxicity'][hashtags.index(tag)] > 0.5:
                colors.append('red')  # Dangereux
            else:
                colors.append('skyblue')  # Sain

        # Tracer le bar chart
        plt.figure(figsize=(15, 8))
        plt.bar(hashtags, likes, color=colors)
        plt.xticks(rotation=45, ha='right')
        plt.xlabel("Hashtags")
        plt.ylabel("Likes")
        plt.title("Top 30 hashtags TikTok (rouge = toxique)")
        plt.tight_layout()
        plt.show()
        
        
        '''

        # ----------- TEST AVEC BERT HATE SPEECH ----------

        '''tokenizer = AutoTokenizer.from_pretrained("Hate-speech-CNERG/bert-base-uncased-hatexplain")
        model = AutoModelForSequenceClassification.from_pretrained("Hate-speech-CNERG/bert-base-uncased-hatexplain")

        inputs = tokenizer(hash, return_tensors="pt", truncation=True)
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)  # [non-hate, hate, offensive]

        hate_prob = probs[0][1]
        print(f"{hash} scores : {hate_prob}") '''


        # ----------- TEST AVEC ALL MINI LLM SENTENCE TRANSFORMER (comparaison sémantique) ------------ 


    

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

        embedding1 = model.encode(hash, convert_to_tensor=True)
        embedding2 = model.encode(keywords, convert_to_tensor=True)

        scores = util.cos_sim(embedding1, embedding2)

        is_harmful = False
        trigger_keywords = []

        for word, score in zip(keywords, scores[0]):
            if score.item() > 0.45:
                is_harmful = True
                trigger_keywords.append(word)

        if is_harmful:
            colors.append('indianred')  # Dangereux
            trends_alert.extend(trigger_keywords)  # Ajout des mots déclencheurs
        else:
            colors.append('slateblue')  # Sain

        print(f"\n--- Analyse du hashtag : {hash} ---")

        for word, score in zip(keywords, scores[0]):

            print(f"{word} → score de similarité : {score.item():.3f}")

     # Création du dossier de sauvegarde s'il n'existe pas

    output_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "frontend", "static", "img")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "popular_trends.png")

        
    # Visualisation 
    plt.figure(figsize=(15, 8))
    plt.bar(hashtags, likes, color=colors)
    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Trends")
    plt.ylabel("Likes")
    plt.title("Top 20 Tiktok trends")

    for i, (hashtag, like, color) in enumerate(zip(hashtags, likes, colors)):
        if color == 'indianred':
            plt.text(i, like + max(likes)*0.02, "⚠️", ha='center', va='bottom', fontsize=14)

    safe_patch = mpatches.Patch(color='slateblue', label='Not harmful')
    harmful_patch = mpatches.Patch(color='indianred', label='Potentially harmful')
    plt.legend(handles=[safe_patch, harmful_patch], loc="upper right")


    plt.tight_layout()

    # Enregistrement
    plt.savefig(output_path, dpi=300)

    print(f"Graphique enregistré dans : {output_path}")

    print("\n🔍 Mots-clés déclencheurs identifiés :")
    print(set(trends_alert)) 

    plt.show()



def get_communities_by_popular_content():


    result = []
    colors = []
    account_names = []
    likes_list = []
    categories = []
    danger_flags = []

    best_videos_by_author = {}

 

    # Sorting a subset of the most liked content atm

    for user_url, user_data in data["metadata"].items():

        if user_data is None:
            continue  

        author = user_data.get("author", "")
        description = user_data.get("description", "")
        likes = user_data.get("likes", 0)

        if likes is None:
            likes = 0


        # Si auteur déjà présent, garder la vidéo avec le plus de likes
        if author in best_videos_by_author:
            if likes > best_videos_by_author[author]["likes"]:
                best_videos_by_author[author] = {
                    "author": author,
                    "description": description,
                    "likes": likes
                }
        else:
            best_videos_by_author[author] = {
                "author": author,
                "description": description,
                "likes": likes
            }

    result = list(best_videos_by_author.values())

    result_sorted = sorted(result, key=lambda x: x["likes"], reverse=True)
    top_20 = result_sorted[:20]

    # Define the matching keywords by communities

    community_keywords = {
        "Makeup": ["makeup", "contouring", "nose", "cover", "skin problems", "foundation", "makeup product"],
        "Sport": ["gym", "abs", "lift", "workout", "sport", "fit"],
        "Food": ["recipe", "food", "ingredient", "yummy", "foodie"],
        "Fashion": ["fashion", "clothes", "style", "fit"]
    }

    problem_keywords = {

        "ED": ["anorexia", "bulimia", "purge", "noeat"],
        "BodyImage": ["skinny", "thin", "weight loss", "fat", "body checking", "beauty standards"],
        "FearFood": ["calories", "carbs", "diet", "healthy", "clean eating", "keto", "fasting"]
    }

    for i in top_20:

        print(f"\n---------- Analyse compte {i['author']} -------------")

        account_names.append(i["author"])
        likes_list.append(i["likes"])
        description_text = i["description"]

        print(f"\n Description à analyser : {description_text}")

        embedding_bio = model.encode(description_text, convert_to_tensor=True)

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

            print(f"\n🔍 Catégorie potentiellement dangereuse  : {label}")
            for idx, (keyword, score) in enumerate(zip(keywords, scores[0])):
                print(f"  - '{keyword}' (index {idx}) → Similarité : {score.item():.4f}")

            if score.item() > 0.3:  # *** seuil danger
                    is_dangerous = True
                    # *** stocker le mot problematic s’il n’est pas déjà dans la liste
                    if keyword not in influencers_alert:
                        influencers_alert.append(keyword)
                    print(f"Problème détecté ({label}): {keyword}")

        danger_flags.append(is_dangerous)

        print(f"Catégorie assignée : {best_category} | Dangereux : {is_dangerous}")

        color_map = {
            "Makeup": "palevioletred",
            "Sport": "mediumpurple",
            "Food": "lightskyblue",
            "Fashion": "mediumaquamarine",
            "Other": "tan"
        }
        colors.append(color_map.get(best_category, "gray"))

         # 🔧 Création du dossier de sauvegarde s'il n'existe pas
    output_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "frontend", "static", "img")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "popular_influencers_communities.png")

    plt.figure(figsize=(15, 8))
    bars = plt.bar(account_names, likes_list, color=colors)

    for idx, (bar, danger) in enumerate(zip(bars, danger_flags)):
        if danger:
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(likes_list) * 0.02,  # Placement dynamique
                '⚠️',
                ha='center',
                va='bottom',
                fontsize=14
            )

    plt.xticks(rotation=45, ha='right')
    plt.xlabel("Tiktok Users")
    plt.ylabel("Popularity")
    plt.title("Top 20 TikTok Influencers")
    plt.tight_layout()

    legend_elements = [
    Patch(facecolor='palevioletred', edgecolor='black', label='Makeup'),
    Patch(facecolor='mediumpurple', edgecolor='black', label='Sport'),
    Patch(facecolor='lightskyblue', edgecolor='black', label='Food'),
    Patch(facecolor='mediumaquamarine', edgecolor='black', label='Fashion'),
    Patch(facecolor='tan', edgecolor='black', label='Other'),
    Line2D([0], [0], marker='o', color='w', label='⚠️ : Potentially harmful content',
           markerfacecolor='none', markersize=12)
    ]

    plt.legend(handles=legend_elements, loc='upper right')

    print("\nMots potentiellement harmful détectés :", influencers_alert)


     # Enregistrement
    plt.savefig(output_path, dpi=300)
    print(f"Graphique enregistré dans : {output_path}")

    plt.show()

if __name__ == "__main__":
    get_popular_trends()
    get_communities_by_popular_content()

    # Enregistrement des alertes
    alert_path = os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
        "frontend", "static", "alerts.json"
    )

    # Écraser les alertes existantes avec les nouvelles (sans fusion)
    new_alerts = {
        "trends_alert": list(set(trends_alert)),
        "influencers_alert": list(set(influencers_alert))
    }

    # Ajouter les éventuelles alertes de fréquence (si présentes dans le fichier existant)
    alerts_path = os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
        "frontend", "static", "alerts.json"
    )

    # Si le fichier existe, conserver uniquement les alerts.frequency_alerts si tu veux les garder
    if os.path.exists(alerts_path):
        with open(alerts_path, "r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
                if "frequency_alerts" in existing:
                    new_alerts["frequency_alerts"] = existing["frequency_alerts"]
            except json.JSONDecodeError:
                pass

    # Sauvegarder
    with open(alerts_path, "w", encoding="utf-8") as f:
        json.dump(new_alerts, f, indent=2, ensure_ascii=False)

    print(f"✅ Fichier d'alertes écrasé avec succès : {alert_path}")




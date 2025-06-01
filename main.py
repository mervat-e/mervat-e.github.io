from flask import Flask, render_template, url_for
import json
import os
import subprocess

app = Flask(__name__)

# Répertoire de base du frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mots-clés problématiques liés aux TCA
TCA_KEYWORDS = [
    "anorexie", "anorexia", "boulimie", "bulimia", "tca", "eating disorder", "trouble alimentaire",
    "skinny", "maigre", "mince", "mincir", "maigrir", "corps parfait", "objectif poids", "objectif minceur",
    "poids idéal", "corps de rêve", "ventre plat", "thigh gap", "flat stomach", "zero fat", "collarbones",
    "ribs", "bones", "visible ribs", "skinny waist", "skinny arms",
    "régime", "calorie", "calories", "0 calories", "zero calorie", "low carb", "low fat", "no carbs", "sans sucre",
    "fasting", "intermittent fasting", "jeûne", "jeûner", "starvation", "meal skipping", "skip meals", "no eating",
    "rien manger", "ne pas manger",
    "vomir", "vomissement", "purge", "laxatif", "laxatifs", "diurétique", "diurétiques", "surentraînement", "exercise excessif",
    "proana", "pro-ana", "promia", "pro-mia", "ana tips", "ana tricks", "ana goals", "ana buddy",
    "thinspiration", "thinspo", "fitspiration", "bonespo", "fitspo",
    "body check", "trigger warning", "feel fat", "je me sens grosse", "je me sens trop gros",
    "détestation de soi", "perte de poids rapide", "challenge poids", "dégout de nourriture"
]


@app.route("/")
def index():
    user_data_path = os.path.join(BASE_DIR, "..", "backend", "resources", "user_info", "user_data.json")
        # Chargement des données utilisateur
    with open(user_data_path, encoding="utf-8") as f:
        data = json.load(f)
        user1 = data["users"][0]
        user2 = data["users"][1]
    return render_template("index.html",user1=user1, user2=user2)

@app.route("/profile1")
def profile():
    # Chemins vers les fichiers JSON
    user_data_path = os.path.join(BASE_DIR, "..", "backend", "resources", "user_info", "user_data.json")
    tiktok_data_path = os.path.join(BASE_DIR, "..", "backend", "resources", "tiktok_video", "tiktok_metadata.json")

    # 1. Analyse des contenus (graphe, hashtags)
    analyse_script_path = os.path.join(BASE_DIR, "scripts", "analyse_health_content.py")
    try:
        subprocess.run(["python", analyse_script_path], check=True)
    except subprocess.CalledProcessError as e:
        print("❌ Erreur dans analyse_health_content.py :", e)

    # 2. Analyse des alertes (trends, influenceurs)
    monitoring_script_path = os.path.join(BASE_DIR, "scripts", "overall_monitoring.py")
    try:
        subprocess.run(["python", monitoring_script_path], check=True)
    except subprocess.CalledProcessError as e:
        print("❌ Erreur dans overall_monitoring.py :", e)


    # Chargement des données utilisateur
    with open(user_data_path, encoding="utf-8") as f:
        data = json.load(f)
        user = data["users"][-1]

    # Chargement des métadonnées TikTok
    with open(tiktok_data_path, encoding="utf-8") as f:
        tiktok_data = json.load(f)

    # Filtrer les descriptions valides
    all_descriptions = [
        video.get("description", "").lower()
        for video in tiktok_data.get("metadata", {}).values()
        if isinstance(video, dict)
    ]
    total = len(all_descriptions)

    # Recherche des mots problématiques
    found = []
    for desc in all_descriptions:
        for word in TCA_KEYWORDS:
            if word in desc and word not in found:
                found.append(word)

                

        # Charger les alertes enregistrées
    alerts_path = os.path.join(BASE_DIR, "static", "alerts.json")
    trends_alert = []
    influencers_alert = []
    frequency_alerts = []

    if os.path.exists(alerts_path):
        with open(alerts_path, encoding="utf-8") as f:
            alert_data = json.load(f)
            trends_alert = alert_data.get("trends_alert", [])
            influencers_alert = alert_data.get("influencers_alert", [])
            frequency_alerts = alert_data.get("frequency_alerts", [])

    return render_template("profile_2.html", 
        user=user, 
        result={
            "total": total,
            "problematic_count": len(found),
            "found": found,
            "alert": len(found) > 0
        },
        images={
            "hashtags": url_for('static', filename='img/hashtags_barplot.png'),
            "graph": url_for('static', filename='img/category_graph.png'),
            "trends": url_for('static', filename='img/popular_trends.png'),
            "influencers": url_for('static', filename='img/popular_influencers_communities.png'),
        },
        alerts={
            "terms": found,
            "trends": trends_alert,
            "influencers": influencers_alert,
            "frequencies": frequency_alerts
        }
    )

@app.route("/profile2")
def profile_2():
    # Chemins vers les fichiers JSON
    user_data_path = os.path.join(BASE_DIR, "..", "backend", "resources", "user_info", "user_data.json")
    tiktok_data_path = os.path.join(BASE_DIR, "..", "backend", "resources", "tiktok_video", "tiktok_metadata.json")

    # 1. Analyse des contenus (graphe, hashtags)
    analyse_script_path = os.path.join(BASE_DIR, "scripts", "analyse_health_content.py")
    try:
        subprocess.run(["python", analyse_script_path], check=True)
    except subprocess.CalledProcessError as e:
        print("❌ Erreur dans analyse_health_content.py :", e)

    # 2. Analyse des alertes (trends, influenceurs)
    monitoring_script_path = os.path.join(BASE_DIR, "scripts", "overall_monitoring.py")
    try:
        subprocess.run(["python", monitoring_script_path], check=True)
    except subprocess.CalledProcessError as e:
        print("❌ Erreur dans overall_monitoring.py :", e)


    # Chargement des données utilisateur
    with open(user_data_path, encoding="utf-8") as f:
        data = json.load(f)
        user = data["users"][0]

    # Chargement des métadonnées TikTok
    with open(tiktok_data_path, encoding="utf-8") as f:
        tiktok_data = json.load(f)

    # Filtrer les descriptions valides
    all_descriptions = [
        video.get("description", "").lower()
        for video in tiktok_data.get("metadata", {}).values()
        if isinstance(video, dict)
    ]
    total = len(all_descriptions)

    # Recherche des mots problématiques
    found = []
    for desc in all_descriptions:
        for word in TCA_KEYWORDS:
            if word in desc and word not in found:
                found.append(word)

                

        # Charger les alertes enregistrées
    alerts_path = os.path.join(BASE_DIR, "static", "alerts.json")
    trends_alert = []
    influencers_alert = []
    frequency_alerts = []

    if os.path.exists(alerts_path):
        with open(alerts_path, encoding="utf-8") as f:
            alert_data = json.load(f)
            trends_alert = alert_data.get("trends_alert", [])
            influencers_alert = alert_data.get("influencers_alert", [])
            frequency_alerts = alert_data.get("frequency_alerts", [])

    return render_template("profile.html", 
        user=user, 
        result={
            "total": total,
            "problematic_count": len(found),
            "found": found,
            "alert": len(found) > 0
        },
        images={
            "hashtags": url_for('static', filename='img/hashtags_barplot.png'),
            "graph": url_for('static', filename='img/category_graph.png'),
            "trends": url_for('static', filename='img/popular_trends.png'),
            "influencers": url_for('static', filename='img/popular_influencers_communities.png'),
        },
        alerts={
            "terms": found,
            "trends": trends_alert,
            "influencers": influencers_alert,
            "frequencies": frequency_alerts
        }
    )


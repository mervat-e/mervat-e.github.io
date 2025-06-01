import json

TCA_KEYWORDS = [
    # Général
    "anorexie", "anorexia", "boulimie", "bulimia", "tca", "eating disorder", "trouble alimentaire",

    # Idéaux corporels
    "skinny", "maigre", "mince", "mincir", "maigrir", "corps parfait", "objectif poids", "objectif minceur",
    "poids idéal", "corps de rêve", "ventre plat", "thigh gap", "flat stomach", "zero fat", "collarbones",
    "ribs", "bones", "visible ribs", "skinny waist", "skinny arms",

    # Régimes et comportements extrêmes
    "régime", "calorie", "calories", "0 calories", "zero calorie", "low carb", "low fat", "no carbs", "sans sucre",
    "fasting", "intermittent fasting", "jeûne", "jeûner", "starvation", "meal skipping", "skip meals", "no eating",
    "rien manger", "ne pas manger",

    # Comportements compensatoires
    "vomir", "vomissement", "purge", "laxatif", "laxatifs", "diurétique", "diurétiques", "surentraînement", "exercise excessif",

    # Contenus pro-TCA
    "proana", "pro-ana", "promia", "pro-mia", "ana tips", "ana tricks", "ana goals", "ana buddy",
    "thinspiration", "thinspo", "fitspiration", "bonespo", "fitspo",

    # Autres
    "body check", "trigger warning", "feel fat", "je me sens grosse", "je me sens trop gros",
    "détestation de soi", "perte de poids rapide", "challenge poids", "dégout de nourriture"
]


def analyze_tiktok_descriptions(filepath: str):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"error": str(e)}

    metadata = data.get("metadata", {})
    problematic = []

    for link, video in metadata.items():
        description = video.get("description", "").lower()
        if any(term in description for term in TCA_KEYWORDS):
            problematic.append({
                "link": link,
                "description": video.get("description", ""),
                "matched_terms": [t for t in TCA_KEYWORDS if t in description]
            })

    return {
        "total": len(metadata),
        "problematic": len(problematic),
        "alert": len(problematic) > 0,
        "videos": problematic
    }

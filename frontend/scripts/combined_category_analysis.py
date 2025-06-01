# File: frontend/scripts/combined_category_analysis.py (Modified Sections)

import json
import os
import re
from collections import defaultdict, Counter

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import spacy
import matplotlib.cm as cm

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# — CONFIGURATION —
METADATA_PATH = "backend/resources/tiktok_video/tiktok_metadata.json"
NUM_AUTO_CLUSTERS = 30 # Number of auto clusters
SIM_THRESHOLD = 0.40  # spaCy cosine similarity threshold for edges (can be adjusted)

# List of hashtags to ignore during auto-clustering
IGNORE_HASHTAGS = {
    "lg", "fy", "tiktok", "foryou", "ai", "ia", "sprei", "line",
    "fyp", "viral", "explore", "trending", "duet", "stitch", "challenge",
    "live", # Added 'live' based on your example output
    "pourtoi", "fürdich", # Add common variants if needed
    "comedy", "funny", "dance", "music", "art", "beautyhacks", # Add other general tags if desired
    "cat", "dog", "puppy", "gsd", # Add specific animal tags if they clutter results
    "paris", "lyon", "swiss", "france", "neuchatel", # Add location tags if they are not relevant content categories
    "cartok", # Specific niche tag you might want to exclude
    "miam", # Specific niche tag
    "bayram", # Specific event/cultural tag
    "amadou" # Seems like a specific name
}


# Manually Defined Categories (from your first file)
EMOTION_CATS_KEYWORDS = {
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

HEALTH_CATS_KEYWORDS = {
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

MANUAL_CATS = {**EMOTION_CATS_KEYWORDS, **HEALTH_CATS_KEYWORDS}
MANUAL_CAT_NAMES = list(MANUAL_CATS.keys())

# — STEP 1: LOAD METADATA —
def load_metadata(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metadata not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("metadata", {})

# — STEP 2: CLASSIFY AND SEPARATE HASHTAGS —
# Modified to also filter ignored hashtags
def classify_and_separate_hashtags(metadata, manual_cats_keywords, ignore_hashtags):
    manual_cat_counts = Counter()
    unclassified_hashtags = Counter()
    tag_to_manual_cat = {}

    for entry in metadata.values():
        if not isinstance(entry, dict):
            print("⚠️ Entrée ignorée (type invalide):", entry)
            continue

        for tag in entry.get("hashtags", []):
            clean_tag = tag.lower().strip("#")

            if clean_tag in ignore_hashtags:
                continue

            classified = False
            for cat, keywords in manual_cats_keywords.items():
                if any(re.search(rf"\b{re.escape(w)}\b", clean_tag) for w in keywords):
                    manual_cat_counts[cat] += 1
                    tag_to_manual_cat[clean_tag] = cat
                    classified = True
                    break

            if not classified:
                unclassified_hashtags[clean_tag] += 1


    return manual_cat_counts, unclassified_hashtags, tag_to_manual_cat

# — STEP 3: CLUSTER UNCLASSIFIED HASHTAGS —
def cluster_unclassified_hashtags(unclassified_hashtags_counter, n_clusters):
    if not unclassified_hashtags_counter:
        return {}, {}

    unclassified_tags_list = list(unclassified_hashtags_counter.keys())

    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2,4))
    X = vec.fit_transform(unclassified_tags_list)

    # ensure n_clusters ≤ n_samples
    k = min(n_clusters, X.shape[0])
    if k == 0: # Handle case where there are no unclassified tags after filtering
         print("Warning: No unclassified hashtags remaining after filtering and manual classification. Skipping auto-clustering.")
         return {}, {}
    if k < n_clusters:
         print(f"Warning: Number of unique unclassified hashtags ({X.shape[0]}) is less than requested clusters ({n_clusters}). Clustering into {k} groups.")


    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)

    # group tags by cluster, pick representative
    auto_clusters = defaultdict(list)
    for tag, lab in zip(unclassified_tags_list, labels):
        auto_clusters[lab].append(tag)

    # pick the shortest tag as label for clarity
    auto_cluster_names_map = {lab: min(tags, key=len) for lab, tags in auto_clusters.items()}

    # Aggregate counts for auto clusters AND create the final category names with prefix
    auto_cat_counts = Counter()
    tag_to_auto_cluster_prefixed = {}

    for lab, representative_tag in auto_cluster_names_map.items():
        prefixed_cat_name = f"Auto_{representative_tag}"
        for tag_in_cluster in auto_clusters[lab]:
             auto_cat_counts[prefixed_cat_name] += unclassified_hashtags_counter[tag_in_cluster]
             tag_to_auto_cluster_prefixed[tag_in_cluster] = prefixed_cat_name


    return auto_cat_counts, tag_to_auto_cluster_prefixed

# — STEP 4: COMBINE CATEGORIES AND COUNTS —
def combine_categories(manual_cat_counts, auto_cat_counts):
    total_cat_counts = manual_cat_counts + auto_cat_counts
    all_categories = list(total_cat_counts.keys())
    return all_categories, total_cat_counts

# — STEP 5: BUILD & DRAW SEMANTIC GRAPH —
def visualize_combined_graph(all_categories, total_cat_counts, emotion_cat_names, health_cat_names, sim_threshold): # Removed manual_cat_names as it's redundant with emotion/health
    # load spaCy large model
    try:
        nlp = spacy.load("en_core_web_lg")
    except OSError:
        print("Downloading spaCy model 'en_core_web_lg'...")
        spacy.cli.download("en_core_web_lg")
        nlp = spacy.load("en_core_web_lg")


    # Prepare category vectors - handle the "Auto_" prefix
    cat_vectors = {}
    for cat in all_categories:
        clean_cat_name = cat.replace("Auto_", "") # Remove prefix for spaCy
        # Process the text and get the vector
        doc = nlp(clean_cat_name)
        if doc.has_vector:
             cat_vectors[cat] = doc.vector
        else:
             print(f"Warning: Category '{cat}' ({clean_cat_name}) does not have a vector. Skipping for similarity calculation.")
             # Use a small non-zero vector or handle this case explicitly if needed
             # Using a zero vector might cause division by zero if not careful
             # Let's use a vector of NaNs to indicate no valid vector
             cat_vectors[cat] = np.full(nlp.vocab.vectors.shape[1], np.nan)


    # build graph
    G = nx.Graph()
    for cat in all_categories:
        cnt = total_cat_counts.get(cat, 0)
        # Scale node sizes more aggressively and add a minimum size
        size = np.log1p(cnt) * 500 + 200
        G.add_node(cat, size=size)

    # edges by spaCy cosine similarity - only between categories that have valid vectors
    valid_categories = [cat for cat in all_categories if not np.isnan(cat_vectors[cat]).all()]

    for i, c1 in enumerate(valid_categories):
        for c2 in valid_categories[i+1:]:
            v1, v2 = cat_vectors[c1], cat_vectors[c2]
            # Calculate cosine similarity safely
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            if norm_v1 > 0 and norm_v2 > 0:
                 sim = np.dot(v1, v2) / (norm_v1 * norm_v2)
                 if sim >= sim_threshold:
                     G.add_edge(c1, c2, weight=sim)


    plt.figure(figsize=(14, 10))

    # Use spring layout to position nodes based on the (hidden) edges
    pos = nx.spring_layout(G, k=0.8, iterations=200, seed=42)

    sizes = [G.nodes[n]["size"] for n in G.nodes()]

    # Assign colors based on category type (Emotion, Health, Auto-clustered)
    node_colors = []
    for node in G.nodes():
        if node in emotion_cat_names:
            node_colors.append('coral') # Emotion color
        elif node in health_cat_names:
            node_colors.append('lightseagreen') # Health color
        else:
            node_colors.append('lightgray') # Auto-clustered color


    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color=node_colors, alpha=0.9)

    # Draw labels
    # Create a dictionary with cleaned labels
    cleaned_labels = {node: node.replace("Auto_", "") for node in G.nodes()}

    # Draw labels using the cleaned names
    nx.draw_networkx_labels(G, pos, labels=cleaned_labels, font_size=10, font_weight="bold", font_color="black")


    plt.title("Combined Content Categories (Manual & Auto-clustered)", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

# — MAIN EXECUTION —
if __name__ == "__main__":
    meta = load_metadata(METADATA_PATH)

    # Step 2: Classify and separate hashtags, also filtering ignored ones
    manual_cat_counts, unclassified_hashtags_counter, tag_to_manual_cat = classify_and_separate_hashtags(meta, MANUAL_CATS, IGNORE_HASHTAGS)
    print("\n--- Manual Category Counts ---")
    for cat, count in manual_cat_counts.most_common():
        print(f"{cat}: {count}")

    # Step 3: Cluster unclassified hashtags (after filtering)
    auto_cat_counts, tag_to_auto_cluster_prefixed = cluster_unclassified_hashtags(unclassified_hashtags_counter, NUM_AUTO_CLUSTERS)
    print("\n--- Auto-clustered Category Counts ---")
    for cat, count in auto_cat_counts.most_common():
        print(f"{cat}: {count}")

    # Step 4: Combine categories and counts
    all_categories, total_cat_counts = combine_categories(manual_cat_counts, auto_cat_counts)
    print(f"\nTotal unique categories (manual + auto): {len(all_categories)}")

    # Step 5: Visualize the combined graph
    visualize_combined_graph(
        all_categories,
        total_cat_counts,
        list(EMOTION_CATS_KEYWORDS.keys()), # Pass lists of names
        list(HEALTH_CATS_KEYWORDS.keys()),
        SIM_THRESHOLD
    )
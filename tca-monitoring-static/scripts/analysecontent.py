# File: frontend/scripts/analysecontent.py

import json
import os
from collections import defaultdict, Counter

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import spacy

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# — CONFIGURATION — 
METADATA_PATH = "backend/resources/tiktok_video/tiktok_metadata.json"
NUM_CLUSTERS = 40
SIM_THRESHOLD = 0.40  # spaCy cosine similarity threshold for edges

# — STEP 1: LOAD METADATA — 
def load_metadata(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Metadata not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return payload.get("metadata", {})

# — STEP 2: EXTRACT UNIQUE HASHTAGS & COUNTS — 
def extract_hashtags(metadata):
    tag_counts = Counter()
    for entry in metadata.values():
        if not isinstance(entry, dict):
            print("⚠️ Entrée ignorée (type invalide):", entry)
            continue
        for tag in entry.get("hashtags", []):
            clean = tag.lower().strip("#")
            tag_counts[clean] += 1
    hashtags = list(tag_counts.keys())
    return hashtags, tag_counts


# — STEP 3: CLUSTER HASHTAGS INTO 40 GROUPS — 
def cluster_hashtags(hashtags, n_clusters):
    # TF-IDF on character n-grams → better handles short tags
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2,4))
    X = vec.fit_transform(hashtags)

    # ensure n_clusters ≤ n_samples
    k = min(n_clusters, X.shape[0])
    km = KMeans(n_clusters=k, random_state=42)
    labels = km.fit_predict(X)

    # group tags by cluster, pick representative
    clusters = defaultdict(list)
    for tag, lab in zip(hashtags, labels):
        clusters[lab].append(tag)

    # pick the shortest tag as label for clarity
    cluster_names = {lab: min(tags, key=len) for lab, tags in clusters.items()}
    tag_to_cluster = {tag: cluster_names[lab] for lab, tags in clusters.items() for tag in tags}

    return cluster_names, tag_to_cluster

# — STEP 4: AGGREGATE COUNTS INTO CLUSTERS — 
def aggregate_counts(tag_to_cluster, tag_counts):
    cat_counts = Counter()
    for tag, cnt in tag_counts.items():
        cat = tag_to_cluster[tag]
        cat_counts[cat] += cnt
    return cat_counts

# — STEP 5: BUILD & DRAW SEMANTIC GRAPH — 
def visualize_semantic_graph(cat_counts, cluster_names, sim_threshold):
    # load spaCy large model
    nlp = spacy.load("en_core_web_lg")

    # prepare category vectors
    cats = list(cluster_names.values())
    vecs = {cat: nlp(cat).vector for cat in cats}

    # build graph
    G = nx.Graph()
    for cat in cats:
        cnt = cat_counts.get(cat, 0)
        size = 100 + np.sqrt(cnt) * 50  # gentle scaling
        G.add_node(cat, size=size)

    # edges by spaCy cosine similarity
    for i, c1 in enumerate(cats):
        for c2 in cats[i+1:]:
            v1, v2 = vecs[c1], vecs[c2]
            sim = np.dot(v1, v2) / (np.linalg.norm(v1)*np.linalg.norm(v2))
            if sim >= sim_threshold:
                G.add_edge(c1, c2, weight=sim)

    # layout and draw
    plt.figure(figsize=(14,10))
    pos = nx.spring_layout(G, seed=42, k=1.0)

    sizes = [G.nodes[n]["size"] for n in G.nodes()]
    cmap = plt.cm.tab20
    colors = [cmap(i % cmap.N) for i, _ in enumerate(G.nodes())]

    edges = G.edges(data=True)
    widths = [d["weight"]*2 for (_,_,d) in edges]

    nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color=colors, alpha=0.8)
    nx.draw_networkx_edges(G, pos, width=widths, alpha=0.4, edge_color="gray")
    nx.draw_networkx_labels(G, pos, font_size=9)

    plt.title(f"Content Categories (spaCy links, thresh={sim_threshold})")
    plt.axis("off")
    plt.tight_layout()
    plt.show()

# — MAIN — 
if __name__ == "__main__":
    meta = load_metadata(METADATA_PATH)
    hashtags, tag_counts = extract_hashtags(meta)
    cluster_names, tag_to_cluster = cluster_hashtags(hashtags, NUM_CLUSTERS)
    cat_counts = aggregate_counts(tag_to_cluster, tag_counts)
    visualize_semantic_graph(cat_counts, cluster_names, SIM_THRESHOLD)

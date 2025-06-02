import json
import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer, util
from keybert import KeyBERT
from collections import defaultdict

with open("data/input_products.json", "r", encoding="utf-8") as f:
    products = json.load(f)

with open("stopwords/stopwords_de.txt", "r", encoding="utf-8") as f:
    stopwords = set(line.strip().lower() for line in f if line.strip())

with open("stopwords/banned_keywords.txt", "r", encoding="utf-8") as f:
    bannedwords = set(line.strip().lower() for line in f if line.strip())

sbert_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
kw_model = KeyBERT(model=sbert_model)

all_texts = []
product_texts = []

for product in products:
    text_parts = []
    if product.get("title"):
        text_parts.append(product["title"])
    if product.get("description"):
        text_parts.append(product["description"])
    if product.get("bullets"):
        text_parts.append(" ".join(product["bullets"]))

    full_text = " ".join(text_parts).strip()[:1000]
    if full_text:
        all_texts.append(full_text)
        product_texts.append({
            "text": full_text,
            "title": product.get("title", ""),
            "url": product.get("url", "")
        })

#tf-idf
vectorizer = TfidfVectorizer(ngram_range=(1, 3), stop_words=list(stopwords), max_features=1000)
tfidf_matrix = vectorizer.fit_transform(all_texts)
tfidf_keywords = vectorizer.get_feature_names_out()
tfidf_scores = tfidf_matrix.sum(axis=0).A1
keyword_freq = dict(zip(tfidf_keywords, tfidf_scores))
max_freq = max(keyword_freq.values()) if keyword_freq else 1  

results = defaultdict(lambda: {
    "score": 0,
    "products": set(),
    "cosine_score": 0,
    "in_title": False,
    "source": set()
})

print("\nExtracting keywords...\n")

for entry in product_texts:
    text = entry["text"]
    title = entry["title"].lower()
    url = entry["url"]

    keybert_keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),
        stop_words=None,
        top_n=10,
        use_mmr=True,
        diversity=0.7
    )

    #merge keybert&tfidf
    candidates = set([kw for kw, _ in keybert_keywords] + list(keyword_freq.keys()))

    filtered_candidates = []
    for kw in candidates:
        clean_kw = kw.lower().strip()
        if not clean_kw or not re.search(r"[a-zA-Zäöüß]", clean_kw):
            continue
        if any(w in stopwords or w in bannedwords for w in clean_kw.split()):
            continue
        filtered_candidates.append(clean_kw)

    text_vector = sbert_model.encode(text)
    candidate_vectors = sbert_model.encode(filtered_candidates)
    cosine_scores = util.pytorch_cos_sim(text_vector, candidate_vectors)[0].cpu().numpy()

    for i, kw in enumerate(filtered_candidates):
        cosine_score = float(cosine_scores[i])
        raw_tfidf = keyword_freq.get(kw, 0)
        normalized_freq = raw_tfidf / max_freq

        results[kw]["score"] += 0.6 * cosine_score + 0.4 * normalized_freq
        results[kw]["cosine_score"] += cosine_score

        if re.search(rf'\b{re.escape(kw)}\b', text.lower()):
            results[kw]["products"].add(url)

        if kw in keyword_freq:
            results[kw]["source"].add("tfidf")
        if kw in [k.lower() for k, _ in keybert_keywords]:
            results[kw]["source"].add("keybert")
        if re.search(rf'\b{re.escape(kw)}\b', title):
            results[kw]["in_title"] = True

final_keywords = [
    {
        "keyword": kw,
        "score": round(data["score"], 4),
        "appearances": len(data["products"]),
        "semantic_score": round(data["cosine_score"], 4),
        "in_title": data["in_title"],
        "source": list(data["source"])
    }
    for kw, data in sorted(results.items(), key=lambda item: item[1]["score"], reverse=True)
]

with open("data/ranked_keywords.json", "w", encoding="utf-8") as f:
    json.dump(final_keywords, f, indent=2, ensure_ascii=False)

pd.DataFrame(final_keywords).to_csv("data/ranked_keywords.csv", index=False)

print("\nRanked keywords saved to ranked_keywords.json &.csv")

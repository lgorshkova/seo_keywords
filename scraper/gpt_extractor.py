import json
import os
import re
import pandas as pd
from collections import Counter
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

INPUT_PRODUCTS_FILE = "data/input_products.json"
GPT_KEYWORDS_JSON = "data/gpt_keywords.json"
GPT_KEYWORDS_CSV = "data/gpt_keywords.csv"

with open(INPUT_PRODUCTS_FILE, "r", encoding="utf-8") as f:
    products = json.load(f)

all_texts = []
for product in products:
    parts = []
    if product.get("title"):
        parts.append(product["title"])
    if product.get("description"):
        parts.append(product["description"])
    if product.get("bullets"):
        parts.append(" ".join(product["bullets"]))
    full_text = " ".join(parts).strip()
    if full_text:
        all_texts.append(full_text)

combined_text = "\n\n".join(all_texts)[:12000]

print("Calling ChatGPT to extract keywords...")
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Extract the top 15 unique keywords or short phrases relevant to the text. "
                           "Avoid generic or marketing terms. Return a comma-separated list only."
            },
            {"role": "user", "content": combined_text}
        ]
    )

    raw_output = response.choices[0].message.content
    print("\nGPT raw output:\n", raw_output)

    keywords = [kw.strip().lower() for kw in raw_output.split(",") if kw.strip()]
    keyword_counts = Counter(keywords)

    # Save results
    with open(GPT_KEYWORDS_JSON, "w", encoding="utf-8") as f:
        json.dump(keywords, f, indent=2, ensure_ascii=False)

    pd.DataFrame({
        "keyword": list(keyword_counts.keys()),
        "count": list(keyword_counts.values())
    }).to_csv(GPT_KEYWORDS_CSV, index=False)

    print(f"\nSaved to {GPT_KEYWORDS_JSON} and {GPT_KEYWORDS_CSV}")

except Exception as e:
    print("GPT API call failed:", e)

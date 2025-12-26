from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

def tfidf_retrieve(df, query_text, top_k=10):
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf = vectorizer.fit_transform(df["text"])

    q_vec = vectorizer.transform([query_text])
    scores = cosine_similarity(q_vec, tfidf)[0]

    top_idx = scores.argsort()[::-1][:top_k]
    return df.iloc[top_idx]["nct_number"].tolist()

def jaccard_retrieve(df, query_text, top_k=10):
    q_tokens = set(query_text.lower().split())
    scores = []

    for _, row in df.iterrows():
        doc_tokens = set(row["text"].lower().split())
        score = len(q_tokens & doc_tokens) / max(len(q_tokens | doc_tokens), 1)
        scores.append(score)

    df["score"] = scores
    return df.sort_values("score", ascending=False)["nct_number"].head(top_k).tolist()

import re
import numpy as np
import pandas as pd
import torch

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from taxonomy import TECH_CATEGORY_DEFS, SUBCATEGORY_MIN_SCORE, SUBCATEGORY_MIN_GAP

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[Model] device: {DEVICE}")

embed_model = SentenceTransformer(
    "intfloat/multilingual-e5-small",
    device=DEVICE
)

def clean_text(text: str) -> str:
    if text is None:
        return ""

    text = str(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s*\[\+\d+\s+chars\]\s*$", "", text)
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_text(title: str, description: str, content: str = "") -> str:
    title = clean_text(title)
    description = clean_text(description)
    content = clean_text(content)

    if content:
        text = f"{title}. {title}. {description}. {content}".strip()
    elif description:
        text = f"{title}. {title}. {description}".strip()
    else:
        text = title.strip()

    return re.sub(r"\s+", " ", text).strip()


def preprocess_news_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["title"] = df["title"].fillna("").astype(str)
    df["description"] = df["description"].fillna("").astype(str)

    if "content" not in df.columns:
        df["content"] = ""

    df["content"] = df["content"].fillna("").astype(str)

    df["text"] = df.apply(
        lambda row: build_text(row["title"], row["description"], row["content"]),
        axis=1
    )

    df = df[df["title"].str.strip() != ""]
    df = df[df["text"].str.len() >= 20]

    if "url" in df.columns:
        df["url"] = df["url"].fillna("").astype(str)
        df_non_empty_url = df["url"].str.strip() != ""
        df_non_url = df[~df_non_empty_url]
        df_with_url = df[df_non_empty_url].drop_duplicates(subset=["url"])
        df = pd.concat([df_with_url, df_non_url], ignore_index=True)

    df = df.drop_duplicates(subset=["text"])
    df = df.reset_index(drop=True)

    return df


def encode_texts(texts, batch_size=64):
    return embed_model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


def classify_subcategory(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if df.empty:
        df["tech_category"] = []
        df["tech_category_score"] = []
        df["tech_category_score_gap"] = []
        df["top2_category"] = []
        df["top2_score"] = []
        return df

    category_names = list(TECH_CATEGORY_DEFS.keys())
    category_texts = [TECH_CATEGORY_DEFS[name] for name in category_names]

    print("[Subcategory] Encode category definitions")
    category_embeddings = encode_texts(category_texts, batch_size=16)

    print("[Subcategory] Encode article texts")
    article_embeddings = encode_texts(df["text"].tolist(), batch_size=64)

    sims = cosine_similarity(article_embeddings, category_embeddings)

    assigned_categories = []
    top1_scores = []
    score_gaps = []
    top2_categories = []
    top2_scores = []

    for row in sims:
        sorted_idx = np.argsort(row)[::-1]

        top1_idx = sorted_idx[0]
        top2_idx = sorted_idx[1] if len(sorted_idx) > 1 else sorted_idx[0]

        top1_category = category_names[top1_idx]
        top2_category = category_names[top2_idx]

        top1_score = float(row[top1_idx])
        top2_score = float(row[top2_idx])
        score_gap = top1_score - top2_score

        if top1_score < SUBCATEGORY_MIN_SCORE or score_gap < SUBCATEGORY_MIN_GAP:
            final_category = "Other Tech"
        else:
            final_category = top1_category

        assigned_categories.append(final_category)
        top1_scores.append(top1_score)
        score_gaps.append(score_gap)
        top2_categories.append(top2_category)
        top2_scores.append(top2_score)

    df["tech_category"] = assigned_categories
    df["tech_category_score"] = top1_scores
    df["tech_category_score_gap"] = score_gaps
    df["top2_category"] = top2_categories
    df["top2_score"] = top2_scores

    return df
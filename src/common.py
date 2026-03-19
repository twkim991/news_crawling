import re
from functools import lru_cache
from typing import Iterable

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.taxonomy import (
    STACK_ALIASES,
    STACK_MAX_TAGS,
    STACK_MIN_HITS,
    TECH_CATEGORY_DEFS,
    SUBCATEGORY_MIN_GAP,
    SUBCATEGORY_MIN_SCORE,
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[Model] device: {DEVICE}")

HTML_TAG_RE = re.compile(r"<[^>]+>")
TRUNCATED_CHARS_RE = re.compile(r"\s*\[\+\d+\s+chars\]\s*$")
URL_RE = re.compile(r"http\S+|www\.\S+")
WHITESPACE_RE = re.compile(r"[\r\n\t]+")
MULTISPACE_RE = re.compile(r"\s+")
REPRINT_NOISE_RE = re.compile(
    r"(?:reuters|associated press|ap news|yonhap news|연합뉴스|무단전재|재배포|all rights reserved)",
    re.IGNORECASE,
)
NON_ALNUM_RE = re.compile(r"[^a-z0-9가-힣]+")
LOW_SIGNAL_TITLE_RE = re.compile(r"(?:video|podcast|newsletter|live updates?)", re.IGNORECASE)

REQUIRED_SCHEMA_COLUMNS = ["title", "description", "content", "url", "published_at", "source"]


@lru_cache(maxsize=1)
def get_embed_model() -> SentenceTransformer:
    print("[Model] load sentence-transformer")
    return SentenceTransformer("intfloat/multilingual-e5-small", device=DEVICE)


def clean_text(text: str) -> str:
    if text is None:
        return ""

    cleaned = str(text)
    cleaned = HTML_TAG_RE.sub(" ", cleaned)
    cleaned = TRUNCATED_CHARS_RE.sub("", cleaned)
    cleaned = URL_RE.sub(" ", cleaned)
    cleaned = REPRINT_NOISE_RE.sub(" ", cleaned)
    cleaned = WHITESPACE_RE.sub(" ", cleaned)
    return MULTISPACE_RE.sub(" ", cleaned).strip()


def _clean_text_series(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.replace(HTML_TAG_RE, " ", regex=True)
        .str.replace(TRUNCATED_CHARS_RE, "", regex=True)
        .str.replace(URL_RE, " ", regex=True)
        .str.replace(REPRINT_NOISE_RE, " ", regex=True)
        .str.replace(WHITESPACE_RE, " ", regex=True)
        .str.replace(MULTISPACE_RE, " ", regex=True)
        .str.strip()
    )


def normalize_title_for_dedup(series: pd.Series) -> pd.Series:
    return (
        _clean_text_series(series)
        .str.lower()
        .str.replace(NON_ALNUM_RE, " ", regex=True)
        .str.replace(MULTISPACE_RE, " ", regex=True)
        .str.strip()
    )


def _get_text_column(df: pd.DataFrame, column: str) -> pd.Series:
    return _clean_text_series(df[column]) if column in df else pd.Series("", index=df.index, dtype="object")


def ensure_schema(df: pd.DataFrame, *, source_name: str | None = None) -> pd.DataFrame:
    normalized = df.copy()
    for column in REQUIRED_SCHEMA_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""

    if source_name is not None:
        normalized["source"] = source_name
    else:
        normalized["source"] = normalized["source"].fillna("").replace("", "unknown")

    return normalized


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

    return MULTISPACE_RE.sub(" ", text).strip()


def build_text_series(title: pd.Series, description: pd.Series, content: pd.Series) -> pd.Series:
    text_with_content = (title + ". " + title + ". " + description + ". " + content).str.strip()
    text_without_content = (title + ". " + title + ". " + description).str.strip()
    text = np.where(
        content.str.len() > 0,
        text_with_content,
        np.where(description.str.len() > 0, text_without_content, title),
    )
    return pd.Series(text, index=title.index).str.replace(MULTISPACE_RE, " ", regex=True).str.strip()


def preprocess_news_df(df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_schema(df)
    df = df.copy()

    title_clean = _get_text_column(df, "title")
    desc_clean = _get_text_column(df, "description")
    content_clean = _get_text_column(df, "content")

    df["title"] = title_clean
    df["description"] = desc_clean
    df["content"] = content_clean
    df["normalized_title"] = normalize_title_for_dedup(df["title"])
    df["text"] = build_text_series(title_clean, desc_clean, content_clean)
    df["text_len"] = df["text"].str.len()
    df["content_ratio"] = np.where(df["text_len"] > 0, df["content"].str.len() / df["text_len"], 0.0)

    df = df[df["title"].ne("")]
    df = df[df["text_len"] >= 30]
    df = df[df["normalized_title"].str.len() >= 8]
    df = df[~df["title"].str.fullmatch(LOW_SIGNAL_TITLE_RE, na=False)]
    df = df[df["content_ratio"] <= 0.97]

    if "url" in df.columns:
        df["url"] = df["url"].fillna("").astype(str)
        has_url = df["url"].str.strip().ne("")
        df = pd.concat(
            [df.loc[has_url].drop_duplicates(subset=["url"]), df.loc[~has_url]],
            ignore_index=True,
        )

    df = df.drop_duplicates(subset=["text"])
    df = df.drop_duplicates(subset=["normalized_title"])
    return df.reset_index(drop=True)


def encode_texts(texts: Iterable[str], batch_size: int = 64):
    return get_embed_model().encode(
        list(texts),
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


@lru_cache(maxsize=1)
def _get_category_embeddings():
    category_names = tuple(TECH_CATEGORY_DEFS.keys())
    print("[Subcategory] Encode category definitions")
    category_embeddings = encode_texts(list(TECH_CATEGORY_DEFS.values()), batch_size=16)
    return category_names, category_embeddings


@lru_cache(maxsize=1)
def _get_stack_patterns():
    patterns = {}
    for stack_name, info in STACK_ALIASES.items():
        compiled = []
        for alias in info["aliases"]:
            normalized = alias.lower().strip()
            escaped = re.escape(normalized)
            if re.fullmatch(r"[a-z0-9\.\+#\-\s]+", normalized):
                pattern = re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")
            else:
                pattern = re.compile(escaped)
            compiled.append(pattern)
        patterns[stack_name] = {
            "category": info["category"],
            "patterns": tuple(compiled),
        }
    return patterns


def annotate_stack_taxonomy(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    stack_patterns = _get_stack_patterns()

    if df.empty:
        for column in [
            "stack_matches",
            "stack_labels",
            "stack_categories",
            "primary_stack",
            "secondary_stack",
            "stack_domain",
            "stack_match_count",
            "stack_label_count",
        ]:
            df[column] = pd.Series(dtype="object" if "count" not in column else "float64")
        return df

    primary_stacks = []
    secondary_stacks = []
    stack_domains = []
    stack_match_counts = []
    stack_matches = []
    stack_labels = []
    stack_categories = []
    stack_label_counts = []

    for _, row in df.iterrows():
        text = " ".join(
            [
                str(row.get("title", "")),
                str(row.get("description", "")),
                str(row.get("content", "")),
                str(row.get("text", "")),
            ]
        ).lower()

        matches = []
        for stack_name, pattern_info in stack_patterns.items():
            hit_count = sum(1 for pattern in pattern_info["patterns"] if pattern.search(text))
            if hit_count >= STACK_MIN_HITS:
                matches.append((stack_name, pattern_info["category"], hit_count))

        matches.sort(key=lambda item: (-item[2], item[0]))
        selected_matches = matches[:STACK_MAX_TAGS]
        match_names = [name for name, _, _ in selected_matches]
        match_categories = sorted({category for _, category, _ in selected_matches})

        stack_matches.append("|".join(f"{name}:{hit_count}" for name, _, hit_count in selected_matches))
        stack_labels.append("|".join(match_names))
        stack_categories.append("|".join(match_categories))
        stack_match_counts.append(float(sum(hit_count for _, _, hit_count in selected_matches)))
        stack_label_counts.append(float(len(match_names)))

        primary_name = match_names[0] if match_names else "Unspecified"
        secondary_name = match_names[1] if len(match_names) > 1 else ""
        inferred_domain = match_categories[0] if match_categories else row.get("tech_category", "Other Tech")

        primary_stacks.append(primary_name)
        secondary_stacks.append(secondary_name)
        stack_domains.append(inferred_domain)

    df["stack_matches"] = stack_matches
    df["stack_labels"] = stack_labels
    df["stack_categories"] = stack_categories
    df["primary_stack"] = primary_stacks
    df["secondary_stack"] = secondary_stacks
    df["stack_domain"] = stack_domains
    df["stack_match_count"] = stack_match_counts
    df["stack_label_count"] = stack_label_counts
    return df


def classify_subcategory(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if df.empty:
        for column in [
            "tech_category",
            "tech_category_score",
            "tech_category_score_gap",
            "top2_category",
            "top2_score",
        ]:
            df[column] = pd.Series(dtype="object" if "category" in column else "float64")
        return annotate_stack_taxonomy(df)

    category_names, category_embeddings = _get_category_embeddings()

    print("[Subcategory] Encode article texts")
    article_embeddings = encode_texts(df["text"].tolist(), batch_size=64)

    sims = cosine_similarity(article_embeddings, category_embeddings)
    top_two_indices = np.argpartition(sims, kth=-2, axis=1)[:, -2:]
    top_two_scores = np.take_along_axis(sims, top_two_indices, axis=1)
    top_two_order = np.argsort(top_two_scores, axis=1)[:, ::-1]
    top_two_indices = np.take_along_axis(top_two_indices, top_two_order, axis=1)

    top1_idx = top_two_indices[:, 0]
    top2_idx = top_two_indices[:, 1]
    row_idx = np.arange(len(df))

    top1_scores = sims[row_idx, top1_idx].astype(float)
    top2_scores = sims[row_idx, top2_idx].astype(float)
    score_gaps = top1_scores - top2_scores

    top1_categories = np.take(category_names, top1_idx)
    top2_categories = np.take(category_names, top2_idx)
    final_categories = np.where(
        (top1_scores < SUBCATEGORY_MIN_SCORE) | (score_gaps < SUBCATEGORY_MIN_GAP),
        "Other Tech",
        top1_categories,
    )

    df["tech_category"] = final_categories
    df["tech_category_score"] = top1_scores
    df["tech_category_score_gap"] = score_gaps
    df["top2_category"] = top2_categories
    df["top2_score"] = top2_scores

    return annotate_stack_taxonomy(df)

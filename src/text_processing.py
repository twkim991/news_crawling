import re

import numpy as np
import pandas as pd

HTML_TAG_RE = re.compile(r"<[^>]+>")
TRUNCATED_CHARS_RE = re.compile(r"\s*\[\+\d+\s+chars\]\s*$")
URL_RE = re.compile(r"http\S+|www\.\S+")
WHITESPACE_RE = re.compile(r"[\r\n\t]+")
MULTISPACE_RE = re.compile(r"\s+")

REQUIRED_SCHEMA_COLUMNS = ["title", "description", "content", "url", "published_at", "source"]


def clean_text(text: str) -> str:
    if text is None:
        return ""

    cleaned = str(text)
    cleaned = HTML_TAG_RE.sub(" ", cleaned)
    cleaned = TRUNCATED_CHARS_RE.sub("", cleaned)
    cleaned = URL_RE.sub(" ", cleaned)
    cleaned = WHITESPACE_RE.sub(" ", cleaned)
    return MULTISPACE_RE.sub(" ", cleaned).strip()


def _clean_text_series(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.replace(HTML_TAG_RE, " ", regex=True)
        .str.replace(TRUNCATED_CHARS_RE, "", regex=True)
        .str.replace(URL_RE, " ", regex=True)
        .str.replace(WHITESPACE_RE, " ", regex=True)
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


def preprocess_news_df(df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_schema(df)
    df = df.copy()

    title_clean = _get_text_column(df, "title")
    desc_clean = _get_text_column(df, "description")
    content_clean = _get_text_column(df, "content")

    df["title"] = title_clean
    df["description"] = desc_clean
    df["content"] = content_clean
    df["text"] = [
        build_text(title, description, content)
        for title, description, content in zip(title_clean, desc_clean, content_clean)
    ]
    df["text"] = pd.Series(df["text"], index=df.index).str.replace(MULTISPACE_RE, " ", regex=True).str.strip()

    df = df[df["title"].ne("")]
    df = df[df["text"].str.len() >= 20]

    if "url" in df.columns:
        df["url"] = df["url"].fillna("").astype(str)
        has_url = df["url"].str.strip().ne("")
        df = pd.concat(
            [df.loc[has_url].drop_duplicates(subset=["url"]), df.loc[~has_url]],
            ignore_index=True,
        )

    return df.drop_duplicates(subset=["text"]).reset_index(drop=True)

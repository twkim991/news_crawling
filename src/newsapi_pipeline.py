import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

from io_utils import ensure_dir
from settings import NEWSAPI_PROCESSED_PATH, NEWSAPI_RAW_PATH, RAW_DIR, PROCESSED_DIR
from text_processing import preprocess_news_df

load_dotenv()

API_KEY = os.getenv("newsapi_key")

ensure_dir(RAW_DIR)
ensure_dir(PROCESSED_DIR)


def fetch_newsapi_everything(
    query: str,
    from_date: str,
    to_date: str,
    language: str = "en",
    page_size: int = 100,
    max_pages: int = 1,
) -> pd.DataFrame:
    url = "https://newsapi.org/v2/everything"
    all_articles = []

    print(f"[NewsAPI] max_pages={max_pages}")

    for page in range(1, max_pages + 1):
        print(f"[NewsAPI] request page={page}")

        params = {
            "q": query,
            "searchIn": "title,description",
            "from": from_date,
            "to": to_date,
            "language": language,
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "page": page,
            "apiKey": API_KEY,
        }

        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()

        data = resp.json()

        if data.get("status") != "ok":
            raise RuntimeError(f"NewsAPI error: {data}")

        articles = data.get("articles", [])
        if not articles:
            break

        all_articles.extend(articles)
        time.sleep(0.3)

        if len(articles) < page_size:
            break

    return pd.DataFrame(all_articles)


def normalize_newsapi_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[
            "source", "title", "description", "content", "url", "published_at"
        ])

    df = df.copy()

    df["title"] = df.get("title", "").fillna("")
    df["description"] = df.get("description", "").fillna("")
    df["content"] = df.get("content", "").fillna("")
    df["url"] = df.get("url", "").fillna("")
    df["published_at"] = df.get("publishedAt", "").fillna("")
    df["source"] = "NewsAPI"

    return df[["source", "title", "description", "content", "url", "published_at"]]


def main():
    query = (
        '(technology OR software OR developer OR programming OR '
        'cloud OR database OR "artificial intelligence" OR AI)'
    )
    from_date = "2026-03-01"
    to_date = "2026-03-12"

    print("[1] Fetch NewsAPI data")
    raw_df = fetch_newsapi_everything(
        query=query,
        from_date=from_date,
        to_date=to_date,
        language="en",
        page_size=100,
        max_pages=1,
    )
    print("raw rows:", len(raw_df))

    raw_path = NEWSAPI_RAW_PATH
    raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")

    print("[2] Normalize schema")
    norm_df = normalize_newsapi_df(raw_df)

    print("[3] Preprocess")
    clean_df = preprocess_news_df(norm_df)
    print("processed rows:", len(clean_df))

    processed_path = NEWSAPI_PROCESSED_PATH
    clean_df.to_csv(processed_path, index=False, encoding="utf-8-sig")

    print("[4] Done")
    print("saved raw      :", raw_path)
    print("saved processed:", processed_path)


if __name__ == "__main__":
    main()
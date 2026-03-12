import os
import time
import requests
import pandas as pd

from dotenv import load_dotenv
from common import preprocess_news_df

load_dotenv()

API_KEY = os.getenv("newsapi_key")

RAW_DIR = r"data\raw"
PROCESSED_DIR = r"data\processed"

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


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

    raw_path = os.path.join(RAW_DIR, "newsapi_raw.csv")
    raw_df.to_csv(raw_path, index=False, encoding="utf-8-sig")

    print("[2] Normalize schema")
    norm_df = normalize_newsapi_df(raw_df)

    print("[3] Preprocess")
    clean_df = preprocess_news_df(norm_df)
    print("processed rows:", len(clean_df))

    processed_path = os.path.join(PROCESSED_DIR, "newsapi_processed.csv")
    clean_df.to_csv(processed_path, index=False, encoding="utf-8-sig")

    print("[4] Done")
    print("saved raw      :", raw_path)
    print("saved processed:", processed_path)


if __name__ == "__main__":
    main()
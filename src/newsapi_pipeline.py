import os
import time

import argparse
import pandas as pd
import requests

from dotenv import load_dotenv
from src.common import preprocess_news_df

load_dotenv()

API_KEY = os.getenv("newsapi_key")

RAW_DIR = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")

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
    parser = argparse.ArgumentParser(description="Fetch and preprocess NewsAPI articles")
    parser.add_argument(
        "--query",
        default='(technology OR software OR developer OR programming OR cloud OR database OR "artificial intelligence" OR AI)',
        help="NewsAPI everything query",
    )
    parser.add_argument("--from-date", default="2026-03-01", help="inclusive start date (YYYY-MM-DD)")
    parser.add_argument("--to-date", default="2026-03-12", help="inclusive end date (YYYY-MM-DD)")
    parser.add_argument("--language", default="en", help="NewsAPI language filter")
    parser.add_argument("--page-size", type=int, default=100, help="results per page")
    parser.add_argument("--max-pages", type=int, default=1, help="maximum pages to fetch")
    parser.add_argument("--raw-output", default=os.path.join(RAW_DIR, "newsapi_raw.csv"), help="raw output csv path")
    parser.add_argument("--processed-output", default=os.path.join(PROCESSED_DIR, "newsapi_processed.csv"), help="processed output csv path")
    args = parser.parse_args()

    if not API_KEY:
        raise RuntimeError("Missing NewsAPI key. Set `newsapi_key` in the environment or .env file.")

    print("[1] Fetch NewsAPI data")
    raw_df = fetch_newsapi_everything(
        query=args.query,
        from_date=args.from_date,
        to_date=args.to_date,
        language=args.language,
        page_size=args.page_size,
        max_pages=args.max_pages,
    )
    print("raw rows:", len(raw_df))

    raw_df.to_csv(args.raw_output, index=False, encoding="utf-8-sig")

    print("[2] Normalize schema")
    norm_df = normalize_newsapi_df(raw_df)

    print("[3] Preprocess")
    clean_df = preprocess_news_df(norm_df)
    print("processed rows:", len(clean_df))

    clean_df.to_csv(args.processed_output, index=False, encoding="utf-8-sig")

    print("[4] Done")
    print("saved raw      :", args.raw_output)
    print("saved processed:", args.processed_output)


if __name__ == "__main__":
    main()

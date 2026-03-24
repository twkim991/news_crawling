# newsapi_pipeline.py

import argparse
import os
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse

import pandas as pd
import requests
from dotenv import load_dotenv

from src.common import preprocess_news_df

load_dotenv()

API_KEY = os.getenv("newsapi_key")

RAW_DIR = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")

DEFAULT_QUERY_GROUPS = [
    {
        "label": "language_backend",
        "query": '(python OR java OR javascript OR typescript OR spring OR django OR fastapi)',
    },
    {
        "label": "frontend_web",
        "query": '(react OR next.js OR vue OR angular OR svelte)',
    },
    {
        "label": "ai_ml",
        "query": '(pytorch OR tensorflow OR openai OR "machine learning" OR "deep learning" OR llm)',
    },
    {
        "label": "cloud_devops",
        "query": '(kubernetes OR docker OR aws OR azure OR "google cloud" OR terraform OR jenkins)',
    },
    {
        "label": "data_db",
        "query": '(postgresql OR mongodb OR redis OR kafka OR mysql OR elasticsearch)',
    },
]

DEFAULT_OUTPUT_COLUMNS = [
    "source",
    "source_name",
    "title",
    "description",
    "content",
    "url",
    "published_at",
    "domain",
    "query_label",
    "query_text",
    "request_from",
    "request_to",
]

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


def _safe_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column].fillna("").astype(str)
    return pd.Series("", index=df.index, dtype="object")


def _safe_domain(url: str) -> str:
    value = str(url).strip()
    if not value:
        return ""
    return urlparse(value).netloc.lower()


def _normalize_query_groups(
    query: str | None = None,
    query_groups: list[dict] | None = None,
) -> list[dict]:
    if query_groups:
        normalized = []
        for idx, item in enumerate(query_groups, start=1):
            label = str(item.get("label", f"group_{idx}")).strip() or f"group_{idx}"
            query_text = str(item.get("query", "")).strip()
            if not query_text:
                continue
            normalized.append({
                "label": label,
                "query": query_text,
            })
        if normalized:
            return normalized

    if query is not None and str(query).strip():
        return [{
            "label": "custom_query",
            "query": str(query).strip(),
        }]

    return DEFAULT_QUERY_GROUPS.copy()


def _parse_ymd(date_str: str) -> datetime:
    return datetime.strptime(str(date_str).strip(), "%Y-%m-%d")


def _daterange_days(from_date: str, to_date: str) -> list[tuple[str, str]]:
    start_dt = _parse_ymd(from_date)
    end_dt = _parse_ymd(to_date)

    if start_dt > end_dt:
        raise ValueError(f"from_date({from_date}) must be <= to_date({to_date})")

    ranges = []
    current = start_dt
    while current <= end_dt:
        day_str = current.strftime("%Y-%m-%d")
        ranges.append((day_str, day_str))
        current += timedelta(days=1)

    return ranges


def fetch_newsapi_everything(
    query: str,
    from_date: str,
    to_date: str,
    language: str = "en",
    page_size: int = 100,
    max_pages: int = 1,
    sleep_seconds: float = 0.3,
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

        if len(articles) < page_size:
            break

        time.sleep(sleep_seconds)

    return pd.DataFrame(all_articles)


def fetch_newsapi_multi_query_by_day(
    query_groups: list[dict],
    from_date: str,
    to_date: str,
    language: str = "en",
    page_size: int = 100,
    max_pages: int = 1,
    sleep_seconds: float = 0.3,
    continue_on_error: bool = False,
) -> pd.DataFrame:
    collected_frames = []
    day_ranges = _daterange_days(from_date, to_date)

    total_tasks = len(query_groups) * len(day_ranges)
    current_task = 0

    for day_from, day_to in day_ranges:
        print("")
        print(f"[NewsAPI] ===== Day Window: {day_from} =====")

        for group_idx, group in enumerate(query_groups, start=1):
            current_task += 1

            label = group["label"]
            query_text = group["query"]

            print("")
            print(f"[NewsAPI] ----- Task {current_task}/{total_tasks} -----")
            print(f"[NewsAPI] day   : {day_from}")
            print(f"[NewsAPI] group : {group_idx}/{len(query_groups)}")
            print(f"[NewsAPI] label : {label}")
            print(f"[NewsAPI] query : {query_text}")

            try:
                part_df = fetch_newsapi_everything(
                    query=query_text,
                    from_date=day_from,
                    to_date=day_to,
                    language=language,
                    page_size=page_size,
                    max_pages=max_pages,
                    sleep_seconds=sleep_seconds,
                )
            except Exception as exc:
                print(
                    f"[NewsAPI] query failed: "
                    f"day={day_from}, label={label}, error={exc}"
                )
                if continue_on_error:
                    continue
                raise

            if part_df.empty:
                print(f"[NewsAPI] no rows fetched for day={day_from}, label={label}")
                continue

            part_df = part_df.copy()
            part_df["query_label"] = label
            part_df["query_text"] = query_text
            part_df["request_from"] = day_from
            part_df["request_to"] = day_to

            print(f"[NewsAPI] fetched rows for day={day_from}, label={label}: {len(part_df)}")
            collected_frames.append(part_df)

    if not collected_frames:
        return pd.DataFrame()

    raw_df = pd.concat(collected_frames, ignore_index=True)
    return raw_df.reset_index(drop=True)


def normalize_newsapi_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=DEFAULT_OUTPUT_COLUMNS)

    working = df.copy()

    working["title"] = working.get("title", "").fillna("")
    working["description"] = working.get("description", "").fillna("")
    working["content"] = working.get("content", "").fillna("")
    working["url"] = working.get("url", "").fillna("")
    working["published_at"] = working.get("publishedAt", "").fillna("")

    if "source" in working.columns:
        working["source_name"] = working["source"].apply(
            lambda x: x.get("name", "") if isinstance(x, dict) else ""
        )
    else:
        working["source_name"] = ""

    working["source"] = "NewsAPI"
    working["domain"] = working["url"].apply(_safe_domain)

    if "query_label" not in working.columns:
        working["query_label"] = ""
    if "query_text" not in working.columns:
        working["query_text"] = ""
    if "request_from" not in working.columns:
        working["request_from"] = ""
    if "request_to" not in working.columns:
        working["request_to"] = ""

    return working[DEFAULT_OUTPUT_COLUMNS].copy()


def dedupe_newsapi_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    working = df.copy()
    before_total = len(working)

    if "url" in working.columns:
        working["url"] = working["url"].fillna("").astype(str).str.strip()

        url_non_empty = working["url"].ne("")
        with_url = working.loc[url_non_empty].copy()
        without_url = working.loc[~url_non_empty].copy()

        before_with_url = len(with_url)
        with_url = with_url.drop_duplicates(subset=["url"], keep="first")
        print(f"[NewsAPI] dedupe by url: {before_with_url} -> {len(with_url)}")

        working = pd.concat([with_url, without_url], ignore_index=True)

    title_series = _safe_series(working, "title").str.strip().str.lower()
    published_series = _safe_series(working, "published_at").str.strip()
    source_name_series = _safe_series(working, "source_name").str.strip().str.lower()

    working["_dedupe_title"] = title_series
    working["_dedupe_published_at"] = published_series
    working["_dedupe_source_name"] = source_name_series

    fallback_mask = (
        working["_dedupe_title"].ne("")
        & working["_dedupe_published_at"].ne("")
    )

    fallback_part = working.loc[fallback_mask].copy()
    non_fallback_part = working.loc[~fallback_mask].copy()

    before_fallback = len(fallback_part)
    fallback_part = fallback_part.drop_duplicates(
        subset=["_dedupe_title", "_dedupe_published_at", "_dedupe_source_name"],
        keep="first",
    )
    print(
        "[NewsAPI] dedupe by title+published_at+source_name: "
        f"{before_fallback} -> {len(fallback_part)}"
    )

    working = pd.concat([fallback_part, non_fallback_part], ignore_index=True)
    working = working.drop(
        columns=[
            "_dedupe_title",
            "_dedupe_published_at",
            "_dedupe_source_name",
        ],
        errors="ignore",
    )

    working = working.reset_index(drop=True)

    print(f"[NewsAPI] dedupe total: {before_total} -> {len(working)}")
    return working


def run_newsapi_collection(
    query=None,
    query_groups=None,
    from_date=None,
    to_date=None,
    language="en",
    page_size=100,
    max_pages=1,
    raw_output=None,
    output_path=None,
    continue_on_error=False,
):
    if not API_KEY:
        raise RuntimeError("Missing NewsAPI key. Set `newsapi_key` in the environment or .env file.")

    if from_date is None or to_date is None:
        raise ValueError("from_date and to_date must be provided in pipeline execution")

    normalized_query_groups = _normalize_query_groups(
        query=query,
        query_groups=query_groups,
    )

    print("[NewsAPI] Query groups")
    for idx, item in enumerate(normalized_query_groups, start=1):
        print(f"  {idx}. {item['label']} -> {item['query']}")

    print("[NewsAPI] Date windows")
    day_ranges = _daterange_days(from_date, to_date)
    for idx, (day_from, day_to) in enumerate(day_ranges, start=1):
        print(f"  {idx}. {day_from} ~ {day_to}")

    print("[NewsAPI] Fetch")
    raw_df = fetch_newsapi_multi_query_by_day(
        query_groups=normalized_query_groups,
        from_date=from_date,
        to_date=to_date,
        language=language,
        page_size=page_size,
        max_pages=max_pages,
        continue_on_error=continue_on_error,
    )

    print("[NewsAPI] raw rows before dedupe:", len(raw_df))

    if raw_output:
        raw_df.to_csv(raw_output, index=False, encoding="utf-8-sig")

    print("[NewsAPI] Normalize")
    norm_df = normalize_newsapi_df(raw_df)

    print("[NewsAPI] Dedupe")
    dedup_df = dedupe_newsapi_df(norm_df)

    print("[NewsAPI] Preprocess")
    clean_df = preprocess_news_df(dedup_df)

    print("processed rows:", len(clean_df))

    if output_path:
        clean_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    return clean_df


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and preprocess NewsAPI articles with multi-query + day-splitting + dedupe"
    )
    parser.add_argument(
        "--query",
        default=None,
        help="single NewsAPI everything query. If omitted, DEFAULT_QUERY_GROUPS is used.",
    )
    parser.add_argument("--from-date", default="2026-03-01", help="inclusive start date (YYYY-MM-DD)")
    parser.add_argument("--to-date", default="2026-03-12", help="inclusive end date (YYYY-MM-DD)")
    parser.add_argument("--language", default="en", help="NewsAPI language filter")
    parser.add_argument("--page-size", type=int, default=100, help="results per page")
    parser.add_argument("--max-pages", type=int, default=1, help="maximum pages to fetch per query group")
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="continue remaining query/day tasks even if one request fails",
    )
    parser.add_argument(
        "--raw-output",
        default=os.path.join(RAW_DIR, "newsapi_raw.csv"),
        help="raw output csv path",
    )
    parser.add_argument(
        "--processed-output",
        default=os.path.join(PROCESSED_DIR, "newsapi_processed.csv"),
        help="processed output csv path",
    )
    args = parser.parse_args()

    if not API_KEY:
        raise RuntimeError("Missing NewsAPI key. Set `newsapi_key` in the environment or .env file.")

    print("[1] Fetch NewsAPI data")
    clean_df = run_newsapi_collection(
        query=args.query,
        query_groups=None,
        from_date=args.from_date,
        to_date=args.to_date,
        language=args.language,
        page_size=args.page_size,
        max_pages=args.max_pages,
        raw_output=args.raw_output,
        output_path=args.processed_output,
        continue_on_error=args.continue_on_error,
    )

    print("[4] Done")
    print("saved raw      :", args.raw_output)
    print("saved processed:", args.processed_output)
    print("final rows     :", len(clean_df))


if __name__ == "__main__":
    main()
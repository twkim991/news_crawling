import argparse
import glob
import os
from urllib.parse import urlparse

import pandas as pd

from src.common import preprocess_news_df

RAW_DIR = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")

DEFAULT_COLUMNS = [
    "source",
    "title",
    "description",
    "content",
    "url",
    "published_at",
    "domain",
    "source_common_name",
    "document_identifier",
    "themes",
    "organizations",
    "tone",
    "file_timestamp",
]


def _safe_domain(url: str) -> str:
    value = str(url).strip()
    if not value:
        return ""
    return urlparse(value).netloc.lower()


def _safe_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column].fillna("").astype(str)
    return pd.Series("", index=df.index, dtype="object")


def _discover_geeknews_files(
    raw_dir: str = RAW_DIR,
    pattern: str = "geeknews_*.csv",
) -> list[str]:
    return sorted(glob.glob(os.path.join(raw_dir, pattern)))


def _load_geeknews_monthly_files(file_paths: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for path in file_paths:
        try:
            frame = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            continue

        if frame.empty:
            continue

        frame = frame.copy()
        frame["source_file"] = os.path.basename(path)
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=["date", "title", "link", "source_file"])

    return pd.concat(frames, ignore_index=True)


def _normalize_geeknews_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

    working = df.copy()
    working["date"] = pd.to_datetime(_safe_series(working, "date"), errors="coerce")
    working = working.loc[working["date"].notna()].copy()

    if working.empty:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

    title = _safe_series(working, "title").str.strip()
    url = _safe_series(working, "link").str.strip()

    working = working.loc[title.ne("") & url.ne("")].copy()
    if working.empty:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

    normalized = pd.DataFrame(index=working.index)
    normalized["source"] = "GeekNews"
    normalized["title"] = _safe_series(working, "title").str.strip()
    normalized["description"] = ""
    normalized["content"] = ""
    normalized["url"] = _safe_series(working, "link").str.strip()
    normalized["published_at"] = working["date"].dt.strftime("%Y-%m-%d 00:00:00")
    normalized["domain"] = normalized["url"].map(_safe_domain)
    normalized["source_common_name"] = "GeekNews"
    normalized["document_identifier"] = normalized["url"]
    normalized["themes"] = ""
    normalized["organizations"] = ""
    normalized["tone"] = ""
    normalized["file_timestamp"] = working["date"].dt.strftime("%Y%m%d000000")

    return (
        normalized[DEFAULT_COLUMNS]
        .drop_duplicates(subset=["url", "title", "published_at"])
        .reset_index(drop=True)
    )


def run_geeknews_collection(
    run_date: str,
    raw_dir: str = RAW_DIR,
    raw_output: str | None = None,
    processed_output: str | None = None,
) -> pd.DataFrame:
    file_paths = _discover_geeknews_files(raw_dir=raw_dir)

    if not file_paths:
        empty_df = pd.DataFrame(columns=DEFAULT_COLUMNS)
        if raw_output:
            pd.DataFrame(columns=["date", "title", "link", "source_file"]).to_csv(
                raw_output,
                index=False,
                encoding="utf-8-sig",
            )
        if processed_output:
            empty_df.to_csv(processed_output, index=False, encoding="utf-8-sig")
        return empty_df

    monthly_df = _load_geeknews_monthly_files(file_paths)

    if monthly_df.empty:
        empty_df = pd.DataFrame(columns=DEFAULT_COLUMNS)
        if raw_output:
            pd.DataFrame(columns=["date", "title", "link", "source_file"]).to_csv(
                raw_output,
                index=False,
                encoding="utf-8-sig",
            )
        if processed_output:
            empty_df.to_csv(processed_output, index=False, encoding="utf-8-sig")
        return empty_df

    monthly_df["date"] = pd.to_datetime(
        _safe_series(monthly_df, "date"),
        errors="coerce",
    )
    target_date = pd.to_datetime(run_date, format="%Y-%m-%d", errors="raise")
    daily_df = monthly_df.loc[monthly_df["date"] == target_date].copy()

    if raw_output:
        daily_df.to_csv(raw_output, index=False, encoding="utf-8-sig")

    normalized = _normalize_geeknews_df(daily_df)
    processed = preprocess_news_df(normalized)

    if processed_output:
        processed.to_csv(processed_output, index=False, encoding="utf-8-sig")

    return processed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load monthly GeekNews CSV files and build a daily processed dataset"
    )
    parser.add_argument("--run-date", required=True, help="target date (YYYY-MM-DD)")
    parser.add_argument(
        "--raw-dir",
        default=RAW_DIR,
        help="directory containing geeknews_YYYY-MM.csv files",
    )
    parser.add_argument(
        "--raw-output",
        default=os.path.join(RAW_DIR, "geeknews_raw.csv"),
        help="daily raw csv path",
    )
    parser.add_argument(
        "--processed-output",
        default=os.path.join(PROCESSED_DIR, "geeknews_processed.csv"),
        help="daily processed csv path",
    )
    args = parser.parse_args()

    processed = run_geeknews_collection(
        run_date=args.run_date,
        raw_dir=args.raw_dir,
        raw_output=args.raw_output,
        processed_output=args.processed_output,
    )

    print("[GeekNews] run_date:", args.run_date)
    print("[GeekNews] processed rows:", len(processed))
    print("[GeekNews] saved processed:", args.processed_output)


if __name__ == "__main__":
    main()
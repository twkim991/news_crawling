# ssafy_dataset_pipeline.py

import argparse
import glob
import os
import re
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

TECH_CATEGORY_KEYWORDS = [
    "it",
    "ict",
    "과학",
    "기술",
    "테크",
    "디지털",
    "산업",
    "경제",
    "국제",
    "기업",
    "스타트업",
    "벤처",
    "증권",
]

TECH_TEXT_KEYWORDS = [
    "ai", "a.i", "llm", "ml", "머신러닝", "딥러닝", "생성형 ai", "인공지능",
    "반도체", "칩", "gpu", "cpu", "npu",
    "클라우드", "서버", "api", "sdk", "플랫폼", "소프트웨어", "하드웨어", "오픈소스",
    "데이터", "데이터센터", "db", "database", "sql", "nosql",
    "앱", "모바일", "웹", "브라우저", "프론트엔드", "백엔드", "개발자", "개발",
    "로봇", "자율주행", "드론", "iot", "사물인터넷", "사이버보안", "보안", "해킹",
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "kotlin", "swift", "dart",
    "react", "vue", "angular", "svelte", "next.js", "spring", "django", "fastapi", "express", "nestjs",
    "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy",
    "postgresql", "postgres", "mysql", "sqlite", "sql server", "mssql", "mongodb", "redis",
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "kafka", "spark", "dbt",
    "github actions", "gitlab ci", "gitlab ci/cd", "jenkins", "terraform",
]

TECH_KEYWORD_RE = re.compile(
    "|".join(re.escape(keyword) for keyword in sorted(TECH_TEXT_KEYWORDS, key=len, reverse=True)),
    flags=re.IGNORECASE,
)

TECH_CATEGORY_RE = re.compile(
    "|".join(re.escape(keyword) for keyword in sorted(TECH_CATEGORY_KEYWORDS, key=len, reverse=True)),
    flags=re.IGNORECASE,
)


def _safe_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column].fillna("").astype(str)
    return pd.Series("", index=df.index, dtype="object")


def _safe_domain(url: str) -> str:
    value = str(url).strip()
    if not value:
        return ""
    return urlparse(value).netloc.lower()


def _discover_ssafy_files(
    raw_dir: str = RAW_DIR,
    pattern: str = "ssafy_dataset_news_*.csv",
) -> list[str]:
    return sorted(glob.glob(os.path.join(raw_dir, pattern)))


def _load_ssafy_files(file_paths: list[str]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for path in file_paths:
        try:
            frame = pd.read_csv(path, sep="|", engine="python")
        except pd.errors.EmptyDataError:
            continue

        if frame.empty:
            continue

        frame = frame.copy()
        frame["source_file"] = os.path.basename(path)
        frames.append(frame)

    if not frames:
        return pd.DataFrame(
            columns=[
                "company",
                "title",
                "link",
                "published",
                "category",
                "category_str",
                "reporter",
                "article",
                "source_file",
            ]
        )

    return pd.concat(frames, ignore_index=True)


def _apply_ssafy_candidate_filter(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    working = df.copy()

    title = _safe_series(working, "title").str.strip()
    article = _safe_series(working, "article").str.strip()
    category = _safe_series(working, "category").str.strip()
    category_str = _safe_series(working, "category_str").str.strip()
    link = _safe_series(working, "link").str.strip()
    published = _safe_series(working, "published").str.strip()

    valid_mask = (
        title.ne("")
        & article.ne("")
        & link.ne("")
        & published.ne("")
    )

    combined_category = (category + " " + category_str).str.strip()
    combined_text = (title + " " + article).str.strip()

    category_mask = combined_category.str.contains(TECH_CATEGORY_RE, na=False)
    keyword_mask = combined_text.str.contains(TECH_KEYWORD_RE, na=False)

    candidate_mask = valid_mask & (category_mask | keyword_mask)

    filtered = working.loc[candidate_mask].copy()

    print("[SSAFY Dataset] rows before candidate filter:", len(working))
    print("[SSAFY Dataset] valid rows:", int(valid_mask.sum()))
    print("[SSAFY Dataset] category match rows:", int((valid_mask & category_mask).sum()))
    print("[SSAFY Dataset] keyword match rows:", int((valid_mask & keyword_mask).sum()))
    print("[SSAFY Dataset] rows after candidate filter:", len(filtered))

    return filtered


def _normalize_ssafy_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

    working = df.copy()

    title = _safe_series(working, "title").str.strip()
    article = _safe_series(working, "article").str.strip()
    link = _safe_series(working, "link").str.strip()
    published = pd.to_datetime(_safe_series(working, "published"), errors="coerce")
    category = _safe_series(working, "category").str.strip()
    category_str = _safe_series(working, "category_str").str.strip()
    company = _safe_series(working, "company").str.strip()

    valid_mask = title.ne("") & article.ne("") & link.ne("") & published.notna()
    working = working.loc[valid_mask].copy()
    if working.empty:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

    title = _safe_series(working, "title").str.strip()
    article = _safe_series(working, "article").str.strip()
    link = _safe_series(working, "link").str.strip()
    published = pd.to_datetime(_safe_series(working, "published"), errors="coerce")
    category = _safe_series(working, "category").str.strip()
    category_str = _safe_series(working, "category_str").str.strip()
    company = _safe_series(working, "company").str.strip()

    normalized = pd.DataFrame(index=working.index)
    normalized["source"] = "SSAFY_DATASET"
    normalized["title"] = title
    normalized["description"] = category_str.where(category_str.ne(""), category)
    normalized["content"] = article
    normalized["url"] = link
    normalized["published_at"] = published.dt.strftime("%Y-%m-%d %H:%M:%S")
    normalized["domain"] = normalized["url"].map(_safe_domain)
    normalized["source_common_name"] = company.where(company.ne(""), "SSAFY_DATASET")
    normalized["document_identifier"] = link
    normalized["themes"] = category_str.where(category_str.ne(""), category)
    normalized["organizations"] = company
    normalized["tone"] = ""
    normalized["file_timestamp"] = published.dt.strftime("%Y%m%d%H%M%S")

    return (
        normalized[DEFAULT_COLUMNS]
        .drop_duplicates(subset=["url"])
        .reset_index(drop=True)
    )


def run_ssafy_dataset_collection(
    run_date: str,
    raw_dir: str = RAW_DIR,
    raw_output: str | None = None,
    processed_output: str | None = None,
) -> pd.DataFrame:
    file_paths = _discover_ssafy_files(raw_dir=raw_dir)

    if not file_paths:
        empty_raw = pd.DataFrame(
            columns=[
                "company",
                "title",
                "link",
                "published",
                "category",
                "category_str",
                "reporter",
                "article",
                "source_file",
            ]
        )
        empty_processed = pd.DataFrame(columns=DEFAULT_COLUMNS)

        if raw_output:
            empty_raw.to_csv(raw_output, index=False, encoding="utf-8-sig")
        if processed_output:
            empty_processed.to_csv(processed_output, index=False, encoding="utf-8-sig")
        return empty_processed

    raw_df = _load_ssafy_files(file_paths)
    if raw_df.empty:
        empty_processed = pd.DataFrame(columns=DEFAULT_COLUMNS)
        if raw_output:
            raw_df.to_csv(raw_output, index=False, encoding="utf-8-sig")
        if processed_output:
            empty_processed.to_csv(processed_output, index=False, encoding="utf-8-sig")
        return empty_processed

    raw_df["published_dt"] = pd.to_datetime(_safe_series(raw_df, "published"), errors="coerce")
    target_date = pd.to_datetime(run_date, format="%Y-%m-%d", errors="raise")
    daily_df = raw_df.loc[raw_df["published_dt"].dt.normalize() == target_date].copy()

    if raw_output:
        daily_df.drop(columns=["published_dt"], errors="ignore").to_csv(
            raw_output,
            index=False,
            encoding="utf-8-sig",
        )

    candidate_df = _apply_ssafy_candidate_filter(daily_df)
    normalized = _normalize_ssafy_df(candidate_df)
    processed = preprocess_news_df(normalized)

    if processed_output:
        processed.to_csv(processed_output, index=False, encoding="utf-8-sig")

    print("[SSAFY Dataset] run_date:", run_date)
    print("[SSAFY Dataset] daily raw rows:", len(daily_df))
    print("[SSAFY Dataset] processed rows:", len(processed))

    return processed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load semiannual SSAFY dataset csv files and build a daily processed dataset"
    )
    parser.add_argument("--run-date", required=True, help="target date (YYYY-MM-DD)")
    parser.add_argument(
        "--raw-dir",
        default=RAW_DIR,
        help="directory containing ssafy_dataset_news_*.csv files",
    )
    parser.add_argument(
        "--raw-output",
        default=os.path.join(RAW_DIR, "ssafy_dataset_raw.csv"),
        help="daily raw csv path",
    )
    parser.add_argument(
        "--processed-output",
        default=os.path.join(PROCESSED_DIR, "ssafy_dataset_processed.csv"),
        help="daily processed csv path",
    )
    args = parser.parse_args()

    processed = run_ssafy_dataset_collection(
        run_date=args.run_date,
        raw_dir=args.raw_dir,
        raw_output=args.raw_output,
        processed_output=args.processed_output,
    )

    print("[SSAFY Dataset] saved processed:", args.processed_output)
    print("[SSAFY Dataset] processed rows:", len(processed))


if __name__ == "__main__":
    main()
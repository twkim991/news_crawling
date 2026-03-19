import argparse
import io
import os
import re
import zipfile
from datetime import datetime, timezone
from urllib.parse import urlparse

import pandas as pd
import requests

from common import preprocess_news_df

RAW_DIR = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")
MASTERFILELIST_URL = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
GKG_SUFFIX = ".gkg.csv.zip"
DEFAULT_COLUMNS = [
    "source", "title", "description", "content", "url", "published_at",
    "domain", "source_common_name", "document_identifier", "themes", "persons",
    "organizations", "locations", "tone", "gcam", "file_timestamp", "file_url",
]
GKG_COLUMNS = [
    "gkg_record_id", "date", "source_collection_id", "source_common_name", "document_identifier",
    "counts", "v2_counts", "themes", "enhanced_themes", "locations", "v2_locations", "persons",
    "v2_persons", "organizations", "v2_organizations", "tone", "enhanced_dates", "gcam",
    "sharing_image", "related_images", "social_image_embeds", "social_video_embeds", "quotations",
    "all_names", "amounts", "translation_info", "extras_xml",
]
DEFAULT_TECH_KEYWORDS = [
    "technology", "software", "developer", "programming", "cloud", "database", "cybersecurity",
    "semiconductor", "robotics", "artificial intelligence", "machine learning", "generative ai",
    "llm", "openai", "anthropic", "google cloud", "aws", "azure", "kubernetes", "docker",
    "python", "java", "typescript", "react", "pytorch", "tensorflow", "github", "oracle",
    "microsoft", "google", "meta", "nvidia", "tsmc", "chip", "data center",
]
URL_TOKEN_SPLIT_RE = re.compile(r"[-_/]+")
NON_ALNUM_RE = re.compile(r"[^0-9A-Za-z가-힣\s]+")
MULTISPACE_RE = re.compile(r"\s+")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


def _parse_datetime(value: str) -> datetime:
    if len(value) == 8:
        return datetime.strptime(value, "%Y%m%d").replace(tzinfo=timezone.utc)
    if len(value) == 14:
        return datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    raise ValueError("Datetime must be YYYYMMDD or YYYYMMDDHHMMSS")


def _safe_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column].fillna("").astype(str)
    return pd.Series("", index=df.index, dtype="object")


def _fetch_masterfile_index() -> pd.DataFrame:
    response = requests.get(MASTERFILELIST_URL, timeout=60)
    response.raise_for_status()

    rows = []
    for line in response.text.splitlines():
        parts = line.strip().split(" ")
        if len(parts) < 3:
            continue
        url = parts[-1]
        if not url.endswith(GKG_SUFFIX):
            continue
        timestamp = os.path.basename(url).split(".")[0]
        if len(timestamp) != 14 or not timestamp.isdigit():
            continue
        rows.append({
            "file_timestamp": timestamp,
            "size_bytes": int(parts[0]),
            "md5": parts[1],
            "file_url": url,
        })

    index_df = pd.DataFrame(rows)
    if index_df.empty:
        return index_df
    return index_df.sort_values("file_timestamp").reset_index(drop=True)


def list_gkg_file_urls(start_datetime: str, end_datetime: str, max_files: int | None = None) -> pd.DataFrame:
    start = _parse_datetime(start_datetime)
    end = _parse_datetime(end_datetime)
    if start >= end:
        raise ValueError("start_datetime must be earlier than end_datetime")

    index_df = _fetch_masterfile_index()
    if index_df.empty:
        return index_df

    mask = index_df["file_timestamp"].between(start.strftime("%Y%m%d%H%M%S"), end.strftime("%Y%m%d%H%M%S"), inclusive="left")
    filtered = index_df.loc[mask].copy()
    if max_files is not None:
        filtered = filtered.head(max_files)
    return filtered.reset_index(drop=True)


def _read_zipped_tsv(content: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        members = [name for name in archive.namelist() if name.endswith('.csv')]
        if not members:
            raise ValueError("No CSV file found inside GDELT archive")
        with archive.open(members[0]) as fp:
            return pd.read_csv(
                fp,
                sep='\t',
                names=GKG_COLUMNS,
                dtype=str,
                keep_default_na=False,
                on_bad_lines='skip',
            )


def download_gkg_files(file_index_df: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for row in file_index_df.itertuples(index=False):
        print(f"[GDELT GKG] download {row.file_timestamp} {row.file_url}")
        response = requests.get(row.file_url, timeout=120)
        response.raise_for_status()
        frame = _read_zipped_tsv(response.content)
        frame["file_timestamp"] = row.file_timestamp
        frame["file_url"] = row.file_url
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=GKG_COLUMNS + ["file_timestamp", "file_url"])
    return pd.concat(frames, ignore_index=True)


def _build_tech_keyword_regex(extra_keywords: list[str] | None = None) -> re.Pattern[str]:
    keywords = list(DEFAULT_TECH_KEYWORDS)
    if extra_keywords:
        keywords.extend([keyword.strip() for keyword in extra_keywords if keyword.strip()])
    escaped = sorted({re.escape(keyword.lower()) for keyword in keywords}, key=len, reverse=True)
    return re.compile("|".join(escaped), re.IGNORECASE)


def filter_tech_gkg_records(df: pd.DataFrame, extra_keywords: list[str] | None = None) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    tech_re = _build_tech_keyword_regex(extra_keywords)
    working = df.copy()
    signal = (
        _safe_series(working, "enhanced_themes") + " "
        + _safe_series(working, "themes") + " "
        + _safe_series(working, "v2_organizations") + " "
        + _safe_series(working, "organizations") + " "
        + _safe_series(working, "v2_persons") + " "
        + _safe_series(working, "persons") + " "
        + _safe_series(working, "document_identifier") + " "
        + _safe_series(working, "source_common_name") + " "
        + _safe_series(working, "gcam")
    )
    working["is_tech_candidate"] = signal.str.contains(tech_re, na=False)
    filtered = working.loc[working["is_tech_candidate"]].copy()
    return filtered.drop_duplicates(subset=["gkg_record_id", "document_identifier", "file_timestamp"])


def _slug_to_title(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rsplit("/", 1)[-1]
    path = URL_TOKEN_SPLIT_RE.sub(" ", path)
    path = NON_ALNUM_RE.sub(" ", path)
    return MULTISPACE_RE.sub(" ", path).strip()


def _normalize_multi_value(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.replace(r"[#,;|]", " ", regex=True)
        .str.replace(r"<[^>]+>", " ", regex=True)
        .str.replace(MULTISPACE_RE, " ", regex=True)
        .str.strip()
    )


def normalize_gkg_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=DEFAULT_COLUMNS)

    normalized = pd.DataFrame(index=df.index)
    normalized["source"] = "GDELT"
    normalized["url"] = _safe_series(df, "document_identifier")
    normalized["domain"] = normalized["url"].map(lambda url: urlparse(url).netloc.lower())
    normalized["source_common_name"] = _safe_series(df, "source_common_name")
    normalized["document_identifier"] = _safe_series(df, "document_identifier")
    normalized["themes"] = _normalize_multi_value(_safe_series(df, "enhanced_themes"))
    normalized["persons"] = _normalize_multi_value(_safe_series(df, "v2_persons"))
    normalized["organizations"] = _normalize_multi_value(_safe_series(df, "v2_organizations"))
    normalized["locations"] = _normalize_multi_value(_safe_series(df, "v2_locations"))
    normalized["tone"] = _safe_series(df, "tone")
    normalized["gcam"] = _safe_series(df, "gcam")
    normalized["file_timestamp"] = _safe_series(df, "file_timestamp")
    normalized["file_url"] = _safe_series(df, "file_url")
    normalized["published_at"] = _safe_series(df, "date")

    inferred_title = normalized["url"].map(_slug_to_title)
    normalized["title"] = inferred_title.where(inferred_title.ne(""), normalized["source_common_name"])
    normalized["description"] = (
        "source=" + normalized["source_common_name"]
        + "; domain=" + normalized["domain"]
        + "; themes=" + normalized["themes"]
    )
    normalized["content"] = (
        "organizations=" + normalized["organizations"]
        + "; persons=" + normalized["persons"]
        + "; locations=" + normalized["locations"]
        + "; tone=" + normalized["tone"]
        + "; gcam=" + normalized["gcam"]
    )

    return normalized[DEFAULT_COLUMNS]


def main() -> None:
    parser = argparse.ArgumentParser(description="Download and preprocess raw GDELT GKG files for tech-news trend analysis")
    parser.add_argument("--start-datetime", default="20260301000000", help="UTC start datetime (YYYYMMDD or YYYYMMDDHHMMSS)")
    parser.add_argument("--end-datetime", default="20260302000000", help="UTC end datetime (YYYYMMDD or YYYYMMDDHHMMSS)")
    parser.add_argument("--max-files", type=int, default=96, help="maximum number of 15-minute GKG files to download")
    parser.add_argument("--extra-keywords", nargs="*", default=None, help="extra technology keywords for candidate filtering")
    parser.add_argument("--raw-output", default=os.path.join(RAW_DIR, "gdelt_raw_gkg.csv"), help="raw GKG csv path")
    parser.add_argument("--processed-output", default=os.path.join(PROCESSED_DIR, "gdelt_processed.csv"), help="processed csv path")
    args = parser.parse_args()

    print("[1] Build GKG file list")
    file_index_df = list_gkg_file_urls(args.start_datetime, args.end_datetime, max_files=args.max_files)
    print("selected files:", len(file_index_df))

    print("[2] Download GKG raw files")
    raw_df = download_gkg_files(file_index_df)
    print("raw rows:", len(raw_df))
    raw_df.to_csv(args.raw_output, index=False, encoding="utf-8-sig")

    print("[3] Filter technology candidates")
    tech_raw_df = filter_tech_gkg_records(raw_df, extra_keywords=args.extra_keywords)
    print("tech candidate rows:", len(tech_raw_df))

    print("[4] Normalize schema")
    normalized = normalize_gkg_df(tech_raw_df)

    print("[5] Preprocess")
    processed = preprocess_news_df(normalized)
    print("processed rows:", len(processed))
    processed.to_csv(args.processed_output, index=False, encoding="utf-8-sig")

    print("[6] Done")
    print("saved raw      :", args.raw_output)
    print("saved processed:", args.processed_output)


if __name__ == "__main__":
    main()

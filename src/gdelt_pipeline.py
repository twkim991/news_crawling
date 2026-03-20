import argparse
import io
import json
import os
import re
import zipfile
from datetime import datetime, timezone
from urllib.parse import urlparse

import pandas as pd
import requests

from src.common import preprocess_news_df

RAW_DIR = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")
OUTPUT_DIR = "outputs"
MASTERFILELIST_URL = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
GKG_SUFFIX = ".gkg.csv.zip"

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

GKG_COLUMNS = [
    "gkg_record_id",
    "date",
    "source_collection_id",
    "source_common_name",
    "document_identifier",
    "counts",
    "v2_counts",
    "themes",
    "enhanced_themes",
    "locations",
    "v2_locations",
    "persons",
    "v2_persons",
    "organizations",
    "v2_organizations",
    "tone",
    "enhanced_dates",
    "gcam",
    "sharing_image",
    "related_images",
    "social_image_embeds",
    "social_video_embeds",
    "quotations",
    "all_names",
    "amounts",
    "translation_info",
    "extras_xml",
]

KEEP_GKG_COLUMNS = [
    "gkg_record_id",
    "date",
    "source_common_name",
    "document_identifier",
    "themes",
    "enhanced_themes",
    "organizations",
    "v2_organizations",
    "tone",
    "extras_xml",
]

DEFAULT_TECH_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "kotlin", "swift", "dart",
    "react", "vue", "angular", "svelte", "next.js", "spring", "django", "fastapi", "express", "nestjs",
    "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy", "openai", "hugging face", "langchain", "mlflow", "kubeflow",
    "postgresql", "mysql", "oracle", "mongodb", "cassandra", "dynamodb", "redis", "memcached", "elasticsearch", "opensearch",
    "aws", "google cloud", "azure", "naver cloud", "docker", "kubernetes",
    "kafka", "spark", "dbt", "github actions", "gitlab ci", "jenkins", "terraform", "ansible", "prometheus", "grafana",
    "github", "gitlab", "jira", "postman", "swagger", "vscode", "intellij",
]

TEXT_DECODE_ATTEMPTS = (
    ("utf-8", "strict"),
    ("utf-8", "replace"),
    ("latin-1", "strict"),
)

URL_TOKEN_SPLIT_RE = re.compile(r"[-_/]+")
NON_ALNUM_RE = re.compile(r"[^0-9A-Za-z가-힣\s]+")
MULTISPACE_RE = re.compile(r"\s+")
PAGE_TITLE_RE = re.compile(r"<PAGE_TITLE>(.*?)</PAGE_TITLE>", re.IGNORECASE | re.DOTALL)

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


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


def _parse_gdelt_published_at(series: pd.Series) -> pd.Series:
    raw = series.fillna("").astype(str).str.strip()
    parsed_14 = pd.to_datetime(raw.where(raw.str.len() == 14), format="%Y%m%d%H%M%S", errors="coerce", utc=True)
    parsed_8 = pd.to_datetime(raw.where(raw.str.len() == 8), format="%Y%m%d", errors="coerce", utc=True)
    parsed = parsed_14.fillna(parsed_8)
    return parsed.dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")


def _safe_domain(url: str) -> str:
    value = str(url).strip()
    if not value:
        return ""
    return urlparse(value).netloc.lower()


def _fetch_masterfile_index() -> pd.DataFrame:
    response = requests.get(MASTERFILELIST_URL, timeout=60)
    response.raise_for_status()

    rows = []
    for line in response.text.splitlines():
        parts = line.strip().split()
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

    mask = index_df["file_timestamp"].between(
        start.strftime("%Y%m%d%H%M%S"),
        end.strftime("%Y%m%d%H%M%S"),
        inclusive="left",
    )
    filtered = index_df.loc[mask].copy()

    if max_files is not None:
        filtered = filtered.head(max_files)

    return filtered.reset_index(drop=True)


def _parse_tsv_text(decoded_text: str) -> pd.DataFrame:
    return pd.read_csv(
        io.StringIO(decoded_text),
        sep="\t",
        names=GKG_COLUMNS,
        dtype=str,
        keep_default_na=False,
        on_bad_lines="skip",
        engine="python",
    )


def _decode_gkg_bytes(raw_bytes: bytes) -> tuple[str, str, str]:
    last_error = None

    for encoding, errors in TEXT_DECODE_ATTEMPTS:
        try:
            decoded = raw_bytes.decode(encoding, errors=errors)
            return decoded, encoding, errors
        except UnicodeDecodeError as exc:
            last_error = exc

    raise UnicodeDecodeError(
        getattr(last_error, "encoding", "unknown"),
        getattr(last_error, "object", raw_bytes),
        getattr(last_error, "start", 0),
        getattr(last_error, "end", 1),
        getattr(last_error, "reason", "Failed to decode GDELT bytes"),
    )


def _read_zipped_tsv(content: bytes) -> tuple[pd.DataFrame, dict]:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        members = [name for name in archive.namelist() if name.endswith(".csv")]
        if not members:
            raise ValueError("No CSV file found inside GDELT archive")

        with archive.open(members[0]) as fp:
            raw_bytes = fp.read()

    decoded_text, encoding, errors = _decode_gkg_bytes(raw_bytes)
    frame = _parse_tsv_text(decoded_text)

    decode_meta = {
        "archive_member": members[0],
        "encoding": encoding,
        "errors": errors,
        "byte_length": len(raw_bytes),
    }
    return frame, decode_meta


def _shrink_gkg_frame(frame: pd.DataFrame) -> pd.DataFrame:
    available = [col for col in KEEP_GKG_COLUMNS if col in frame.columns]
    return frame[available].copy()


def download_gkg_files(file_index_df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    frames: list[pd.DataFrame] = []
    failures: list[dict] = []
    fallback_count = 0

    for row in file_index_df.itertuples(index=False):
        print(f"[GDELT GKG] download {row.file_timestamp} {row.file_url}")

        try:
            response = requests.get(row.file_url, timeout=120)
            response.raise_for_status()

            frame, decode_meta = _read_zipped_tsv(response.content)
            frame = _shrink_gkg_frame(frame)

            frame["file_timestamp"] = row.file_timestamp
            frame["file_url"] = row.file_url
            frame["decoded_encoding"] = decode_meta["encoding"]
            frame["decode_errors"] = decode_meta["errors"]

            frames.append(frame)

            if not (decode_meta["encoding"] == "utf-8" and decode_meta["errors"] == "strict"):
                fallback_count += 1
                print(
                    "[GDELT GKG] decode fallback "
                    f"encoding={decode_meta['encoding']} errors={decode_meta['errors']} member={decode_meta['archive_member']}"
                )

        except Exception as exc:
            failures.append({
                "file_timestamp": row.file_timestamp,
                "file_url": row.file_url,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            })
            print(f"[GDELT GKG] skip failed file {row.file_timestamp}: {type(exc).__name__}: {exc}")

    print(f"[GDELT GKG] downloaded={len(frames)} failed={len(failures)} decode_fallbacks={fallback_count}")

    if not frames:
        empty_columns = KEEP_GKG_COLUMNS + ["file_timestamp", "file_url", "decoded_encoding", "decode_errors"]
        return pd.DataFrame(columns=empty_columns), failures

    return pd.concat(frames, ignore_index=True), failures


def _build_keyword_pattern(keyword: str) -> str:
    normalized = keyword.lower().strip()
    escaped = re.escape(normalized).replace(r"\ ", r"\s+")
    if re.fullmatch(r"[a-z0-9\.\+#\-\s]+", normalized):
        return rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
    return escaped


def _build_tech_keyword_regex(extra_keywords: list[str] | None = None) -> re.Pattern[str]:
    keywords = list(DEFAULT_TECH_KEYWORDS)
    if extra_keywords:
        keywords.extend([keyword.strip() for keyword in extra_keywords if keyword.strip()])

    unique_keywords = sorted({k.lower().strip() for k in keywords if k.strip()}, key=len, reverse=True)
    parts = [_build_keyword_pattern(keyword) for keyword in unique_keywords]
    return re.compile("|".join(parts), re.IGNORECASE)


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
        + _safe_series(working, "document_identifier") + " "
        + _safe_series(working, "source_common_name")
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


def _extract_page_title(extras_xml: str) -> str:
    value = str(extras_xml).strip()
    if not value:
        return ""

    match = PAGE_TITLE_RE.search(value)
    if not match:
        return ""

    title = match.group(1)
    title = re.sub(r"<[^>]+>", " ", title)
    title = MULTISPACE_RE.sub(" ", title).strip()
    return title


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
    normalized["domain"] = normalized["url"].map(_safe_domain)
    normalized["source_common_name"] = _safe_series(df, "source_common_name")
    normalized["document_identifier"] = _safe_series(df, "document_identifier")

    enhanced_themes = _normalize_multi_value(_safe_series(df, "enhanced_themes"))
    base_themes = _normalize_multi_value(_safe_series(df, "themes"))
    normalized["themes"] = enhanced_themes.where(enhanced_themes.ne(""), base_themes)

    v2_orgs = _normalize_multi_value(_safe_series(df, "v2_organizations"))
    base_orgs = _normalize_multi_value(_safe_series(df, "organizations"))
    normalized["organizations"] = v2_orgs.where(v2_orgs.ne(""), base_orgs)

    normalized["tone"] = _safe_series(df, "tone")
    normalized["file_timestamp"] = _safe_series(df, "file_timestamp")
    normalized["published_at"] = _parse_gdelt_published_at(_safe_series(df, "date"))

    page_title = _safe_series(df, "extras_xml").map(_extract_page_title)
    inferred_title = normalized["url"].map(_slug_to_title)
    fallback_title = normalized["source_common_name"].where(
        normalized["source_common_name"].str.strip().ne(""),
        normalized["themes"].str.slice(0, 120),
    )
    normalized["title"] = page_title.where(
        page_title.ne(""),
        inferred_title.where(inferred_title.ne(""), fallback_title),
    )

    print(normalized[["url", "title"]].head(10).to_dict(orient="records"))

    normalized["description"] = normalized["themes"]
    normalized["content"] = normalized["organizations"]

    return normalized[DEFAULT_COLUMNS]


def _write_failure_report(failures: list[dict], path: str) -> None:
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    with open(path, "w", encoding="utf-8") as fp:
        json.dump(failures, fp, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and preprocess raw GDELT GKG files for tech-news trend analysis"
    )
    parser.add_argument("--start-datetime", default="20260301000000", help="UTC start datetime (YYYYMMDD or YYYYMMDDHHMMSS)")
    parser.add_argument("--end-datetime", default="20260302000000", help="UTC end datetime (YYYYMMDD or YYYYMMDDHHMMSS)")
    parser.add_argument("--max-files", type=int, default=96, help="maximum number of 15-minute GKG files to download")
    parser.add_argument("--extra-keywords", nargs="*", default=None, help="extra technology keywords for candidate filtering")
    parser.add_argument("--raw-output", default=os.path.join(RAW_DIR, "gdelt_raw_gkg.csv"), help="raw GKG csv path")
    parser.add_argument("--processed-output", default=os.path.join(PROCESSED_DIR, "gdelt_processed.csv"), help="processed csv path")
    parser.add_argument("--failure-log", default=os.path.join(OUTPUT_DIR, "gdelt_failed_files.json"), help="json path for failed download/decode records")
    args = parser.parse_args()

    print("[1] Build GKG file list")
    file_index_df = list_gkg_file_urls(
        args.start_datetime,
        args.end_datetime,
        max_files=args.max_files,
    )
    print("selected files:", len(file_index_df))

    print("[2] Download GKG raw files")
    raw_df, failures = download_gkg_files(file_index_df)
    print("raw rows:", len(raw_df))
    print("raw columns:", list(raw_df.columns))

    raw_df.to_csv(args.raw_output, index=False, encoding="utf-8-sig")
    _write_failure_report(failures, args.failure_log)

    print("failed files:", len(failures))
    print("failure log:", args.failure_log)

    print("[3] Filter technology candidates")
    tech_raw_df = filter_tech_gkg_records(raw_df, extra_keywords=args.extra_keywords)
    print("tech candidate rows:", len(tech_raw_df))

    print("[4] Normalize schema")
    normalized = normalize_gkg_df(tech_raw_df)
    print("normalized rows:", len(normalized))
    print("normalized columns:", list(normalized.columns))
    print("published_at sample:", normalized["published_at"].head(5).tolist())

    print("[5] Preprocess")
    processed = preprocess_news_df(normalized)
    print("processed rows:", len(processed))
    processed.to_csv(args.processed_output, index=False, encoding="utf-8-sig")

    print("[6] Done")
    print("saved raw      :", args.raw_output)
    print("saved processed:", args.processed_output)


if __name__ == "__main__":
    main()
# src/load_reference_items_to_postgres.py

import glob
import os
from typing import Iterable

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

SOURCE_DIRS = [
    "outputs/gdelt",
    "outputs/newsapi",
    "outputs/geeknews",
    "outputs/ssafy_dataset",
]

SOURCE_TYPE_ID = 2
REQUIRED_COLUMNS = ["title", "url", "published_at"]


def _safe_read_csv(path: str) -> pd.DataFrame | None:
    if not os.path.exists(path):
        return None

    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except pd.errors.EmptyDataError:
        return None

    if df.empty:
        return None

    return df


def _get_tracked_only_csv_files(source_dirs: Iterable[str]) -> list[str]:
    files = []

    for source_dir in source_dirs:
        pattern = os.path.join(source_dir, "*", "*_classified_tracked_only.csv")
        files.extend(glob.glob(pattern))

    return sorted(files)


def _normalize_reference_items(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in working.columns]
    if missing_cols:
        raise ValueError(f"필수 컬럼이 없습니다: {missing_cols}")

    working = working[REQUIRED_COLUMNS].copy()

    working["title"] = working["title"].fillna("").astype(str).str.strip()
    working["url"] = working["url"].fillna("").astype(str).str.strip()
    working["published_at"] = working["published_at"].fillna("").astype(str).str.strip()

    working = working.loc[
        working["title"].ne("")
        & working["url"].ne("")
        & working["published_at"].ne("")
    ].copy()

    if working.empty:
        return working

    working["published_at"] = pd.to_datetime(
        working["published_at"],
        errors="coerce",
        utc=True,
    )

    working = working.loc[working["published_at"].notna()].copy()

    if working.empty:
        return working

    working = working.drop_duplicates(
        subset=["title", "url", "published_at"]
    ).reset_index(drop=True)

    return working


def _build_insert_rows(df: pd.DataFrame) -> list[tuple]:
    rows = []

    for _, row in df.iterrows():
        rows.append(
            (
                SOURCE_TYPE_ID,
                row["title"],
                row["url"],
                row["published_at"].to_pydatetime(),
            )
        )

    return rows


def insert_reference_items(conn, rows: list[tuple]) -> int:
    if not rows:
        return 0

    sql = """
        INSERT INTO reference_items (
            source_type_id,
            title,
            url,
            published_at
        )
        SELECT
            v.source_type_id,
            v.title,
            v.url,
            v.published_at
        FROM (
            VALUES %s
        ) AS v(source_type_id, title, url, published_at)
        WHERE NOT EXISTS (
            SELECT 1
            FROM reference_items r
            WHERE r.source_type_id = v.source_type_id
              AND r.url = v.url
              AND r.published_at = v.published_at
        )
    """

    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=1000)

    conn.commit()
    return len(rows)


def process_one_file(conn, file_path: str) -> None:
    print(f"[LOAD] file={file_path}")

    df = _safe_read_csv(file_path)
    if df is None:
        print(f"[SKIP] empty or unreadable file: {file_path}")
        return

    normalized = _normalize_reference_items(df)
    if normalized.empty:
        print(f"[SKIP] no valid reference rows: {file_path}")
        return

    rows = _build_insert_rows(normalized)
    requested_count = len(rows)

    before_count = _count_reference_items(conn)

    insert_reference_items(conn, rows)

    after_count = _count_reference_items(conn)
    inserted_count = after_count - before_count

    print(f"[DONE] requested={requested_count}, inserted={inserted_count}, skipped_duplicate={requested_count - inserted_count}")


def _count_reference_items(conn) -> int:
    sql = "SELECT COUNT(*) FROM reference_items"
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchone()[0]


def main():
    files = _get_tracked_only_csv_files(SOURCE_DIRS)

    if not files:
        print("[LOAD] no tracked_only csv files found")
        return

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        print(f"[LOAD] file count = {len(files)}")
        for file_path in files:
            process_one_file(conn, file_path)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
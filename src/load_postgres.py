# src/load_news_scores_to_postgres.py

import glob
import os
import re
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = os.getenv("DB_CONFIG")
FINAL_DIR = "outputs/final"
FILE_DATE_PATTERN = re.compile(r"final_14d_stack_trend_scores_(\d{4}_\d{2}_\d{2})\.csv$")
SCORE_QUANT = Decimal("0.001")


def quantize_3(value):
    if pd.isna(value):
        return None
    return Decimal(str(value)).quantize(SCORE_QUANT, rounding=ROUND_HALF_UP)


def parse_run_date_from_filename(file_path: str) -> datetime.date:
    file_name = os.path.basename(file_path)
    match = FILE_DATE_PATTERN.fullmatch(file_name)
    if not match:
        raise ValueError(f"지원하지 않는 파일명 형식입니다: {file_name}")

    return datetime.strptime(match.group(1), "%Y_%m_%d").date()


def get_collection_period_from_sunday_file(file_path: str):
    run_date = parse_run_date_from_filename(file_path)

    # 월요일=0, ..., 일요일=6
    if run_date.weekday() != 6:
        return None

    # 예:
    # 2026-03-29(일) -> 2026-03-23(월)
    return run_date - timedelta(days=6)


def load_stack_name_to_id_map(conn) -> dict[str, int]:
    sql = """
        SELECT stack_id, stack_name
        FROM stacks
    """
    with conn.cursor() as cur:
        cur.execute(sql)
        rows = cur.fetchall()

    result = {}
    for stack_id, stack_name in rows:
        if stack_name is None:
            continue
        result[str(stack_name).strip()] = stack_id
    return result


def build_upsert_rows(df: pd.DataFrame, stack_name_to_id: dict[str, int], collection_period):
    rows = []
    missing_stack_names = []

    for _, row in df.iterrows():
        stack_name = str(row.get("stack_name", "")).strip()
        if not stack_name:
            continue

        stack_id = stack_name_to_id.get(stack_name)
        if stack_id is None:
            missing_stack_names.append(stack_name)
            continue

        score_news = quantize_3(row.get("trend_score_30"))

        rows.append(
            (
                stack_id,
                collection_period,
                score_news,
            )
        )

    return rows, sorted(set(missing_stack_names))


def upsert_score_news(conn, rows):
    if not rows:
        return 0

    sql = """
        INSERT INTO stack_score_history (
            stack_id,
            collection_period,
            score_news
        )
        VALUES %s
        ON CONFLICT (stack_id, collection_period)
        DO UPDATE SET
            score_news = EXCLUDED.score_news
    """

    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=1000)

    conn.commit()
    return len(rows)


def process_one_file(conn, file_path: str, stack_name_to_id: dict[str, int]):
    collection_period = get_collection_period_from_sunday_file(file_path)
    if collection_period is None:
        print(f"[SKIP] not sunday final file: {file_path}")
        return

    print(f"[LOAD] file={file_path}")
    print(f"[LOAD] collection_period={collection_period}")

    df = pd.read_csv(file_path, encoding="utf-8-sig")

    if df.empty:
        print(f"[SKIP] empty file: {file_path}")
        return

    required_cols = ["stack_name", "trend_score_30"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"필수 컬럼이 없습니다: {missing_cols}")

    rows, missing_stack_names = build_upsert_rows(
        df=df,
        stack_name_to_id=stack_name_to_id,
        collection_period=collection_period,
    )

    if missing_stack_names:
        print("[WARN] stacks 테이블에서 못 찾은 stack_name:")
        for name in missing_stack_names:
            print(f"  - {name}")

    affected = upsert_score_news(conn, rows)
    print(f"[DONE] inserted/updated rows = {affected}")


def get_final_csv_files():
    pattern = os.path.join(FINAL_DIR, "final_14d_stack_trend_scores_*.csv")
    return sorted(glob.glob(pattern))


def main():
    files = get_final_csv_files()
    if not files:
        print("[LOAD] no final csv files found")
        return

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        stack_name_to_id = load_stack_name_to_id_map(conn)
        print(f"[LOAD] loaded stack map count = {len(stack_name_to_id)}")

        for file_path in files:
            process_one_file(conn, file_path, stack_name_to_id)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
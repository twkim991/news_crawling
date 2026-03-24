# pipeline.py

import argparse
import os
from datetime import datetime, timedelta, timezone

# 각 파이프라인 import (수정 후 사용 가능)
from src.gdelt_pipeline import run_gdelt_collection
from src.gdelt_analysis_pipeline import run_gdelt_analysis
from src.newsapi_pipeline import run_newsapi_collection
from src.newsapi_analysis_pipeline import run_newsapi_analysis


def _resolve_default_run_date() -> str:
    now_utc = datetime.now(timezone.utc)
    target_date = (now_utc - timedelta(days=1)).date()
    return target_date.strftime("%Y-%m-%d")


def _date_to_suffix(run_date: str) -> str:
    return run_date.replace("-", "_")


def run_daily_pipeline(run_date: str):
    print("======================================")
    print(" DAILY TECH NEWS PIPELINE START ")
    print(" run_date:", run_date)
    print("======================================")

    suffix = _date_to_suffix(run_date)

    # -----------------------------
    # 1. GDELT 수집
    # -----------------------------
    gdelt_processed_path = f"data/processed/gdelt_processed_{suffix}.csv"
    gdelt_raw_path = f"data/raw/gdelt_raw_{suffix}.csv"
    gdelt_failure_log = f"outputs/gdelt_failed_{suffix}.json"

    print("\n[STEP 1] GDELT COLLECTION")
    run_gdelt_collection(
        processed_output=gdelt_processed_path,
        raw_output=gdelt_raw_path,
        failure_log=gdelt_failure_log,
    )

    # -----------------------------
    # 2. GDELT 분석
    # -----------------------------
    gdelt_output_dir = f"outputs/gdelt/{suffix}"

    print("\n[STEP 2] GDELT ANALYSIS")
    run_gdelt_analysis(
        input_path=gdelt_processed_path,
        output_dir=gdelt_output_dir,
        output_prefix=f"gdelt_{suffix}",
    )

    # -----------------------------
    # 3. NewsAPI 수집
    # -----------------------------
    newsapi_processed_path = f"data/processed/newsapi_processed_{suffix}.csv"

    print("\n[STEP 3] NEWSAPI COLLECTION")
    run_newsapi_collection(
        from_date=run_date,
        to_date=run_date,
        output_path=newsapi_processed_path,
    )

    # -----------------------------
    # 4. NewsAPI 분석
    # -----------------------------
    newsapi_output_dir = f"outputs/newsapi/{suffix}"

    print("\n[STEP 4] NEWSAPI ANALYSIS")
    run_newsapi_analysis(
        input_path=newsapi_processed_path,
        output_dir=newsapi_output_dir,
        output_prefix=f"newsapi_{suffix}",
    )

    print("\n======================================")
    print(" DAILY PIPELINE DONE ")
    print("======================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily news pipeline orchestrator")
    parser.add_argument(
        "--run-date",
        default=None,
        help="target date (YYYY-MM-DD), default = yesterday UTC",
    )
    args = parser.parse_args()

    run_date = args.run_date or _resolve_default_run_date()

    run_daily_pipeline(run_date)
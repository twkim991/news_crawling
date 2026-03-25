# pipeline.py

import argparse
import os
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

# 각 파이프라인 import (수정 후 사용 가능)
from src.gdelt_pipeline import run_gdelt_collection
from src.gdelt_analysis_pipeline import run_gdelt_analysis
from src.newsapi_pipeline import run_newsapi_collection
from src.newsapi_analysis_pipeline import run_newsapi_analysis

SCORE_DECIMALS = 3


def _resolve_default_run_date() -> str:
    now_utc = datetime.now(timezone.utc)
    target_date = (now_utc - timedelta(days=1)).date()
    return target_date.strftime("%Y-%m-%d")


def _date_to_suffix(run_date: str) -> str:
    return run_date.replace("-", "_")


FINAL_TREND_COLUMNS = [
    "period_type",
    "period_value",
    "stack_category",
    "stack_subgroup",
    "stack_name",
    "article_count",
    "unique_article_count",
    "weighted_article_sum",
    "period_total_weight",
    "share_ratio",
    "avg_binary_score",
    "event_hit_count",
    "event_ratio",
    "share_score",
    "volume_score",
    "event_score",
    "confidence_score",
    "trend_score_raw",
    "trend_score_30",
    "previous_trend_score_30",
    "score_delta",
    "score_delta_pct",
]


def _empty_final_trend_df() -> pd.DataFrame:
    return pd.DataFrame(columns=FINAL_TREND_COLUMNS)


def _safe_read_csv(path: str) -> pd.DataFrame | None:
    if not os.path.exists(path):
        return None

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return None

    if df.empty:
        return None

    return df


def _build_14d_final_trend_scores(
    run_date: str,
    lookback_days: int = 7,
    output_dir: str = "outputs/final",
) -> str:
    os.makedirs(output_dir, exist_ok=True)

    run_date_dt = datetime.strptime(run_date, "%Y-%m-%d")
    collected_frames = []

    for offset in range(lookback_days):
        target_dt = run_date_dt - timedelta(days=offset)
        target_suffix = target_dt.strftime("%Y_%m_%d")

        candidate_files = [
            (
                "newsapi",
                f"outputs/newsapi/{target_suffix}/newsapi_{target_suffix}_daily_stack_trend_scores.csv",
            ),
            (
                "gdelt",
                f"outputs/gdelt/{target_suffix}/gdelt_{target_suffix}_daily_stack_trend_scores.csv",
            ),
        ]

        for source_name, file_path in candidate_files:
            df = _safe_read_csv(file_path)
            if df is None:
                continue

            working = df.copy()
            working["source_name"] = source_name
            working["source_file_date"] = target_dt.strftime("%Y-%m-%d")
            collected_frames.append(working)

    start_date = (run_date_dt - timedelta(days=lookback_days - 1)).strftime("%Y-%m-%d")
    end_date = run_date_dt.strftime("%Y-%m-%d")

    output_path = os.path.join(
        output_dir,
        f"final_7d_stack_trend_scores_{_date_to_suffix(run_date)}.csv",
    )

    if not collected_frames:
        empty_df = _empty_final_trend_df()
        empty_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"[FINAL TREND] No input daily trend files found. Saved empty file: {output_path}")
        return output_path

    merged = pd.concat(collected_frames, ignore_index=True)

    required_cols = [
        "stack_category",
        "stack_subgroup",
        "stack_name",
        "article_count",
        "unique_article_count",
        "weighted_article_sum",
        "avg_binary_score",
        "event_hit_count",
    ]
    missing_cols = [col for col in required_cols if col not in merged.columns]
    if missing_cols:
        raise ValueError(f"final trend aggregation failed. missing columns: {missing_cols}")

    merged["article_count"] = pd.to_numeric(merged["article_count"], errors="coerce").fillna(0.0)
    merged["unique_article_count"] = pd.to_numeric(merged["unique_article_count"], errors="coerce").fillna(0.0)
    merged["weighted_article_sum"] = pd.to_numeric(merged["weighted_article_sum"], errors="coerce").fillna(0.0)
    merged["avg_binary_score"] = pd.to_numeric(merged["avg_binary_score"], errors="coerce").fillna(0.0)
    merged["event_hit_count"] = pd.to_numeric(merged["event_hit_count"], errors="coerce").fillna(0.0)

    merged["confidence_numerator"] = merged["avg_binary_score"] * merged["article_count"]

    grouped = (
        merged.groupby(
            ["stack_category", "stack_subgroup", "stack_name"],
            dropna=False,
            as_index=False,
        )
        .agg(
            article_count=("article_count", "sum"),
            unique_article_count=("unique_article_count", "sum"),
            weighted_article_sum=("weighted_article_sum", "sum"),
            event_hit_count=("event_hit_count", "sum"),
            confidence_numerator=("confidence_numerator", "sum"),
        )
    )

    grouped["period_type"] = "rolling_14d"
    grouped["period_value"] = f"{start_date}~{end_date}"

    grouped["avg_binary_score"] = np.where(
        grouped["article_count"] > 0,
        grouped["confidence_numerator"] / grouped["article_count"],
        0.0,
    )

    period_total_weight = grouped["weighted_article_sum"].sum()
    grouped["period_total_weight"] = period_total_weight

    grouped["share_ratio"] = np.where(
        grouped["period_total_weight"] > 0,
        grouped["weighted_article_sum"] / grouped["period_total_weight"],
        0.0,
    )
    grouped["event_ratio"] = np.where(
        grouped["article_count"] > 0,
        grouped["event_hit_count"] / grouped["article_count"],
        0.0,
    )

    # 14일 집계용 volume 기준치.
    # 기존 daily=5, weekly=20, monthly=60 사이의 중간값 성격으로 30 사용.
    volume_ref = 30.0

    grouped["share_score"] = (grouped["share_ratio"] * 18.0).round(SCORE_DECIMALS)
    grouped["volume_score"] = (
        np.minimum(grouped["article_count"] / volume_ref, 1.0) * 8.0
    ).round(SCORE_DECIMALS)
    grouped["event_score"] = (
        np.minimum(grouped["event_ratio"], 1.0) * 2.0
    ).round(SCORE_DECIMALS)
    grouped["confidence_score"] = (
        np.minimum(grouped["avg_binary_score"], 1.0) * 2.0
    ).round(SCORE_DECIMALS)

    grouped["trend_score_raw"] = (
        grouped["share_score"]
        + grouped["volume_score"]
        + grouped["event_score"]
        + grouped["confidence_score"]
    )
    grouped["trend_score_30"] = grouped["trend_score_raw"].clip(upper=30.0).round(14)

    grouped["previous_trend_score_30"] = np.nan
    grouped["score_delta"] = np.nan
    grouped["score_delta_pct"] = np.nan

    final_df = grouped[
        [
            "period_type",
            "period_value",
            "stack_category",
            "stack_subgroup",
            "stack_name",
            "article_count",
            "unique_article_count",
            "weighted_article_sum",
            "period_total_weight",
            "share_ratio",
            "avg_binary_score",
            "event_hit_count",
            "event_ratio",
            "share_score",
            "volume_score",
            "event_score",
            "confidence_score",
            "trend_score_raw",
            "trend_score_30",
            "previous_trend_score_30",
            "score_delta",
            "score_delta_pct",
        ]
    ].sort_values(
        ["trend_score_30", "weighted_article_sum", "stack_name"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    final_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[FINAL TREND] Saved: {output_path}")

    return output_path


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

    run_date_dt = datetime.strptime(run_date, "%Y-%m-%d")
    start_datetime = run_date_dt.strftime("%Y%m%d000000")
    end_datetime = (run_date_dt + timedelta(days=1)).strftime("%Y%m%d000000")

    print("\n[STEP 1] GDELT COLLECTION")
    run_gdelt_collection(
        processed_output=gdelt_processed_path,
        raw_output=gdelt_raw_path,
        failure_log=gdelt_failure_log,
        start_datetime=start_datetime,     
        end_datetime=end_datetime,
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
    newsapi_raw_path = f"data/raw/newsapi_raw_{suffix}.csv"
    newsapi_processed_path = f"data/processed/newsapi_processed_{suffix}.csv"

    print("\n[STEP 3] NEWSAPI COLLECTION")
    run_newsapi_collection(
        from_date=run_date,
        to_date=run_date,
        page_size=100,
        max_pages=1,
        raw_output=newsapi_raw_path,
        output_path=newsapi_processed_path,
        continue_on_error=False,
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


    # -----------------------------
    # 5. 최근 14일 최종 트렌드 점수 생성
    # -----------------------------
    print("\n[STEP 5] FINAL 14-DAY TREND AGGREGATION")
    final_output_path = _build_14d_final_trend_scores(
        run_date=run_date,
        lookback_days=7,
        output_dir="outputs/final",
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
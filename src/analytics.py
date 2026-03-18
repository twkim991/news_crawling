import json
import os
from datetime import datetime, timezone

import pandas as pd


def _normalize_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", utc=True)


def build_run_metadata(df: pd.DataFrame, tech_df: pd.DataFrame, *, input_sources: list[str], model_path: str, output_dir: str, thresholds: dict) -> dict:
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_sources": input_sources,
        "model_path": model_path,
        "output_dir": output_dir,
        "thresholds": thresholds,
        "rows": {
            "input": int(len(df)),
            "tech": int(len(tech_df)),
            "tech_ratio": float(len(tech_df) / len(df)) if len(df) else 0.0,
        },
        "source_distribution": df["source"].astype(str).value_counts().to_dict() if not df.empty else {},
        "tech_source_distribution": tech_df["source"].astype(str).value_counts().to_dict() if not tech_df.empty else {},
        "tech_category_distribution": tech_df["tech_category"].astype(str).value_counts().to_dict() if "tech_category" in tech_df else {},
    }
    return metadata


def save_run_metadata(metadata: dict, output_path: str) -> None:
    folder = os.path.dirname(output_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(metadata, fp, ensure_ascii=False, indent=2)


def build_trend_reports(tech_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if tech_df.empty or "published_at" not in tech_df.columns:
        empty = pd.DataFrame(columns=["period", "tech_category", "article_count"])
        return {"weekly": empty, "monthly": empty}

    base = tech_df.copy()
    base["published_at"] = _normalize_datetime(base["published_at"])
    dated = base.dropna(subset=["published_at"]).copy()

    if dated.empty:
        empty = pd.DataFrame(columns=["period", "tech_category", "article_count"])
        return {"weekly": empty, "monthly": empty}

    weekly = (
        dated.assign(period=dated["published_at"].dt.to_period("W-MON").astype(str))
        .groupby(["period", "tech_category"], as_index=False)
        .size()
        .rename(columns={"size": "article_count"})
        .sort_values(["period", "article_count", "tech_category"], ascending=[True, False, True])
    )
    monthly = (
        dated.assign(period=dated["published_at"].dt.to_period("M").astype(str))
        .groupby(["period", "tech_category"], as_index=False)
        .size()
        .rename(columns={"size": "article_count"})
        .sort_values(["period", "article_count", "tech_category"], ascending=[True, False, True])
    )
    return {"weekly": weekly, "monthly": monthly}


def save_trend_reports(reports: dict[str, pd.DataFrame], output_dir: str, prefix: str = "tech") -> dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    output_paths = {}
    for name, report_df in reports.items():
        path = os.path.join(output_dir, f"{prefix}_{name}_trends.csv")
        report_df.to_csv(path, index=False, encoding="utf-8-sig")
        output_paths[name] = path
    return output_paths

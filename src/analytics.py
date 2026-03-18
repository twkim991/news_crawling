import json
import os
import re
from collections import Counter
from datetime import datetime, timezone

import pandas as pd

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-\.\+#]{1,}|[가-힣]{2,}")
STOPWORDS = {
    "technology", "tech", "software", "developer", "developers", "platform", "platforms", "news", "says",
    "said", "using", "launch", "launches", "company", "companies", "product", "products", "service", "services",
    "update", "updates", "business", "industry", "market", "markets", "data", "cloud", "ai", "ml",
    "기술", "뉴스", "출시", "기업", "시장", "플랫폼", "서비스", "소프트웨어", "데이터",
}


def _normalize_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", utc=True)


def _share_report(df: pd.DataFrame, group_field: str, period_freq: str, period_name: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["period", group_field, "article_count", "share"])

    grouped = (
        df.assign(period=df["published_at"].dt.to_period(period_freq).astype(str))
        .groupby(["period", group_field], as_index=False)
        .size()
        .rename(columns={"size": "article_count"})
    )
    totals = grouped.groupby("period")["article_count"].transform("sum")
    grouped["share"] = grouped["article_count"] / totals
    grouped["period_type"] = period_name
    return grouped.sort_values(["period", "article_count", group_field], ascending=[True, False, True])


def _growth_report(share_df: pd.DataFrame, entity_field: str) -> pd.DataFrame:
    if share_df.empty:
        return pd.DataFrame(columns=["period", entity_field, "article_count", "share", "share_delta", "count_delta"])

    ordered = share_df.sort_values([entity_field, "period"]).copy()
    ordered["share_delta"] = ordered.groupby(entity_field)["share"].diff().fillna(0.0)
    ordered["count_delta"] = ordered.groupby(entity_field)["article_count"].diff().fillna(0)
    return ordered


def _source_bias_report(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["source", "tech_category", "source_share", "global_share", "lift", "article_count"])

    counts = df.groupby(["source", "tech_category"], as_index=False).size().rename(columns={"size": "article_count"})
    source_totals = counts.groupby("source")["article_count"].transform("sum")
    counts["source_share"] = counts["article_count"] / source_totals

    global_counts = df.groupby("tech_category").size()
    global_share = (global_counts / global_counts.sum()).to_dict()
    counts["global_share"] = counts["tech_category"].map(global_share)
    counts["lift"] = counts["source_share"] / counts["global_share"]
    return counts.sort_values(["lift", "article_count"], ascending=[False, False])


def _extract_keywords(series: pd.Series) -> Counter:
    counter = Counter()
    for text in series.fillna("").astype(str):
        for token in TOKEN_RE.findall(text.lower()):
            if token in STOPWORDS or len(token) < 2:
                continue
            counter[token] += 1
    return counter


def _emerging_keywords_report(df: pd.DataFrame, period_freq: str = "W-MON", top_k: int = 30) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["period", "keyword", "current_count", "previous_count", "delta"])

    working = df.copy()
    working["period"] = working["published_at"].dt.to_period(period_freq).astype(str)
    periods = sorted(working["period"].dropna().unique())
    if len(periods) < 2:
        return pd.DataFrame(columns=["period", "keyword", "current_count", "previous_count", "delta"])

    current_period = periods[-1]
    previous_period = periods[-2]
    current_counter = _extract_keywords(working.loc[working["period"] == current_period, "text"])
    previous_counter = _extract_keywords(working.loc[working["period"] == previous_period, "text"])

    rows = []
    for keyword, current_count in current_counter.items():
        previous_count = previous_counter.get(keyword, 0)
        delta = current_count - previous_count
        if delta > 0:
            rows.append({
                "period": current_period,
                "keyword": keyword,
                "current_count": current_count,
                "previous_count": previous_count,
                "delta": delta,
            })

    report = pd.DataFrame(rows)
    if report.empty:
        return report.reindex(columns=["period", "keyword", "current_count", "previous_count", "delta"])
    return report.sort_values(["delta", "current_count", "keyword"], ascending=[False, False, True]).head(top_k)


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
        "primary_stack_distribution": tech_df["primary_stack"].astype(str).value_counts().to_dict() if "primary_stack" in tech_df else {},
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
        empty_count = pd.DataFrame(columns=["period", "tech_category", "article_count"])
        empty_share = pd.DataFrame(columns=["period", "tech_category", "article_count", "share", "period_type"])
        empty_growth = pd.DataFrame(columns=["period", "tech_category", "article_count", "share", "period_type", "share_delta", "count_delta"])
        empty_bias = pd.DataFrame(columns=["source", "tech_category", "source_share", "global_share", "lift", "article_count"])
        empty_keywords = pd.DataFrame(columns=["period", "keyword", "current_count", "previous_count", "delta"])
        return {
            "category_weekly_counts": empty_count,
            "category_monthly_counts": empty_count.copy(),
            "category_weekly_share": empty_share,
            "category_monthly_share": empty_share.copy(),
            "category_monthly_growth": empty_growth,
            "stack_monthly_share": empty_share.rename(columns={"tech_category": "primary_stack"}),
            "source_bias": empty_bias,
            "emerging_keywords": empty_keywords,
        }

    base = tech_df.copy()
    base["published_at"] = _normalize_datetime(base["published_at"])
    dated = base.dropna(subset=["published_at"]).copy()

    if dated.empty:
        return build_trend_reports(pd.DataFrame())

    category_weekly_counts = (
        dated.assign(period=dated["published_at"].dt.to_period("W-MON").astype(str))
        .groupby(["period", "tech_category"], as_index=False)
        .size()
        .rename(columns={"size": "article_count"})
        .sort_values(["period", "article_count", "tech_category"], ascending=[True, False, True])
    )
    category_monthly_counts = (
        dated.assign(period=dated["published_at"].dt.to_period("M").astype(str))
        .groupby(["period", "tech_category"], as_index=False)
        .size()
        .rename(columns={"size": "article_count"})
        .sort_values(["period", "article_count", "tech_category"], ascending=[True, False, True])
    )

    category_weekly_share = _share_report(dated, "tech_category", "W-MON", "weekly")
    category_monthly_share = _share_report(dated, "tech_category", "M", "monthly")
    category_monthly_growth = _growth_report(category_monthly_share, "tech_category")
    stack_monthly_share = _share_report(dated.assign(primary_stack=dated.get("primary_stack", "Unspecified")), "primary_stack", "M", "monthly")
    source_bias = _source_bias_report(dated)
    emerging_keywords = _emerging_keywords_report(dated)

    return {
        "category_weekly_counts": category_weekly_counts,
        "category_monthly_counts": category_monthly_counts,
        "category_weekly_share": category_weekly_share,
        "category_monthly_share": category_monthly_share,
        "category_monthly_growth": category_monthly_growth,
        "stack_monthly_share": stack_monthly_share,
        "source_bias": source_bias,
        "emerging_keywords": emerging_keywords,
    }


def save_trend_reports(reports: dict[str, pd.DataFrame], output_dir: str, prefix: str = "tech") -> dict[str, str]:
    os.makedirs(output_dir, exist_ok=True)
    output_paths = {}
    for name, report_df in reports.items():
        path = os.path.join(output_dir, f"{prefix}_{name}.csv")
        report_df.to_csv(path, index=False, encoding="utf-8-sig")
        output_paths[name] = path
    return output_paths

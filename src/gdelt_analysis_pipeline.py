# gdelt_analysis_pipeline.py

import argparse
import os
import re
from typing import Iterable

import joblib
import numpy as np
import pandas as pd

from src.common import classify_subcategory, encode_texts, build_text_series
from src.taxonomy import STACK_ALIASES, STACK_EVENT_KEYWORDS

INPUT_PATH = os.path.join("data", "processed", "gdelt_processed.csv")
OUTPUT_DIR = "outputs"
BINARY_MODEL_PATH = os.path.join("models", "ag_binary_logreg.joblib")
BINARY_BATCH_SIZE = 64
BINARY_THRESHOLD = 0.45

os.makedirs(OUTPUT_DIR, exist_ok=True)


def _safe_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column].fillna("").astype(str)
    return pd.Series("", index=df.index, dtype="object")


def _build_text_signal(df: pd.DataFrame) -> pd.Series:
    return (
        _safe_series(df, "title") + " "
        + _safe_series(df, "description") + " "
        + _safe_series(df, "content")
    ).str.strip()


def _year_month_to_suffix(year_month: str) -> str:
    return str(year_month).strip().replace("-", "_")


def _build_keyword_pattern(keyword: str) -> str:
    normalized = keyword.lower().strip()
    escaped = re.escape(normalized).replace(r"\ ", r"\s+")

    if re.fullmatch(r"[a-z0-9\.\+#\-\s]+", normalized):
        return rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"

    return escaped


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    normalized = _normalize_text(text)
    for keyword in keywords:
        if _normalize_text(keyword) in normalized:
            return True
    return False


def _match_stack_aliases_with_rules(
    title_text: str,
    description_text: str,
    content_text: str,
) -> tuple[list[str], dict[str, dict[str, str]]]:
    title_text = _normalize_text(title_text)
    description_text = _normalize_text(description_text)
    content_text = _normalize_text(content_text)
    full_text = f"{title_text} {description_text} {content_text}".strip()

    matched_stacks = []
    debug_map = {}

    for stack_name, info in STACK_ALIASES.items():
        aliases = info.get("aliases", [])
        ambiguous = bool(info.get("ambiguous", False))
        requires_context = bool(info.get("requires_context", False))
        context_keywords = info.get("context_keywords", ())
        negative_keywords = info.get("negative_keywords", ())
        supporting_entities = info.get("supporting_entities", ())
        vendor_signals = info.get("vendor_signals", ())

        alias_hit = False
        title_or_desc_hit = False

        for alias in aliases:
            pattern = _build_keyword_pattern(alias)

            if re.search(pattern, full_text, flags=re.IGNORECASE):
                alias_hit = True

            if (
                re.search(pattern, title_text, flags=re.IGNORECASE)
                or re.search(pattern, description_text, flags=re.IGNORECASE)
            ):
                title_or_desc_hit = True

        if not alias_hit:
            debug_map[stack_name] = {
                "status": "rejected",
                "reason": "no_alias_hit",
            }
            continue

        if not ambiguous:
            matched_stacks.append(stack_name)
            debug_map[stack_name] = {
                "status": "accepted",
                "reason": "non_ambiguous_alias_hit",
            }
            continue

        if negative_keywords and _contains_any(full_text, negative_keywords):
            debug_map[stack_name] = {
                "status": "rejected",
                "reason": "negative_keyword_hit",
            }
            continue

        if not title_or_desc_hit:
            debug_map[stack_name] = {
                "status": "rejected",
                "reason": "content_only_hit",
            }
            continue

        if requires_context:
            has_context = (
                _contains_any(full_text, context_keywords)
                or _contains_any(full_text, supporting_entities)
                or _contains_any(full_text, vendor_signals)
            )
            if not has_context:
                debug_map[stack_name] = {
                    "status": "rejected",
                    "reason": "context_missing",
                }
                continue

        matched_stacks.append(stack_name)
        debug_map[stack_name] = {
            "status": "accepted",
            "reason": "ambiguous_with_context",
        }

    return matched_stacks, debug_map


def _apply_devtech_keyword_gate(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    title_series = _safe_series(working, "title")
    description_series = _safe_series(working, "description")
    content_series = _safe_series(working, "content")

    matched_stack_names = []
    matched_debug_reasons = []
    all_rule_logs = []
    ambiguous_only_flags = []
    gate_pass_flags = []
    rescue_applied_flags = []

    for idx, (title, description, content) in enumerate(
        zip(title_series, description_series, content_series)
    ):
        stacks, debug_map = _match_stack_aliases_with_rules(title, description, content)
        matched_stack_names.append(", ".join(stacks))

        debug_parts = []
        all_parts = []
        ambiguous_only = True if stacks else False

        for stack_name in STACK_ALIASES.keys():
            log = debug_map.get(stack_name, {})
            reason = log.get("reason", "")
            status = log.get("status", "")
            if reason:
                all_parts.append(f"{stack_name}:{status}:{reason}")

        for stack_name in stacks:
            info = STACK_ALIASES.get(stack_name, {})
            if not bool(info.get("ambiguous", False)):
                ambiguous_only = False

            reason = debug_map.get(stack_name, {}).get("reason", "")
            debug_parts.append(f"{stack_name}:{reason}")

        tech_score = float(working.iloc[idx].get("is_tech_score", 0.0))
        rescue_applied = 0

        if not stacks:
            gate_pass = 0
        elif ambiguous_only:
            gate_pass = int(tech_score >= 0.50)
        else:
            gate_pass = 1

        matched_debug_reasons.append(" | ".join(debug_parts))
        all_rule_logs.append(" | ".join(all_parts))
        ambiguous_only_flags.append(int(ambiguous_only))
        gate_pass_flags.append(gate_pass)
        rescue_applied_flags.append(rescue_applied)

    working["devtech_text_signal"] = (
        title_series + " " + description_series + " " + content_series
    ).str.strip()
    working["matched_devtech_aliases"] = matched_stack_names
    working["matched_devtech_reasons"] = matched_debug_reasons
    working["all_devtech_rule_logs"] = all_rule_logs
    working["ambiguous_only_match"] = ambiguous_only_flags
    working["gate_pass_after_stack_rule"] = gate_pass_flags
    working["stack_rescue_applied"] = rescue_applied_flags
    working["is_devtech"] = (
        pd.Series(matched_stack_names).str.strip().ne("")
        & (pd.Series(gate_pass_flags).astype(int) == 1)
    ).astype(int)

    return working


def _apply_binary_tech_classifier(
    df: pd.DataFrame,
    model_path: str,
    batch_size: int = 64,
    threshold: float = 0.5,
) -> pd.DataFrame:
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Binary classifier not found: {model_path}")

    working = df.copy()
    text_signal = _build_text_signal(working)

    print("[GDELT Analysis] Load AG binary classifier")
    clf = joblib.load(model_path)

    print("[GDELT Analysis] Encode texts for binary classification")
    embeddings = encode_texts(text_signal.tolist(), batch_size=batch_size)

    if not isinstance(embeddings, np.ndarray):
        embeddings = np.asarray(embeddings)

    print("[GDELT Analysis] Predict tech / non-tech")
    if hasattr(clf, "predict_proba"):
        proba = clf.predict_proba(embeddings)[:, 1]
        preds = (proba >= threshold).astype(int)
    else:
        preds = clf.predict(embeddings)
        proba = preds.astype(float)

    working["text_signal"] = text_signal
    working["is_tech_score"] = proba
    working["is_tech"] = preds.astype(int)

    return working


def _resolve_date_column(df: pd.DataFrame) -> str | None:
    candidates = [
        "published_at",
        "publishedAt",
        "publish_date",
        "published_date",
        "date",
        "datetime",
        "seendate",
    ]
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _prepare_article_dates(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    date_col = _resolve_date_column(working)
    if date_col is None:
        raise ValueError(
            "날짜 컬럼을 찾지 못했습니다. processed GDELT 파일에 published_at / publishedAt / date / seendate 중 하나는 있어야 합니다."
        )

    working["article_datetime"] = pd.to_datetime(
        working[date_col],
        errors="coerce",
        utc=True,
    )
    working = working.loc[working["article_datetime"].notna()].copy()

    if working.empty:
        return working

    working["article_date"] = working["article_datetime"].dt.strftime("%Y-%m-%d")
    iso_calendar = working["article_datetime"].dt.isocalendar()
    working["article_week"] = (
        iso_calendar["year"].astype(str)
        + "-W"
        + iso_calendar["week"].astype(str).str.zfill(2)
    )
    working["article_month"] = working["article_datetime"].dt.strftime("%Y-%m")

    return working


def _ensure_classification_columns(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    for col, default in [
        ("tech_category", "Other Tech"),
        ("tech_category_score", 0.0),
        ("tech_category_score_gap", 0.0),
        ("top2_category", "Other Tech"),
        ("top2_score", 0.0),
        ("stack_labels", ""),
        ("primary_stack", "Unspecified"),
        ("stack_label_count", 0.0),
    ]:
        if col not in working.columns:
            working[col] = default

    return working


def _finalize_classified_articles(df: pd.DataFrame) -> pd.DataFrame:
    working = _ensure_classification_columns(df)

    working = _prepare_article_dates(working)
    if working.empty:
        return working

    stack_labels = _safe_series(working, "stack_labels").str.strip()
    primary_stack = _safe_series(working, "primary_stack").str.strip()
    tech_category = _safe_series(working, "tech_category").replace("", "Other Tech")

    working["tracked_stack_list"] = stack_labels.apply(
        lambda x: [item.strip() for item in str(x).split("|") if item.strip()]
    )
    working["tracked_stack_count"] = working["tracked_stack_list"].apply(len)

    working["classification_type"] = np.where(
        working["tracked_stack_count"] > 0,
        "tracked_stack",
        "other_tech",
    )
    working["tech_bucket"] = np.where(
        working["tracked_stack_count"] > 0,
        "Tracked Stack",
        "Other Tech",
    )

    working["primary_stack"] = np.where(
        primary_stack.eq("") | primary_stack.eq("Unspecified"),
        np.where(working["tracked_stack_count"] > 0, working["tracked_stack_list"].str[0], "Unspecified"),
        primary_stack,
    )
    working["tech_category"] = np.where(
        working["tracked_stack_count"] > 0,
        tech_category,
        "Other Tech",
    )

    working = working.drop(columns=["tracked_stack_list"], errors="ignore")

    preferred_columns = [
        "article_datetime",
        "article_date",
        "article_week",
        "article_month",
        "classification_type",
        "tech_bucket",
        "tech_category",
        "tech_category_score",
        "tech_category_score_gap",
        "top2_category",
        "top2_score",
        "primary_stack",
        "stack_labels",
        "stack_label_count",
        "matched_devtech_aliases",
        "matched_devtech_reasons",
        "is_tech_score",
        "is_tech",
        "is_devtech",
        "final_is_devtech",
        "title",
        "description",
        "content",
        "url",
        "published_at",
        "source",
    ]

    existing_preferred = [col for col in preferred_columns if col in working.columns]
    remaining = [col for col in working.columns if col not in existing_preferred]

    return (
        working[existing_preferred + remaining]
        .sort_values(["article_datetime", "is_tech_score"], ascending=[True, False])
        .reset_index(drop=True)
    )


def _get_all_tracked_stacks() -> pd.DataFrame:
    rows = []
    for stack_name, info in STACK_ALIASES.items():
        rows.append(
            {
                "stack_name": stack_name,
                "stack_category": info.get("category", ""),
                "stack_subgroup": info.get("subgroup", ""),
            }
        )
    return pd.DataFrame(rows).sort_values(["stack_category", "stack_subgroup", "stack_name"]).reset_index(drop=True)


def _has_event_signal(text: str) -> int:
    normalized = _normalize_text(text)
    return int(any(keyword in normalized for keyword in STACK_EVENT_KEYWORDS))


def _explode_tracked_articles(tracked_df: pd.DataFrame) -> pd.DataFrame:
    if tracked_df.empty:
        return tracked_df.copy()

    working = tracked_df.copy()
    working["stack_list"] = _safe_series(working, "stack_labels").apply(
        lambda x: [item.strip() for item in str(x).split("|") if item.strip()]
    )
    working = working.loc[working["stack_list"].map(len) > 0].copy()

    if working.empty:
        return working

    working["stack_count_for_weight"] = working["stack_list"].map(len)
    working["article_weight"] = 1.0 / working["stack_count_for_weight"]

    text_signal = (
        _safe_series(working, "title") + " "
        + _safe_series(working, "description") + " "
        + _safe_series(working, "content")
    ).str.strip()
    working["event_signal_hit"] = text_signal.apply(_has_event_signal)

    exploded = working.explode("stack_list").rename(columns={"stack_list": "stack_name"})
    exploded["stack_category"] = exploded["stack_name"].map(
        lambda x: STACK_ALIASES.get(x, {}).get("category", "")
    )
    exploded["stack_subgroup"] = exploded["stack_name"].map(
        lambda x: STACK_ALIASES.get(x, {}).get("subgroup", "")
    )

    return exploded.reset_index(drop=True)


def _period_activity_ref(period_type: str) -> int:
    if period_type == "daily":
        return 5
    raise ValueError(f"unknown period_type: {period_type}")


def _build_period_score_rows(
    exploded_df: pd.DataFrame,
    period_col: str,
    period_type: str,
) -> pd.DataFrame:
    if exploded_df.empty:
        return pd.DataFrame()

    all_stacks = _get_all_tracked_stacks()
    all_periods = (
        exploded_df[[period_col]]
        .drop_duplicates()
        .rename(columns={period_col: "period_value"})
        .sort_values("period_value")
        .reset_index(drop=True)
    )

    base_grid = all_periods.assign(_key=1).merge(
        all_stacks.assign(_key=1),
        on="_key",
        how="inner",
    ).drop(columns="_key")

    group_cols = [period_col, "stack_name", "stack_category", "stack_subgroup"]

    agg_spec = {
        "article_count": ("stack_name", "size"),
        "weighted_article_sum": ("article_weight", "sum"),
        "avg_binary_score": ("is_tech_score", "mean"),
        "event_hit_count": ("event_signal_hit", "sum"),
    }

    if "url" in exploded_df.columns:
        agg_spec["unique_article_count"] = ("url", "nunique")
    else:
        agg_spec["unique_article_count"] = ("stack_name", "size")

    grouped = (
        exploded_df.groupby(group_cols, dropna=False)
        .agg(**agg_spec)
        .reset_index()
        .rename(columns={period_col: "period_value"})
    )

    merged = base_grid.merge(
        grouped,
        on=["period_value", "stack_name", "stack_category", "stack_subgroup"],
        how="left",
    )

    for col in [
        "article_count",
        "unique_article_count",
        "weighted_article_sum",
        "avg_binary_score",
        "event_hit_count",
    ]:
        merged[col] = merged[col].fillna(0.0)

    period_totals = (
        merged.groupby("period_value", dropna=False)["weighted_article_sum"]
        .sum()
        .rename("period_total_weight")
        .reset_index()
    )
    merged = merged.merge(period_totals, on="period_value", how="left")

    merged["share_ratio"] = np.where(
        merged["period_total_weight"] > 0,
        merged["weighted_article_sum"] / merged["period_total_weight"],
        0.0,
    )
    merged["event_ratio"] = np.where(
        merged["article_count"] > 0,
        merged["event_hit_count"] / merged["article_count"],
        0.0,
    )

    activity_ref = _period_activity_ref(period_type)

    merged["share_score"] = (merged["share_ratio"] * 18.0).round(4)
    merged["volume_score"] = (
        np.minimum(merged["article_count"] / activity_ref, 1.0) * 8.0
    ).round(4)
    merged["event_score"] = (
        np.minimum(merged["event_ratio"], 1.0) * 2.0
    ).round(4)
    merged["confidence_score"] = (
        np.minimum(merged["avg_binary_score"], 1.0) * 2.0
    ).round(4)

    merged["trend_score_raw"] = (
        merged["share_score"]
        + merged["volume_score"]
        + merged["event_score"]
        + merged["confidence_score"]
    )
    merged["trend_score_30"] = merged["trend_score_raw"].clip(upper=30.0).round(2)
    merged["period_type"] = period_type

    merged = merged.sort_values(["stack_name", "period_value"]).reset_index(drop=True)
    merged["previous_trend_score_30"] = (
        merged.groupby("stack_name")["trend_score_30"].shift(1)
    )
    merged["score_delta"] = (
        merged["trend_score_30"] - merged["previous_trend_score_30"]
    ).round(2)
    merged["score_delta_pct"] = np.where(
        merged["previous_trend_score_30"].fillna(0) > 0,
        (
            (merged["trend_score_30"] - merged["previous_trend_score_30"])
            / merged["previous_trend_score_30"]
            * 100.0
        ).round(2),
        np.nan,
    )

    ordered_cols = [
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
    return merged[ordered_cols]


def _build_daily_stack_trend_scores(tracked_df: pd.DataFrame) -> pd.DataFrame:
    exploded = _explode_tracked_articles(tracked_df)

    empty_columns = [
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

    if exploded.empty:
        return pd.DataFrame(columns=empty_columns)

    daily = _build_period_score_rows(exploded, "article_date", "daily").copy()

    if daily.empty:
        return pd.DataFrame(columns=empty_columns)

    return (
        daily.sort_values(
            ["period_value", "trend_score_30", "stack_name"],
            ascending=[True, False, True],
        )
        .reset_index(drop=True)
    )


def run_gdelt_analysis(
    input_path,
    output_dir,
    output_prefix="gdelt",
    year_month=None,
):
    os.makedirs(output_dir, exist_ok=True)

    print("[GDELT Analysis] Load processed data")
    df = pd.read_csv(input_path)

    print("[GDELT Analysis] Filter empty text rows")
    text_signal = _build_text_signal(df)
    before_rows = len(df)
    df = df.loc[text_signal.ne("")].copy()
    print("rows before filter:", before_rows)
    print("rows after filter :", len(df))

    if df.empty:
        print("[GDELT Analysis] No rows left after filtering. Abort.")
        return None

    print("[GDELT Analysis] Binary tech classification start")
    scored_df = _apply_binary_tech_classifier(
        df,
        model_path=BINARY_MODEL_PATH,
        batch_size=BINARY_BATCH_SIZE,
        threshold=BINARY_THRESHOLD,
    )
    print("[GDELT Analysis] Binary tech classification done")

    print("[GDELT Analysis] Dev-tech keyword gate start")
    gated_df = _apply_devtech_keyword_gate(scored_df)
    print("[GDELT Analysis] Dev-tech keyword gate done")

    gated_df["final_is_devtech"] = (
        (
            (gated_df["is_tech"] == 1) & (gated_df["is_devtech"] == 1)
        ) | (
            (gated_df["is_devtech"] == 1)
            & (gated_df["ambiguous_only_match"] == 0)
            & (gated_df["is_tech_score"] >= 0.30)
        ) | (
            (gated_df["is_tech"] == 1)
            & (gated_df["is_devtech"] == 0)
        )
    ).astype(int)

    tech_df = gated_df.loc[gated_df["final_is_devtech"] == 1].copy()
    print("[GDELT Analysis] Rows kept for final classification:", len(tech_df))

    if tech_df.empty:
        print("[GDELT Analysis] No rows passed final gate. Abort.")
        return None

    if "text" not in tech_df.columns:
        tech_df = tech_df.copy()
        tech_df["text"] = build_text_series(
            _safe_series(tech_df, "title"),
            _safe_series(tech_df, "description"),
            _safe_series(tech_df, "content"),
        )

    print("[GDELT Analysis] Subcategory + stack classification start")
    result_df = classify_subcategory(tech_df)
    print("[GDELT Analysis] Subcategory + stack classification done")

    full_classified_df = _finalize_classified_articles(result_df)
    if full_classified_df.empty:
        print("[GDELT Analysis] No classified rows after date normalization.")
        return None

    tracked_only_df = full_classified_df.loc[
        full_classified_df["tech_bucket"] != "Other Tech"
    ].copy()

    daily_stack_trend_scores_df = _build_daily_stack_trend_scores(tracked_only_df)

    full_output_path = os.path.join(
        output_dir,
        f"{output_prefix}_classified_all.csv",
    )
    tracked_output_path = os.path.join(
        output_dir,
        f"{output_prefix}_classified_tracked_only.csv",
    )
    trend_output_path = os.path.join(
        output_dir,
        f"{output_prefix}_daily_stack_trend_scores.csv",
    )
    debug_output_path = os.path.join(
        output_dir,
        f"{output_prefix}_classified_debug.csv",
    )

    debug_columns = [
        "article_datetime",
        "article_date",
        "article_week",
        "article_month",
        "classification_type",
        "tech_bucket",
        "tech_category",
        "tech_category_score",
        "tech_category_score_gap",
        "top2_category",
        "top2_score",
        "primary_stack",
        "stack_labels",
        "stack_label_count",
        "matched_devtech_aliases",
        "matched_devtech_reasons",
        "all_devtech_rule_logs",
        "ambiguous_only_match",
        "is_tech_score",
        "is_tech",
        "is_devtech",
        "final_is_devtech",
        "title",
        "description",
        "content",
        "url",
        "published_at",
        "source",
    ]
    debug_columns = [col for col in debug_columns if col in full_classified_df.columns]
    debug_df = full_classified_df[debug_columns].copy()

    full_classified_df.to_csv(full_output_path, index=False, encoding="utf-8-sig")
    tracked_only_df.to_csv(tracked_output_path, index=False, encoding="utf-8-sig")
    daily_stack_trend_scores_df.to_csv(trend_output_path, index=False, encoding="utf-8-sig")
    debug_df.to_csv(debug_output_path, index=False, encoding="utf-8-sig")

    print("\nSaved:", full_output_path)
    print("Saved:", tracked_output_path)
    print("Saved:", trend_output_path)

    return {
        "classified_all": full_classified_df,
        "classified_tracked_only": tracked_only_df,
        "daily_stack_trend_scores": daily_stack_trend_scores_df,
        "classified_debug": debug_df,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze processed GDELT tech data and build stack trend scores"
    )
    parser.add_argument("--year-month", default=None, help="month in YYYY-MM format")
    parser.add_argument("--input-path", default=INPUT_PATH, help="processed GDELT csv path")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="directory to save analysis outputs")
    parser.add_argument("--output-prefix", default="gdelt", help="prefix for output file names")
    args = parser.parse_args()

    if args.year_month:
        suffix = _year_month_to_suffix(args.year_month)
        input_path = args.input_path or os.path.join(
            "data",
            "processed",
            f"gdelt_processed_{suffix}.csv",
        )
        output_dir = args.output_dir or os.path.join("outputs", suffix)
        output_prefix = args.output_prefix or f"gdelt_{suffix}"
    else:
        input_path = args.input_path or INPUT_PATH
        output_dir = args.output_dir or OUTPUT_DIR
        output_prefix = args.output_prefix or "gdelt"

    os.makedirs(output_dir, exist_ok=True)

    print("[GDELT Analysis] input_path :", input_path)
    print("[GDELT Analysis] output_dir :", output_dir)
    print("[GDELT Analysis] output_prefix :", output_prefix)

    run_gdelt_analysis(
        input_path=input_path,
        output_dir=output_dir,
        output_prefix=output_prefix,
        year_month=args.year_month,
    )


if __name__ == "__main__":
    main()
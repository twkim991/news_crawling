import argparse
import os
import re

import joblib
import numpy as np
import pandas as pd

from src.analytics import build_trend_reports, save_trend_reports
from src.common import classify_subcategory, encode_texts
from src.taxonomy import STACK_ALIASES

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


def _get_taxonomy_stack_aliases() -> list[str]:
    aliases = []

    for stack_name, info in STACK_ALIASES.items():
        stack_aliases = info.get("aliases", [])
        aliases.extend(stack_aliases)

    unique_aliases = sorted(
        {alias.strip().lower() for alias in aliases if str(alias).strip()},
        key=len,
        reverse=True,
    )
    return unique_aliases


def _build_devtech_regex_from_taxonomy() -> re.Pattern[str]:
    aliases = _get_taxonomy_stack_aliases()
    patterns = [_build_keyword_pattern(alias) for alias in aliases]
    return re.compile("|".join(patterns), re.IGNORECASE)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())


def _contains_any(text: str, keywords: list[str] | tuple[str, ...]) -> bool:
    normalized = _normalize_text(text)
    for keyword in keywords:
        if _normalize_text(keyword) in normalized:
            return True
    return False


def _match_stack_aliases_with_rules(
    title_text: str,
    description_text: str,
    content_text: str,
) -> list[str]:
    title_text = _normalize_text(title_text)
    description_text = _normalize_text(description_text)
    content_text = _normalize_text(content_text)
    full_text = f"{title_text} {description_text} {content_text}".strip()

    matched_stacks = []

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

            if re.search(pattern, title_text, flags=re.IGNORECASE) or re.search(pattern, description_text, flags=re.IGNORECASE):
                title_or_desc_hit = True

        if not alias_hit:
            continue

        # 비모호 스택은 그대로 통과
        if not ambiguous:
            matched_stacks.append(stack_name)
            continue

        # 모호 스택은 negative keyword 있으면 탈락
        if negative_keywords and _contains_any(full_text, negative_keywords):
            continue

        # content(organizations 추정)에서만 잡힌 경우는 버림
        if not title_or_desc_hit:
            continue

        # requires_context가 있으면 context / supporting / vendor signal 중 하나는 필요
        if requires_context:
            has_context = (
                _contains_any(full_text, context_keywords)
                or _contains_any(full_text, supporting_entities)
                or _contains_any(full_text, vendor_signals)
            )
            if not has_context:
                continue

        matched_stacks.append(stack_name)

    return matched_stacks


def _extract_matched_stack_aliases(text: str, devtech_re: re.Pattern[str]) -> list[str]:
    value = str(text).strip()
    if not value:
        return []

    matches = []
    seen = set()

    for match in devtech_re.finditer(value):
        matched = match.group(0).strip()
        normalized = re.sub(r"\s+", " ", matched.lower())
        if normalized and normalized not in seen:
            seen.add(normalized)
            matches.append(normalized)

    return matches


def _apply_devtech_keyword_gate(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    title_series = _safe_series(working, "title")
    description_series = _safe_series(working, "description")
    content_series = _safe_series(working, "content")

    matched_stack_names = []
    for title, description, content in zip(title_series, description_series, content_series):
        stacks = _match_stack_aliases_with_rules(title, description, content)
        matched_stack_names.append(", ".join(stacks))

    working["devtech_text_signal"] = (
        title_series + " " + description_series + " " + content_series
    ).str.strip()
    working["matched_devtech_aliases"] = matched_stack_names
    working["is_devtech"] = pd.Series(matched_stack_names).str.strip().ne("").astype(int)

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


def run_gdelt_analysis(
    input_path,
    output_dir,
    output_prefix="gdelt",
    year_month=None,
):
    os.makedirs(output_dir, exist_ok=True)

    print("[GDELT Analysis] Load processed data")
    df = pd.read_csv(input_path)

    text_signal = _build_text_signal(df)
    df = df.loc[text_signal.ne("")].copy()

    if df.empty:
        print("No data")
        return

    scored_df = _apply_binary_tech_classifier(
        df,
        model_path=BINARY_MODEL_PATH,
        batch_size=BINARY_BATCH_SIZE,
        threshold=BINARY_THRESHOLD,
    )

    gated_df = _apply_devtech_keyword_gate(scored_df)

    gated_df["final_is_devtech"] = (
        (gated_df["is_tech"] == 1) & (gated_df["is_devtech"] == 1)
    ).astype(int)

    binary_output_path = os.path.join(output_dir, f"{output_prefix}_binary_scored.csv")
    gated_df.to_csv(binary_output_path, index=False, encoding="utf-8-sig")

    tech_df = gated_df.loc[gated_df["final_is_devtech"] == 1].copy()

    if tech_df.empty:
        print("No tech data")
        return

    result_df = classify_subcategory(tech_df)

    output_path = os.path.join(output_dir, f"{output_prefix}_tech_analyzed.csv")
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    trend_reports = build_trend_reports(result_df)
    save_trend_reports(trend_reports, output_dir, prefix=output_prefix)

    return result_df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze processed GDELT tech data and build trend reports"
    )
    parser.add_argument("--year-month", default=None, help="month in YYYY-MM format")
    parser.add_argument("--input-path", default=INPUT_PATH, help="processed GDELT csv path")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help="directory to save analysis outputs")
    parser.add_argument("--output-prefix", default="gdelt", help="prefix for output file names")
    args = parser.parse_args()

    if args.year_month:
        suffix = _year_month_to_suffix(args.year_month)
        input_path = args.input_path or os.path.join("data", "processed", f"gdelt_processed_{suffix}.csv")
        output_dir = args.output_dir or os.path.join("outputs", suffix)
        output_prefix = args.output_prefix or f"gdelt_{suffix}"
    else:
        input_path = args.input_path or INPUT_PATH
        output_dir = args.output_dir or OUTPUT_DIR
        output_prefix = args.output_prefix or "gdelt"

    os.makedirs(args.output_dir, exist_ok=True)

    print("[GDELT Analysis] Load processed data")
    print("input_path:", input_path)
    print("output_dir:", output_dir)
    print("output_prefix:", output_prefix)

    df = pd.read_csv(input_path)

    # 이미 gdelt_pipeline에서 preprocess_news_df()를 거친 파일이므로
    # 여기서는 재전처리하지 않고 바로 분석용 최소 필터만 적용
    print("[GDELT Analysis] Filter empty text rows")
    text_signal = _build_text_signal(df)
    before_rows = len(df)
    df = df.loc[text_signal.ne("")].copy()
    print("rows before filter:", before_rows)
    print("rows after filter :", len(df))

    if df.empty:
        print("[GDELT Analysis] No rows left after filtering. Abort.")
        return

    print("[GDELT Analysis] Binary tech classification start")
    scored_df = _apply_binary_tech_classifier(
        df,
        model_path=BINARY_MODEL_PATH,
        batch_size=BINARY_BATCH_SIZE,
        threshold=BINARY_THRESHOLD,
    )
    print("[GDELT Analysis] Binary tech classification done")

    print("\n[GDELT Analysis] is_tech distribution")
    print(scored_df["is_tech"].value_counts(dropna=False))

    print("\n[GDELT Analysis] Top binary scores sample")
    print(
        scored_df[["title", "is_tech_score", "is_tech"]]
        .sort_values("is_tech_score", ascending=False)
        .head(10)
        .to_dict(orient="records")
    )

    print("[GDELT Analysis] Dev-tech keyword gate start")
    gated_df = _apply_devtech_keyword_gate(scored_df)
    print("[GDELT Analysis] Dev-tech keyword gate done")

    print("\n[GDELT Analysis] is_devtech distribution")
    print(gated_df["is_devtech"].value_counts(dropna=False))

    print("\n[GDELT Analysis] Top dev-tech matched sample")
    print(
        gated_df.loc[
            gated_df["is_devtech"] == 1,
            ["title", "matched_devtech_aliases", "is_tech_score", "is_tech", "is_devtech"]
        ]
        .sort_values("is_tech_score", ascending=False)
        .head(10)
        .to_dict(orient="records")
    )

    gated_df["final_is_devtech"] = (
        (gated_df["is_tech"] == 1) & (gated_df["is_devtech"] == 1)
    ).astype(int)

    print("\n[GDELT Analysis] final_is_devtech distribution")
    print(gated_df["final_is_devtech"].value_counts(dropna=False))

    binary_output_path = os.path.join(args.output_dir, f"{args.output_prefix}_binary_scored.csv")
    print("[GDELT Analysis] Save binary + gate scored csv")
    gated_df.to_csv(binary_output_path, index=False, encoding="utf-8-sig")

    tech_df = gated_df.loc[gated_df["final_is_devtech"] == 1].copy()
    print("[GDELT Analysis] Rows kept for subcategory classification:", len(tech_df))

    if tech_df.empty:
        print("[GDELT Analysis] No rows passed the 2-stage gate. Abort subcategory analysis.")
        print("\nSaved:", binary_output_path)
        return

    print("[GDELT Analysis] Subcategory classification start")
    result_df = classify_subcategory(tech_df)
    print("[GDELT Analysis] Subcategory classification done")

    if "tech_category" in result_df.columns:
        print("\n[GDELT Analysis] Category distribution")
        print(result_df["tech_category"].value_counts(dropna=False))
    else:
        print("\n[GDELT Analysis] 'tech_category' column not found in result")

    output_path = os.path.join(args.output_dir, f"{args.output_prefix}_tech_analyzed.csv")
    print("[GDELT Analysis] Save analyzed csv")
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("[GDELT Analysis] Build trend reports")
    trend_reports = build_trend_reports(result_df)

    print("[GDELT Analysis] Save trend reports")
    trend_paths = save_trend_reports(trend_reports, args.output_dir, prefix=args.output_prefix)

    print("\nSaved:", binary_output_path)
    print("Saved:", output_path)
    print(
    scored_df[["title", "is_tech_score", "is_tech"]]
    .sort_values("is_tech_score", ascending=False)
    .head(10)
    .to_dict(orient="records")
)
    for report_name, report_path in trend_paths.items():
        print(f"{report_name}: {report_path}")


if __name__ == "__main__":
    main()
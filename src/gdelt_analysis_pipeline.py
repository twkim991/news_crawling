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
BINARY_THRESHOLD = 0.35

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
    text_signal = _build_text_signal(working)
    devtech_re = _build_devtech_regex_from_taxonomy()

    working["devtech_text_signal"] = text_signal
    working["matched_devtech_aliases"] = text_signal.map(
        lambda text: ", ".join(_extract_matched_stack_aliases(text, devtech_re))
    )
    working["is_devtech"] = working["matched_devtech_aliases"].str.strip().ne("").astype(int)

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


def main() -> None:
    print("[GDELT Analysis] Load processed data")
    df = pd.read_csv(INPUT_PATH)
    print("loaded rows:", len(df))
    print("loaded columns:", list(df.columns))

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

    binary_output_path = os.path.join(OUTPUT_DIR, "gdelt_binary_scored.csv")
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

    output_path = os.path.join(OUTPUT_DIR, "gdelt_tech_analyzed.csv")
    print("[GDELT Analysis] Save analyzed csv")
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("[GDELT Analysis] Build trend reports")
    trend_reports = build_trend_reports(result_df)

    print("[GDELT Analysis] Save trend reports")
    trend_paths = save_trend_reports(trend_reports, OUTPUT_DIR, prefix="gdelt")

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
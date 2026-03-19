import os

import pandas as pd

from src.analytics import build_trend_reports, save_trend_reports
from src.common import classify_subcategory

INPUT_PATH = os.path.join("data", "processed", "gdelt_processed.csv")
OUTPUT_DIR = "outputs"

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

    print("[GDELT Analysis] Subcategory classification start")
    result_df = classify_subcategory(df)
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

    print("\nSaved:", output_path)
    for report_name, report_path in trend_paths.items():
        print(f"{report_name}: {report_path}")


if __name__ == "__main__":
    main()
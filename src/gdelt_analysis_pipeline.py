import os

import pandas as pd

from analytics import build_trend_reports, save_trend_reports
from common import classify_subcategory, preprocess_news_df

INPUT_PATH = os.path.join("data", "processed", "gdelt_processed.csv")
OUTPUT_DIR = "outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def main() -> None:
    print("[GDELT Analysis] Load processed data")
    df = pd.read_csv(INPUT_PATH)
    df = preprocess_news_df(df)

    print("rows:", len(df))

    print("[GDELT Analysis] Subcategory classification")
    result_df = classify_subcategory(df)

    print("\n[GDELT Analysis] Category distribution")
    print(result_df["tech_category"].value_counts(dropna=False))

    output_path = os.path.join(OUTPUT_DIR, "gdelt_tech_analyzed.csv")
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    trend_paths = save_trend_reports(build_trend_reports(result_df), OUTPUT_DIR, prefix="gdelt")

    print("\nSaved:", output_path)
    for report_name, report_path in trend_paths.items():
        print(f"{report_name}: {report_path}")


if __name__ == "__main__":
    main()

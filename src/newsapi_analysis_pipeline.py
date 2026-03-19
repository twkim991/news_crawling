import argparse
import os

import pandas as pd

from src.analytics import build_trend_reports, save_trend_reports
from src.common import classify_subcategory, preprocess_news_df

def main():
    parser = argparse.ArgumentParser(description="Analyze processed NewsAPI tech articles")
    parser.add_argument("--input", default=os.path.join("data", "processed", "newsapi_processed.csv"), help="processed NewsAPI csv path")
    parser.add_argument("--output-dir", default="outputs", help="directory for analyzed csv and reports")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("[NewsAPI Analysis] Load processed data")
    df = pd.read_csv(args.input)
    df = preprocess_news_df(df)

    print("rows:", len(df))

    print("[NewsAPI Analysis] Subcategory classification")
    result_df = classify_subcategory(df)

    print("\n[NewsAPI Analysis] Category distribution")
    print(result_df["tech_category"].value_counts(dropna=False))

    output_path = os.path.join(args.output_dir, "newsapi_tech_analyzed.csv")
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    trend_paths = save_trend_reports(build_trend_reports(result_df), args.output_dir, prefix="newsapi")

    print("\nSaved:", output_path)
    for report_name, report_path in trend_paths.items():
        print(f"{report_name}: {report_path}")


if __name__ == "__main__":
    main()

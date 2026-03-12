import os
import pandas as pd

from common import classify_subcategory

INPUT_PATH = r"data\processed\newsapi_processed.csv"
OUTPUT_DIR = r"outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def main():
    print("[NewsAPI Analysis] Load processed data")
    df = pd.read_csv(INPUT_PATH)

    print("rows:", len(df))

    print("[NewsAPI Analysis] Subcategory classification")
    result_df = classify_subcategory(df)

    print("\n[NewsAPI Analysis] Category distribution")
    print(result_df["tech_category"].value_counts(dropna=False))

    output_path = os.path.join(OUTPUT_DIR, "newsapi_tech_analyzed.csv")
    result_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("\nSaved:", output_path)


if __name__ == "__main__":
    main()
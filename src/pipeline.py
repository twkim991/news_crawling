from loaders import load_ag_news, load_newsapi
from preprocess import preprocess_dataframe
from classifier import load_binary_classifier, predict_binary, classify_subcategory
from taxonomy import TECH_CATEGORY_DEFS

import pandas as pd


def run_pipeline():

    print("Load datasets")

    ag = load_ag_news("data/raw/train.csv")
    newsapi = load_newsapi("data/processed/newsapi_processed.csv")

    df = pd.concat([ag, newsapi], ignore_index=True)

    print("Preprocess")

    df = preprocess_dataframe(df)

    print("Load classifier")

    binary_model = load_binary_classifier("models/ag_binary_logreg.joblib")

    print("Binary classification")

    df = predict_binary(df, binary_model)

    print("\n=== Overall tech_pred distribution ===")
    print(df["tech_pred"].value_counts(dropna=False))

    print("\n=== tech_pred ratio by source ===")
    for source_name, group in df.groupby("source"):
        total = len(group)
        tech_count = int((group["tech_pred"] == 1).sum())
        non_tech_count = int((group["tech_pred"] == 0).sum())
        tech_ratio = tech_count / total if total > 0 else 0

        print(f"\n[source] {source_name}")
        print(f"total      : {total}")
        print(f"tech       : {tech_count}")
        print(f"non-tech   : {non_tech_count}")
        print(f"tech ratio : {tech_ratio:.4f}")

        if "class_index" in group.columns:
            print("class_index distribution:")
            print(group["class_index"].value_counts(dropna=False))

    tech_df = df[df["tech_pred"] == 1].copy()

    print("\n=== tech_df distribution by source ===")
    print(tech_df["source"].value_counts(dropna=False))

    for source_name, group in tech_df.groupby("source"):
        print(f"\n[tech_df source] {source_name}")
        print(f"rows: {len(group)}")

        if "class_index" in group.columns:
            print(group["class_index"].value_counts(dropna=False))


    print("Subcategory classification")

    tech_df = classify_subcategory(tech_df, TECH_CATEGORY_DEFS)

    for source_name, group in tech_df.groupby("source"):
        safe_name = str(source_name).lower().replace("/", "_")
        group.to_csv(
            f"outputs/final_tech_news_{safe_name}.csv",
            index=False,
            encoding="utf-8-sig"
        )

    print("Done")

if __name__ == "__main__":
    run_pipeline()
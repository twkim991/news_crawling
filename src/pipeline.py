import argparse
import os

import pandas as pd

from src.analytics import build_run_metadata, build_trend_reports, save_run_metadata, save_trend_reports
from src.classifier import load_binary_classifier, predict_binary
from src.common import classify_subcategory, preprocess_news_df
from src.loaders import load_gdelt, load_newsapi, load_ssafy_processed


def _load_input_frames(newsapi_path: str | None, ssafy_path: str | None, gdelt_path: str | None) -> tuple[list[pd.DataFrame], list[str]]:
    frames = []
    sources = []

    if newsapi_path:
        frames.append(load_newsapi(newsapi_path))
        sources.append(newsapi_path)

    if ssafy_path:
        frames.append(load_ssafy_processed(ssafy_path))
        sources.append(ssafy_path)

    if gdelt_path:
        frames.append(load_gdelt(gdelt_path))
        sources.append(gdelt_path)

    return frames, sources


def _build_stack_article_view(tech_df: pd.DataFrame) -> pd.DataFrame:
    if tech_df.empty or "stack_labels" not in tech_df.columns:
        return pd.DataFrame(columns=list(tech_df.columns) + ["stack_label"])

    stack_df = tech_df.copy()
    stack_df["stack_label"] = stack_df["stack_labels"].fillna("").str.split("|")
    stack_df = stack_df.explode("stack_label")
    stack_df["stack_label"] = stack_df["stack_label"].fillna("").astype(str).str.strip()
    return stack_df[stack_df["stack_label"].ne("")].reset_index(drop=True)


def run_pipeline(
    newsapi_path: str | None,
    ssafy_path: str | None,
    gdelt_path: str | None,
    model_path: str,
    output_dir: str,
    metadata_path: str,
    proba_threshold: float,
    uncertainty_margin: float,
):
    print("Load datasets")
    frames, input_sources = _load_input_frames(newsapi_path, ssafy_path, gdelt_path)
    if not frames:
        raise ValueError("At least one operational dataset must be provided.")

    df = pd.concat(frames, ignore_index=True)

    print("Preprocess")
    df = preprocess_news_df(df)

    print("Load classifier")
    binary_model = load_binary_classifier(model_path)

    print("Binary classification")
    df = predict_binary(
        df,
        binary_model,
        proba_threshold=proba_threshold,
        uncertainty_margin=uncertainty_margin,
    )

    uncertain_df = df[df["is_uncertain"]].copy()
    tech_df = df[(df["tech_pred"] == 1) & (~df["is_uncertain"])].copy()

    print("Subcategory classification")
    tech_df = classify_subcategory(tech_df)
    stack_article_df = _build_stack_article_view(tech_df)

    os.makedirs(output_dir, exist_ok=True)
    uncertain_df.to_csv(
        os.path.join(output_dir, "uncertain_articles_all_sources.csv"),
        index=False,
        encoding="utf-8-sig",
    )
    tech_df.to_csv(
        os.path.join(output_dir, "final_tech_news_all_sources.csv"),
        index=False,
        encoding="utf-8-sig",
    )
    stack_article_df.to_csv(
        os.path.join(output_dir, "final_tech_news_by_stack.csv"),
        index=False,
        encoding="utf-8-sig",
    )
    for source_name, group in tech_df.groupby("source"):
        safe_name = str(source_name).lower().replace("/", "_").replace(" ", "_")
        group.to_csv(
            os.path.join(output_dir, f"final_tech_news_{safe_name}.csv"),
            index=False,
            encoding="utf-8-sig",
        )

    trend_paths = save_trend_reports(build_trend_reports(tech_df), output_dir)
    metadata = build_run_metadata(
        df,
        tech_df,
        input_sources=input_sources,
        model_path=model_path,
        output_dir=output_dir,
        thresholds={
            "binary_probability": proba_threshold,
            "uncertainty_margin": uncertainty_margin,
        },
    )
    metadata["trend_reports"] = trend_paths
    metadata["stack_article_output"] = os.path.join(output_dir, "final_tech_news_by_stack.csv")
    save_run_metadata(metadata, metadata_path)

    print("Done")
    print(f"all sources output: {os.path.join(output_dir, 'final_tech_news_all_sources.csv')}")
    print(f"stack article output: {os.path.join(output_dir, 'final_tech_news_by_stack.csv')}")
    print(f"metadata: {metadata_path}")
    for report_name, report_path in trend_paths.items():
        print(f"{report_name}: {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Operational news inference + trend report pipeline")
    parser.add_argument("--newsapi-input", default="data/processed/newsapi_processed.csv", help="processed NewsAPI csv path")
    parser.add_argument("--ssafy-input", default=None, help="processed SSAFY/final csv path")
    parser.add_argument("--gdelt-input", default=None, help="processed GDELT csv path")
    parser.add_argument("--model", default="models/ag_binary_logreg.joblib", help="binary classifier path")
    parser.add_argument("--output-dir", default="outputs", help="directory for inference outputs")
    parser.add_argument("--metadata", default="outputs/metadata.json", help="run metadata json path")
    parser.add_argument("--tech-threshold", type=float, default=0.55, help="binary tech probability threshold")
    parser.add_argument("--uncertainty-margin", type=float, default=0.08, help="uncertain zone from 0.5")
    args = parser.parse_args()

    run_pipeline(
        newsapi_path=args.newsapi_input,
        ssafy_path=args.ssafy_input,
        gdelt_path=args.gdelt_input,
        model_path=args.model,
        output_dir=args.output_dir,
        metadata_path=args.metadata,
        proba_threshold=args.tech_threshold,
        uncertainty_margin=args.uncertainty_margin,
    )

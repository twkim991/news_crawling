import argparse
import json
import os
import re
from datetime import datetime

import pandas as pd

from classifier import load_binary_classifier, predict_binary
from common import classify_subcategory, preprocess_news_df


COLUMN_CANDIDATES = {
    "title": ["title", "제목", "headline", "news_title"],
    "description": ["description", "desc", "요약", "summary", "subtitle", "category_str"],
    "content": ["content", "본문", "기사본문", "article", "body", "news"],
    "url": ["url", "link", "주소", "기사링크"],
    "published_at": ["published_at", "published", "date", "datetime", "등록일", "작성일"],
    "source": ["source", "언론사", "publisher", "press", "company"],
    "category": ["category", "category_str", "섹션", "분류"],
    "reporter": ["reporter", "기자", "author", "writer"],
}

NON_TECH_CATEGORY_REGEX = re.compile(r"(문화|연예|스포츠|사회|정치|국제|생활|라이프|사설|오피니언)")
TECH_KEYWORD_REGEX = re.compile(
    r"(기술|테크|it|ai|인공지능|반도체|클라우드|플랫폼|소프트웨어|앱|모바일|데이터|보안|개발|코딩|프로그래밍)",
    re.IGNORECASE,
)


def load_ssafy_csv(path: str) -> pd.DataFrame:
    """Load SSAFY CSV robustly. Many files are pipe-delimited with multiline quoted article."""
    try:
        return pd.read_csv(path, sep="|", quotechar='"', encoding="utf-8-sig", engine="python")
    except Exception:
        return pd.read_csv(path, encoding="utf-8-sig")


def _resolve_column(df: pd.DataFrame, target: str):
    lower_map = {c.lower(): c for c in df.columns}
    for candidate in COLUMN_CANDIDATES[target]:
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


def normalize_ssafy_schema(df: pd.DataFrame):
    mapped = {target: _resolve_column(df, target) for target in COLUMN_CANDIDATES}

    out = pd.DataFrame()
    for target, original in mapped.items():
        if original is None:
            out[target] = ""
        else:
            out[target] = df[original]

    out["source"] = out["source"].replace("", "SSAFY")
    out["source"] = out["source"].fillna("SSAFY")

    # category_str가 description으로 들어간 경우 text richness를 위해 reporter도 보강
    out["description"] = out["description"].fillna("").astype(str)
    out["reporter"] = out["reporter"].fillna("").astype(str)
    out.loc[out["description"].str.strip() == "", "description"] = (
        "기자: " + out["reporter"].str.strip()
    )

    return out, mapped


def apply_metadata_prior(df: pd.DataFrame) -> pd.DataFrame:
    """Use category metadata as high-precision prior to improve precision."""
    df = df.copy()

    cat_text = (df["category"].astype(str) + " " + df["description"].astype(str)).str.lower()
    cat_text = cat_text.fillna("").astype(str)

    df["is_non_tech_meta"] = cat_text.apply(lambda x: bool(NON_TECH_CATEGORY_REGEX.search(x)))
    df["has_tech_meta"] = cat_text.apply(lambda x: bool(TECH_KEYWORD_REGEX.search(x)))

    # 비기술 섹션이면서 기술 단서가 없는 경우는 강하게 제외 후보
    df["meta_drop"] = df["is_non_tech_meta"] & (~df["has_tech_meta"])
    return df


def calculate_quality_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    no_hangul_re = re.compile(r"[가-힣]")
    ad_noise_re = re.compile(r"\b(기자|무단전재|재배포|저작권자|구독|광고)\b")

    df["title_len"] = df["title"].astype(str).str.len()
    df["text_len"] = df["text"].astype(str).str.len()
    df["has_hangul"] = df["text"].astype(str).apply(lambda x: bool(no_hangul_re.search(x)))
    df["has_ad_noise"] = df["text"].astype(str).apply(lambda x: bool(ad_noise_re.search(x)))

    df["is_short_text"] = df["text_len"] < 40
    df["is_short_title"] = df["title_len"] < 8
    df["quality_drop"] = (
        df["is_short_text"]
        | df["is_short_title"]
        | ~df["has_hangul"]
    )

    return df


def build_profile(df_raw: pd.DataFrame, df_norm: pd.DataFrame, mapped_cols: dict) -> dict:
    missing_ratio = {
        col: float(df_norm[col].astype(str).str.strip().eq("").mean())
        for col in ["title", "description", "content", "url", "published_at", "source", "category", "reporter"]
    }

    profile = {
        "created_at": datetime.now().isoformat(),
        "raw_rows": int(len(df_raw)),
        "raw_columns": list(df_raw.columns),
        "column_mapping": mapped_cols,
        "missing_ratio": missing_ratio,
        "top_categories": df_norm["category"].astype(str).value_counts().head(20).to_dict(),
    }
    return profile


def _safe_makedirs_for_file(path: str):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description="SSAFY 한국어 뉴스 품질강화 + 분류 파이프라인")
    parser.add_argument("--input", default="data/raw/ssafy_dataset_news_2025_1st_half.csv", help="raw CSV path")
    parser.add_argument("--model", default="models/ag_binary_logreg.joblib", help="binary classifier path")
    parser.add_argument("--output", default="outputs/final_ssafy_tech_news.csv", help="final output csv path")
    parser.add_argument("--profile", default="outputs/ssafy_profile.json", help="schema/profile json path")
    parser.add_argument("--tech-threshold", type=float, default=0.55, help="tech probability threshold")
    parser.add_argument("--uncertainty-margin", type=float, default=0.08, help="uncertain zone from 0.5")
    args = parser.parse_args()

    print(f"[SSAFY] load raw: {args.input}")
    raw_df = load_ssafy_csv(args.input)

    norm_df, mapping = normalize_ssafy_schema(raw_df)
    profile = build_profile(raw_df, norm_df, mapping)

    norm_df = preprocess_news_df(norm_df)
    norm_df = apply_metadata_prior(norm_df)
    norm_df = calculate_quality_flags(norm_df)

    print("[SSAFY] load binary model")
    clf = load_binary_classifier(args.model)

    print("[SSAFY] binary inference with confidence")
    pred_df = predict_binary(
        norm_df,
        clf,
        proba_threshold=args.tech_threshold,
        uncertainty_margin=args.uncertainty_margin,
    )

    filtered = pred_df[
        (pred_df["tech_pred"] == 1)
        & (~pred_df["quality_drop"])
        & (~pred_df["is_uncertain"])
        & (~pred_df["meta_drop"])
    ].copy()

    print("[SSAFY] zero-shot subcategory")
    filtered = classify_subcategory(filtered)

    _safe_makedirs_for_file(args.output)
    _safe_makedirs_for_file(args.profile)

    filtered.to_csv(args.output, index=False, encoding="utf-8-sig")
    with open(args.profile, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    print("\n[SSAFY] done")
    print("profile:", args.profile)
    print("output :", args.output)
    print("input rows:", len(raw_df))
    print("after preprocess:", len(norm_df))
    print("tech candidates:", int((pred_df["tech_pred"] == 1).sum()))
    print("meta-drop rows:", int(pred_df["meta_drop"].sum()))
    print("final quality tech:", len(filtered))


if __name__ == "__main__":
    main()

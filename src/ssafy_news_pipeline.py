import argparse
import json
import os
import re
from datetime import datetime

import pandas as pd

from src.classifier import load_binary_classifier, predict_binary
from src.common import classify_subcategory, preprocess_news_df


COLUMN_CANDIDATES = {
    "title": ["title", "제목", "headline", "news_title"],
    "description": ["description", "desc", "요약", "summary", "subtitle"],
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


def _safe_makedirs_for_file(path: str):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)


def _normalize_source_name(value: str) -> str:
    text = str(value).strip()
    if not text:
        return "SSAFY"

    lowered = text.lower()

    source_alias_map = {
        "chosunbiz": "ChosunBiz",
        "조선비즈": "ChosunBiz",
        "매일경제": "매일경제",
        "매경": "매일경제",
        "mk": "매일경제",
        "mbn": "MBN",
        "머니투데이": "머니투데이",
        "mt": "머니투데이",
        "전자신문": "전자신문",
        "zdnet": "ZDNet Korea",
        "zdnet korea": "ZDNet Korea",
        "지디넷코리아": "ZDNet Korea",
        "한겨레": "한겨레",
        "한국경제": "한국경제",
        "hankyung": "한국경제",
        "연합뉴스": "연합뉴스",
        "뉴시스": "뉴시스",
        "it조선": "IT조선",
        "it chosun": "IT조선",
    }

    return source_alias_map.get(lowered, text)


def _normalize_published_at(series: pd.Series) -> pd.Series:
    cleaned = series.fillna("").astype(str).str.strip()
    parsed = pd.to_datetime(cleaned, errors="coerce")
    return parsed.dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")


def _safe_str_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column].fillna("").astype(str)
    return pd.Series("", index=df.index, dtype="object")


def normalize_ssafy_schema(df: pd.DataFrame):
    mapped = {target: _resolve_column(df, target) for target in COLUMN_CANDIDATES}

    out = pd.DataFrame(index=df.index)
    for target, original in mapped.items():
        if original is None:
            out[target] = ""
        else:
            out[target] = df[original]

    out["title"] = out["title"].fillna("").astype(str)
    out["description"] = out["description"].fillna("").astype(str)
    out["content"] = out["content"].fillna("").astype(str)
    out["url"] = out["url"].fillna("").astype(str)
    out["published_at"] = _normalize_published_at(out["published_at"])
    out["source"] = out["source"].fillna("").astype(str).map(_normalize_source_name)
    out["category"] = out["category"].fillna("").astype(str)
    out["reporter"] = out["reporter"].fillna("").astype(str)

    # description이 비어 있으면 reporter만 약하게 보강
    empty_desc_mask = out["description"].str.strip() == ""
    out.loc[empty_desc_mask, "description"] = (
        "기자: " + out.loc[empty_desc_mask, "reporter"].str.strip()
    ).str.strip()

    return out, mapped


def deduplicate_news(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before_rows = len(df)

    # URL 우선 dedupe
    url_series = _safe_str_series(df, "url").str.strip()
    has_url = url_series.ne("")
    df_with_url = df.loc[has_url].copy()
    df_without_url = df.loc[~has_url].copy()

    if not df_with_url.empty:
        df_with_url = df_with_url.drop_duplicates(subset=["url"], keep="first")

    # URL 없는 행은 제목+본문 기준으로 dedupe
    if not df_without_url.empty:
        title_series = _safe_str_series(df_without_url, "title").str.strip()
        content_series = _safe_str_series(df_without_url, "content").str.strip()
        dedupe_key = title_series + "||" + content_series
        df_without_url = df_without_url.loc[~dedupe_key.duplicated(keep="first")].copy()

    deduped = pd.concat([df_with_url, df_without_url], ignore_index=True)

    # 보조 dedupe: 제목+본문 완전 중복 제거
    title_series = _safe_str_series(deduped, "title").str.strip()
    content_series = _safe_str_series(deduped, "content").str.strip()
    dedupe_key = title_series + "||" + content_series
    deduped = deduped.loc[~dedupe_key.duplicated(keep="first")].copy()

    print(f"[SSAFY] deduplicate: {before_rows} -> {len(deduped)}")
    return deduped.reset_index(drop=True)


def apply_metadata_prior(df: pd.DataFrame) -> pd.DataFrame:
    """Use category metadata as high-precision prior to improve precision."""
    df = df.copy()

    cat_text = (_safe_str_series(df, "category") + " " + _safe_str_series(df, "description")).str.lower()
    cat_text = cat_text.fillna("").astype(str)

    df["is_non_tech_meta"] = cat_text.str.contains(NON_TECH_CATEGORY_REGEX, na=False)
    df["has_tech_meta"] = cat_text.str.contains(TECH_KEYWORD_REGEX, na=False)

    # 비기술 섹션이면서 기술 단서가 없는 경우는 강하게 제외 후보
    df["meta_drop"] = df["is_non_tech_meta"] & (~df["has_tech_meta"])
    return df


def calculate_quality_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    no_hangul_re = re.compile(r"[가-힣]")
    ad_noise_re = re.compile(r"\b(기자|무단전재|재배포|저작권자|구독|광고)\b")

    df["title_len"] = _safe_str_series(df, "title").str.len()
    df["text_len"] = _safe_str_series(df, "text").str.len()
    df["has_hangul"] = _safe_str_series(df, "text").str.contains(no_hangul_re, na=False)
    df["has_ad_noise"] = _safe_str_series(df, "text").str.contains(ad_noise_re, na=False)

    df["is_short_text"] = df["text_len"] < 40
    df["is_short_title"] = df["title_len"] < 8

    # 광고성 노이즈는 바로 탈락시키지 않고 보조 지표로만 유지
    df["quality_drop"] = (
        df["is_short_text"]
        | df["is_short_title"]
        | ~df["has_hangul"]
    )

    return df


def build_profile(df_raw: pd.DataFrame, df_norm: pd.DataFrame, mapped_cols: dict) -> dict:
    missing_ratio = {
        col: float(_safe_str_series(df_norm, col).str.strip().eq("").mean())
        for col in ["title", "description", "content", "url", "published_at", "source", "category", "reporter"]
    }

    profile = {
        "created_at": datetime.now().isoformat(),
        "raw_rows": int(len(df_raw)),
        "normalized_rows": int(len(df_norm)),
        "raw_columns": list(df_raw.columns),
        "column_mapping": mapped_cols,
        "missing_ratio": missing_ratio,
        "top_categories": _safe_str_series(df_norm, "category").value_counts().head(20).to_dict(),
        "top_sources": _safe_str_series(df_norm, "source").value_counts().head(20).to_dict(),
    }
    return profile


def save_review_splits(
    df: pd.DataFrame,
    output_dir: str,
    prefix: str = "ssafy",
) -> dict:
    os.makedirs(output_dir, exist_ok=True)

    paths = {
        "meta_drop": os.path.join(output_dir, f"{prefix}_meta_drop_review.csv"),
        "quality_drop": os.path.join(output_dir, f"{prefix}_quality_drop_review.csv"),
        "uncertain": os.path.join(output_dir, f"{prefix}_uncertain_review.csv"),
    }

    meta_drop_df = df.loc[df["meta_drop"]].copy() if "meta_drop" in df.columns else pd.DataFrame()
    quality_drop_df = df.loc[df["quality_drop"]].copy() if "quality_drop" in df.columns else pd.DataFrame()
    uncertain_df = df.loc[df["is_uncertain"]].copy() if "is_uncertain" in df.columns else pd.DataFrame()

    meta_drop_df.to_csv(paths["meta_drop"], index=False, encoding="utf-8-sig")
    quality_drop_df.to_csv(paths["quality_drop"], index=False, encoding="utf-8-sig")
    uncertain_df.to_csv(paths["uncertain"], index=False, encoding="utf-8-sig")

    return paths


def print_basic_analysis(df: pd.DataFrame, title: str) -> None:
    print(f"\n[{title}] rows: {len(df)}")

    if df.empty:
        print(f"[{title}] no rows")
        return

    if "tech_category" in df.columns:
        print(f"\n[{title}] tech_category distribution")
        print(df["tech_category"].astype(str).value_counts(dropna=False).head(20))

    if "primary_stack" in df.columns:
        print(f"\n[{title}] primary_stack distribution")
        print(df["primary_stack"].astype(str).value_counts(dropna=False).head(20))

    if "source" in df.columns:
        print(f"\n[{title}] source distribution")
        print(df["source"].astype(str).value_counts(dropna=False).head(20))

    if "published_at" in df.columns:
        date_series = pd.to_datetime(df["published_at"], errors="coerce")
        daily_counts = date_series.dt.strftime("%Y-%m-%d").value_counts().sort_index()
        print(f"\n[{title}] daily counts (top 20 by date order)")
        print(daily_counts.head(20))


def main():
    parser = argparse.ArgumentParser(description="SSAFY 한국어 뉴스 정제 + 기술뉴스 분류 + 세부 스택 분류 파이프라인")
    parser.add_argument("--input", default="data/raw/ssafy_dataset_news_2025_1st_half.csv", help="raw CSV path")
    parser.add_argument("--model", default="models/ag_binary_logreg.joblib", help="binary classifier path")
    parser.add_argument("--output", default="outputs/final_ssafy_tech_news.csv", help="final output csv path")
    parser.add_argument("--profile", default="outputs/ssafy_profile.json", help="schema/profile json path")
    parser.add_argument("--review-dir", default="outputs/review", help="directory for dropped/uncertain review csv files")
    parser.add_argument("--tech-threshold", type=float, default=0.55, help="tech probability threshold")
    parser.add_argument("--uncertainty-margin", type=float, default=0.08, help="uncertain zone from 0.5")
    args = parser.parse_args()

    _safe_makedirs_for_file(args.output)
    _safe_makedirs_for_file(args.profile)
    os.makedirs(args.review_dir, exist_ok=True)

    print(f"[SSAFY] load raw: {args.input}")
    raw_df = load_ssafy_csv(args.input)
    print("[SSAFY] raw rows:", len(raw_df))

    print("[SSAFY] normalize schema")
    norm_df, mapping = normalize_ssafy_schema(raw_df)
    norm_df = deduplicate_news(norm_df)

    print("[SSAFY] preprocess")
    norm_df = preprocess_news_df(norm_df)

    print("[SSAFY] apply metadata prior")
    norm_df = apply_metadata_prior(norm_df)

    print("[SSAFY] calculate quality flags")
    norm_df = calculate_quality_flags(norm_df)

    profile = build_profile(raw_df, norm_df, mapping)

    print("[SSAFY] load binary model")
    clf = load_binary_classifier(args.model)

    # 품질/메타데이터에서 이미 제외될 행은 binary 추론을 건너뜀
    infer_mask = (~norm_df["quality_drop"]) & (~norm_df["meta_drop"])
    infer_df = norm_df.loc[infer_mask].copy()
    skipped_rows = int((~infer_mask).sum())

    pred_df = norm_df.copy()
    pred_df["tech_pred"] = 0
    pred_df["tech_score"] = 0.0
    pred_df["prediction_confidence"] = 0.0
    pred_df["is_uncertain"] = False

    if infer_df.empty:
        print("[SSAFY] binary inference skipped (no eligible rows)")
    else:
        print(
            f"[SSAFY] binary inference with confidence on {len(infer_df)} / {len(norm_df)} rows "
            f"(skipped {skipped_rows})"
        )
        infer_pred_df = predict_binary(
            infer_df,
            clf,
            proba_threshold=args.tech_threshold,
            uncertainty_margin=args.uncertainty_margin,
        )

        pred_df.loc[
            infer_pred_df.index,
            ["tech_pred", "tech_score", "prediction_confidence", "is_uncertain"],
        ] = infer_pred_df[
            ["tech_pred", "tech_score", "prediction_confidence", "is_uncertain"]
        ]

    print("\n[SSAFY] filtering final tech news")
    filtered = pred_df[
        (pred_df["tech_pred"] == 1)
        & (~pred_df["quality_drop"])
        & (~pred_df["is_uncertain"])
        & (~pred_df["meta_drop"])
    ].copy()

    print("[SSAFY] zero-shot subcategory")
    filtered = classify_subcategory(filtered)

    print_basic_analysis(filtered, "SSAFY Final")

    print("[SSAFY] save final output")
    filtered.to_csv(args.output, index=False, encoding="utf-8-sig")

    print("[SSAFY] save profile")
    with open(args.profile, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    print("[SSAFY] save review splits")
    review_paths = save_review_splits(pred_df, args.review_dir, prefix="ssafy")

    print("\n[SSAFY] done")
    print("profile:", args.profile)
    print("output :", args.output)
    print("review/meta_drop :", review_paths["meta_drop"])
    print("review/quality   :", review_paths["quality_drop"])
    print("review/uncertain :", review_paths["uncertain"])
    print("input rows:", len(raw_df))
    print("after normalize+d edupe:", len(norm_df))
    print("binary tech candidates:", int((pred_df["tech_pred"] == 1).sum()))
    print("meta-drop rows:", int(pred_df["meta_drop"].sum()))
    print("quality-drop rows:", int(pred_df["quality_drop"].sum()))
    print("uncertain rows:", int(pred_df["is_uncertain"].sum()))
    print("final quality tech:", len(filtered))


if __name__ == "__main__":
    main()
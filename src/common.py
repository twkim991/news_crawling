import re
from functools import lru_cache
from typing import Iterable

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.taxonomy import (
    STACK_ALIASES,
    STACK_MAX_TAGS,
    STACK_MIN_HITS,
    STACK_SCORE_THRESHOLD,
    PRIMARY_STACK_MIN_MARGIN,
    PRIMARY_STACK_MIN_SCORE,
    STACK_EVENT_KEYWORDS,
    TECH_CATEGORY_DEFS,
    SUBCATEGORY_MIN_GAP,
    SUBCATEGORY_MIN_SCORE,
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[Model] device: {DEVICE}")

HTML_TAG_RE = re.compile(r"<[^>]+>")
TRUNCATED_CHARS_RE = re.compile(r"\s*\[\+\d+\s+chars\]\s*$")
URL_RE = re.compile(r"http\S+|www\.\S+")
WHITESPACE_RE = re.compile(r"[\r\n\t]+")
MULTISPACE_RE = re.compile(r"\s+")
REPRINT_NOISE_RE = re.compile(
    r"(?:reuters|associated press|ap news|yonhap news|연합뉴스|무단전재|재배포|all rights reserved)",
    re.IGNORECASE,
)
NON_ALNUM_RE = re.compile(r"[^a-z0-9가-힣]+")
LOW_SIGNAL_TITLE_RE = re.compile(r"(?:video|podcast|newsletter|live updates?)", re.IGNORECASE)

REQUIRED_SCHEMA_COLUMNS = ["title", "description", "content", "url", "published_at", "source"]


@lru_cache(maxsize=1)
def get_embed_model() -> SentenceTransformer:
    print("[Model] load sentence-transformer")
    return SentenceTransformer("intfloat/multilingual-e5-small", device=DEVICE)


def clean_text(text: str) -> str:
    if text is None:
        return ""

    cleaned = str(text)
    cleaned = HTML_TAG_RE.sub(" ", cleaned)
    cleaned = TRUNCATED_CHARS_RE.sub("", cleaned)
    cleaned = URL_RE.sub(" ", cleaned)
    cleaned = REPRINT_NOISE_RE.sub(" ", cleaned)
    cleaned = WHITESPACE_RE.sub(" ", cleaned)
    return MULTISPACE_RE.sub(" ", cleaned).strip()


def _clean_text_series(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.replace(HTML_TAG_RE, " ", regex=True)
        .str.replace(TRUNCATED_CHARS_RE, "", regex=True)
        .str.replace(URL_RE, " ", regex=True)
        .str.replace(REPRINT_NOISE_RE, " ", regex=True)
        .str.replace(WHITESPACE_RE, " ", regex=True)
        .str.replace(MULTISPACE_RE, " ", regex=True)
        .str.strip()
    )


def normalize_title_for_dedup(series: pd.Series) -> pd.Series:
    return (
        _clean_text_series(series)
        .str.lower()
        .str.replace(NON_ALNUM_RE, " ", regex=True)
        .str.replace(MULTISPACE_RE, " ", regex=True)
        .str.strip()
    )


def _get_text_column(df: pd.DataFrame, column: str) -> pd.Series:
    return _clean_text_series(df[column]) if column in df else pd.Series("", index=df.index, dtype="object")


def ensure_schema(df: pd.DataFrame, *, source_name: str | None = None) -> pd.DataFrame:
    normalized = df.copy()
    for column in REQUIRED_SCHEMA_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""

    if source_name is not None:
        normalized["source"] = source_name
    else:
        normalized["source"] = normalized["source"].fillna("").replace("", "unknown")

    return normalized

MAX_CONTENT_CHARS = 700
MAX_TEXT_CHARS = 2000


def build_text(title: str, description: str, content: str = "") -> str:
    title = clean_text(title)
    description = clean_text(description)
    content = clean_text(content)[:MAX_CONTENT_CHARS]

    text = f"{title}. {description}. {content}".strip()
    return MULTISPACE_RE.sub(" ", text).strip()[:MAX_TEXT_CHARS]


def build_text_series(title: pd.Series, description: pd.Series, content: pd.Series) -> pd.Series:
    content_cut = content.str.slice(0, MAX_CONTENT_CHARS)
    text = (title + ". " + description + ". " + content_cut).str.strip()
    return text.str.replace(MULTISPACE_RE, " ", regex=True).str.strip().str.slice(0, MAX_TEXT_CHARS)


def preprocess_news_df(df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_schema(df)
    df = df.copy()

    title_clean = _get_text_column(df, "title")
    desc_clean = _get_text_column(df, "description")
    content_clean = _get_text_column(df, "content")

    df["title"] = title_clean
    df["description"] = desc_clean
    df["content"] = content_clean
    df["normalized_title"] = normalize_title_for_dedup(df["title"])
    df["text"] = build_text_series(title_clean, desc_clean, content_clean)
    df["text_len"] = df["text"].str.len()
    df["content_ratio"] = np.where(df["text_len"] > 0, df["content"].str.len() / df["text_len"], 0.0)

    df = df[df["title"].ne("")]
    df = df[df["text_len"] >= 30]
    df = df[df["normalized_title"].str.len() >= 8]
    df = df[~df["title"].str.fullmatch(LOW_SIGNAL_TITLE_RE, na=False)]
    df = df[df["content_ratio"] <= 0.97]

    if "url" in df.columns:
        df["url"] = df["url"].fillna("").astype(str)
        has_url = df["url"].str.strip().ne("")
        df = pd.concat(
            [df.loc[has_url].drop_duplicates(subset=["url"]), df.loc[~has_url]],
            ignore_index=True,
        )

    df = df.drop_duplicates(subset=["text"])
    df = df.drop_duplicates(subset=["normalized_title"])
    return df.reset_index(drop=True)


def encode_texts(texts: Iterable[str], batch_size: int = 64):
    return get_embed_model().encode(
        list(texts),
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


@lru_cache(maxsize=1)
def _get_category_embeddings():
    category_names = tuple(TECH_CATEGORY_DEFS.keys())
    print("[Subcategory] Encode category definitions")
    category_embeddings = encode_texts(list(TECH_CATEGORY_DEFS.values()), batch_size=16)
    return category_names, category_embeddings


@lru_cache(maxsize=1)
def _get_stack_patterns():
    patterns = {}
    for stack_name, info in STACK_ALIASES.items():
        compiled = []
        for alias in info["aliases"]:
            normalized = alias.lower().strip()
            escaped = re.escape(normalized)
            if re.fullmatch(r"[a-z0-9\.\+#\-\s]+", normalized):
                pattern = re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")
            else:
                pattern = re.compile(escaped)
            compiled.append(pattern)
        patterns[stack_name] = {
            "category": info["category"],
            "subgroup": info["subgroup"],
            "patterns": tuple(compiled),
        }
    return patterns


@lru_cache(maxsize=1)
def _get_alias_lookup():
    alias_lookup = {}
    for stack_name, info in STACK_ALIASES.items():
        for alias in info["aliases"]:
            normalized = alias.lower().strip()
            alias_lookup[normalized] = {
                "stack": stack_name,
                "category": info["category"],
                "subgroup": info["subgroup"],
            }
    return alias_lookup


@lru_cache(maxsize=1)
def _get_combined_alias_regex():
    aliases = sorted(_get_alias_lookup().keys(), key=len, reverse=True)
    parts = []

    for alias in aliases:
        escaped = re.escape(alias).replace(r"\ ", r"\s+")
        if re.fullmatch(r"[a-z0-9\.\+#\-\s]+", alias):
            parts.append(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")
        else:
            parts.append(escaped)

    return re.compile("|".join(parts), re.IGNORECASE)


def annotate_stack_taxonomy(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    result_columns = [
        "stack_matches",
        "stack_labels",
        "mentioned_stacks",
        "stack_categories",
        "stack_subgroups",
        "primary_stack",
        "secondary_stack",
        "primary_stack_subgroup",
        "secondary_stack_subgroup",
        "stack_domain",
        "stack_match_count",
        "stack_label_count",
        "stack_confidences",
        "primary_stack_score",
        "primary_stack_margin",
        "stack_disambiguation_notes",
    ]

    if df.empty:
        for column in result_columns:
            df[column] = pd.Series(dtype="object" if "count" not in column and "score" not in column and "margin" not in column else "float64")
        return df

    def _safe_series(frame: pd.DataFrame, column: str) -> pd.Series:
        if column in frame.columns:
            return frame[column].fillna("").astype(str)
        return pd.Series("", index=frame.index, dtype="object")

    def _score_stack_candidate(stack_name: str, info: dict[str, object], hit_count: int, title: str, description: str, content: str, text: str) -> tuple[float, list[str]]:
        score = float(hit_count)
        notes: list[str] = []
        aliases = tuple(str(alias).lower().strip() for alias in info.get("aliases", ()))

        title_hits = sum(title.count(alias) for alias in aliases if alias)
        description_hits = sum(description.count(alias) for alias in aliases if alias)
        content_hits = sum(content.count(alias) for alias in aliases if alias)

        score += title_hits * 3.0
        score += description_hits * 2.0
        score += content_hits * 1.0

        if title_hits:
            notes.append("title_match")
        if description_hits:
            notes.append("description_match")
        if content_hits:
            notes.append("content_match")

        context_keywords = tuple(str(keyword).lower() for keyword in info.get("context_keywords", ()))
        context_hits = sum(1 for keyword in context_keywords if keyword in text)
        if context_hits:
            score += min(context_hits, 3) * 1.5
            notes.append(f"context:{context_hits}")

        vendor_signals = tuple(str(keyword).lower() for keyword in info.get("supporting_entities", ())) + tuple(str(keyword).lower() for keyword in info.get("vendor_signals", ()))
        vendor_hits = sum(1 for keyword in vendor_signals if keyword in text)
        if vendor_hits:
            score += min(vendor_hits, 2) * 1.5
            notes.append(f"vendor:{vendor_hits}")

        event_hits = sum(1 for keyword in STACK_EVENT_KEYWORDS if keyword in text)
        if event_hits:
            score += min(event_hits, 2) * 0.5
            notes.append(f"event:{event_hits}")

        negative_keywords = tuple(str(keyword).lower() for keyword in info.get("negative_keywords", ()))
        negative_hits = sum(1 for keyword in negative_keywords if keyword in text)
        if negative_hits:
            score -= min(negative_hits, 3) * 3.0
            notes.append(f"negative:{negative_hits}")

        requires_context = bool(info.get("requires_context", False))
        is_ambiguous = bool(info.get("ambiguous", False))
        has_support = bool(context_hits or vendor_hits)
        if requires_context and not has_support:
            score -= 4.0
            notes.append("missing_context")
        elif is_ambiguous and not has_support and title_hits == 0 and description_hits == 0:
            score -= 2.0
            notes.append("weak_ambiguous_match")

        return score, notes

    alias_lookup = _get_alias_lookup()
    combined_re = _get_combined_alias_regex()

    title_series = _safe_series(df, "title").str.lower().str.strip()
    description_series = _safe_series(df, "description").str.lower().str.strip()
    content_series = _safe_series(df, "content").str.lower().str.strip()
    text_series = _safe_series(df, "text").str.strip()
    fallback_text = (title_series + " " + description_series + " " + content_series).str.strip()
    analysis_text = text_series.where(text_series.ne(""), fallback_text).str.lower().str.strip()

    df["stack_matches"] = ""
    df["stack_labels"] = ""
    df["mentioned_stacks"] = ""
    df["stack_categories"] = ""
    df["stack_subgroups"] = ""
    df["primary_stack"] = "Unspecified"
    df["secondary_stack"] = ""
    df["primary_stack_subgroup"] = ""
    df["secondary_stack_subgroup"] = ""
    df["stack_domain"] = _safe_series(df, "tech_category").replace("", "Other Tech")
    df["stack_match_count"] = 0.0
    df["stack_label_count"] = 0.0
    df["stack_confidences"] = ""
    df["primary_stack_score"] = 0.0
    df["primary_stack_margin"] = 0.0
    df["stack_disambiguation_notes"] = ""

    valid_mask = analysis_text.ne("")
    if not valid_mask.any():
        return df

    valid_index = df.index[valid_mask]
    unique_frame = pd.DataFrame({
        "analysis_text": analysis_text.loc[valid_mask],
        "title": title_series.loc[valid_mask],
        "description": description_series.loc[valid_mask],
        "content": content_series.loc[valid_mask],
    })

    inverse_codes, _ = pd.factorize(unique_frame["analysis_text"], sort=False)
    unique_frame = unique_frame.drop_duplicates(subset=["analysis_text"]).reset_index(drop=True)

    unique_results = []

    for row in unique_frame.itertuples(index=False):
        hit_counter: dict[str, dict[str, object]] = {}

        for match in combined_re.finditer(row.analysis_text):
            alias = match.group(0).lower().strip()
            info = alias_lookup.get(alias)
            if info is None:
                alias_norm = re.sub(r"\s+", " ", alias)
                info = alias_lookup.get(alias_norm)
            if info is None:
                continue

            stack_name = str(info["stack"])
            stack_info = STACK_ALIASES.get(stack_name, {})
            if stack_name not in hit_counter:
                hit_counter[stack_name] = {
                    "category": info["category"],
                    "subgroup": info["subgroup"],
                    "hit_count": 0,
                    "info": stack_info,
                }
            hit_counter[stack_name]["hit_count"] += 1

        scored_matches = []
        notes_parts = []
        for stack_name, data in hit_counter.items():
            hit_count = int(data["hit_count"])
            if hit_count < STACK_MIN_HITS:
                continue

            score, notes = _score_stack_candidate(
                stack_name,
                data["info"],
                hit_count,
                row.title,
                row.description,
                row.content,
                row.analysis_text,
            )
            notes_parts.append(f"{stack_name}:{','.join(notes) if notes else 'plain'}")
            scored_matches.append((stack_name, data["category"], data["subgroup"], hit_count, score))

        mentioned_matches = sorted(scored_matches, key=lambda item: (-item[4], -item[3], item[0]))
        selected_matches = [item for item in mentioned_matches if item[4] >= STACK_SCORE_THRESHOLD][:STACK_MAX_TAGS]

        match_names = [name for name, _, _, _, _ in selected_matches]
        match_categories = [category for _, category, _, _, _ in selected_matches]
        match_subgroups = [subgroup for _, _, subgroup, _, _ in selected_matches]
        confidence_parts = [f"{name}:{score:.1f}" for name, _, _, _, score in selected_matches]

        primary_stack = "Unspecified"
        primary_subgroup = ""
        secondary_stack = ""
        secondary_subgroup = ""
        stack_domain = "Other Tech"
        primary_score = 0.0
        primary_margin = 0.0

        if selected_matches:
            top_name, top_category, top_subgroup, _, top_score = selected_matches[0]
            next_score = selected_matches[1][4] if len(selected_matches) > 1 else 0.0
            primary_margin = float(top_score - next_score)
            if top_score >= PRIMARY_STACK_MIN_SCORE and primary_margin >= PRIMARY_STACK_MIN_MARGIN:
                primary_stack = top_name
                primary_subgroup = top_subgroup
                stack_domain = top_category
                primary_score = float(top_score)
            else:
                stack_domain = top_category
                primary_score = float(top_score)

            if primary_stack != "Unspecified":
                remaining = [item for item in selected_matches if item[0] != primary_stack]
                if remaining:
                    secondary_stack = remaining[0][0]
                    secondary_subgroup = remaining[0][2]

        unique_results.append({
            "stack_matches": "|".join(f"{name}:{hit_count}:{score:.1f}" for name, _, _, hit_count, score in selected_matches),
            "stack_labels": "|".join(match_names),
            "mentioned_stacks": "|".join(name for name, *_ in mentioned_matches[:STACK_MAX_TAGS]),
            "stack_categories": "|".join(match_categories),
            "stack_subgroups": "|".join(match_subgroups),
            "primary_stack": primary_stack,
            "secondary_stack": secondary_stack,
            "primary_stack_subgroup": primary_subgroup,
            "secondary_stack_subgroup": secondary_subgroup,
            "stack_domain": stack_domain,
            "stack_match_count": float(sum(hit_count for _, _, _, hit_count, _ in selected_matches)),
            "stack_label_count": float(len(match_names)),
            "stack_confidences": "|".join(confidence_parts),
            "primary_stack_score": primary_score,
            "primary_stack_margin": primary_margin,
            "stack_disambiguation_notes": "|".join(notes_parts),
        })

    result_df = pd.DataFrame(unique_results)
    restored = result_df.iloc[inverse_codes].reset_index(drop=True)

    for column in result_columns:
        values = restored[column]
        if column in {"stack_match_count", "stack_label_count", "primary_stack_score", "primary_stack_margin"}:
            df.loc[valid_index, column] = values.astype(float).to_numpy()
        else:
            df.loc[valid_index, column] = values.to_numpy()

    return df

SIMILARITY_CHUNK_SIZE = 4096


def classify_subcategory(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    result_columns = [
        "tech_category",
        "tech_category_score",
        "tech_category_score_gap",
        "top2_category",
        "top2_score",
    ]

    if df.empty:
        for column in result_columns:
            df[column] = pd.Series(dtype="object" if "category" in column else "float64")
        return annotate_stack_taxonomy(df)

    if "text" not in df.columns:
        raise KeyError("classify_subcategory requires a 'text' column")

    # text 정리
    text_series = df["text"].fillna("").astype(str).str.strip()

    # 기본값 먼저 채우기
    df["tech_category"] = "Other Tech"
    df["tech_category_score"] = 0.0
    df["tech_category_score_gap"] = 0.0
    df["top2_category"] = "Other Tech"
    df["top2_score"] = 0.0

    # 빈 텍스트는 분류 제외
    valid_mask = text_series.ne("")
    if not valid_mask.any():
        return annotate_stack_taxonomy(df)

    valid_index = df.index[valid_mask]
    valid_texts = text_series.loc[valid_mask]

    category_names, category_embeddings = _get_category_embeddings()
    category_names = np.asarray(category_names)

    if len(category_names) == 0:
        return annotate_stack_taxonomy(df)

    # 중복 텍스트 제거
    unique_texts, inverse_indices = pd.factorize(valid_texts, sort=False)

    # pd.factorize는 codes, uniques 순서가 아니라 codes first가 아님에 주의
    # 실제 반환: (codes, uniques)
    inverse_codes, unique_values = pd.factorize(valid_texts, sort=False)
    unique_text_list = unique_values.tolist()

    print("[Subcategory] Encode unique article texts")
    unique_embeddings = encode_texts(unique_text_list, batch_size=64)

    # dtype 축소
    unique_embeddings = np.asarray(unique_embeddings, dtype=np.float32)
    category_embeddings = np.asarray(category_embeddings, dtype=np.float32)

    num_unique = len(unique_embeddings)
    num_categories = len(category_names)

    top1_idx_all = np.empty(num_unique, dtype=np.int32)
    top2_idx_all = np.empty(num_unique, dtype=np.int32)
    top1_score_all = np.empty(num_unique, dtype=np.float32)
    top2_score_all = np.empty(num_unique, dtype=np.float32)

    print("[Subcategory] Similarity calculation")
    for start in range(0, num_unique, SIMILARITY_CHUNK_SIZE):
        end = min(start + SIMILARITY_CHUNK_SIZE, num_unique)
        emb_chunk = unique_embeddings[start:end]

        sims = cosine_similarity(emb_chunk, category_embeddings).astype(np.float32, copy=False)

        if num_categories == 1:
            local_top1_idx = np.zeros(len(sims), dtype=np.int32)
            local_top2_idx = np.zeros(len(sims), dtype=np.int32)
            local_top1_score = sims[:, 0]
            local_top2_score = np.zeros(len(sims), dtype=np.float32)
        else:
            local_top2 = np.argpartition(sims, kth=-2, axis=1)[:, -2:]
            local_top2_scores = np.take_along_axis(sims, local_top2, axis=1)
            local_order = np.argsort(local_top2_scores, axis=1)[:, ::-1]
            local_top2 = np.take_along_axis(local_top2, local_order, axis=1)

            row_idx = np.arange(len(sims))
            local_top1_idx = local_top2[:, 0]
            local_top2_idx = local_top2[:, 1]
            local_top1_score = sims[row_idx, local_top1_idx]
            local_top2_score = sims[row_idx, local_top2_idx]

        top1_idx_all[start:end] = local_top1_idx
        top2_idx_all[start:end] = local_top2_idx
        top1_score_all[start:end] = local_top1_score
        top2_score_all[start:end] = local_top2_score

    score_gap_all = top1_score_all - top2_score_all
    top1_category_all = category_names[top1_idx_all]
    top2_category_all = category_names[top2_idx_all]

    final_category_all = np.where(
        (top1_score_all < SUBCATEGORY_MIN_SCORE) | (score_gap_all < SUBCATEGORY_MIN_GAP),
        "Other Tech",
        top1_category_all,
    )

    # unique 결과를 원래 valid row로 복원
    restored_top1_category = final_category_all[inverse_codes]
    restored_top1_score = top1_score_all[inverse_codes]
    restored_score_gap = score_gap_all[inverse_codes]
    restored_top2_category = top2_category_all[inverse_codes]
    restored_top2_score = top2_score_all[inverse_codes]

    df.loc[valid_index, "tech_category"] = restored_top1_category
    df.loc[valid_index, "tech_category_score"] = restored_top1_score.astype(float)
    df.loc[valid_index, "tech_category_score_gap"] = restored_score_gap.astype(float)
    df.loc[valid_index, "top2_category"] = restored_top2_category
    df.loc[valid_index, "top2_score"] = restored_top2_score.astype(float)

    df = annotate_stack_taxonomy(df)

    stack_category_series = df["stack_categories"].fillna("").astype(str).str.strip()
    stack_label_series = df["stack_labels"].fillna("").astype(str).str.strip()

    single_stack_category_mask = stack_category_series.ne("") & ~stack_category_series.str.contains(r"\|", regex=True)
    other_tech_mask = df["tech_category"].fillna("").eq("Other Tech")

    # 임베딩 분류가 Other Tech로 떨어졌더라도,
    # stack taxonomy에서 단일 카테고리가 명확하면 그 카테고리로 보정
    override_mask = single_stack_category_mask & other_tech_mask

    df.loc[override_mask, "tech_category"] = stack_category_series.loc[override_mask]
    df.loc[override_mask, "tech_category_score"] = np.maximum(
        df.loc[override_mask, "tech_category_score"].astype(float),
        0.70,
    )
    df.loc[override_mask, "tech_category_score_gap"] = np.maximum(
        df.loc[override_mask, "tech_category_score_gap"].astype(float),
        0.10,
    )

    print("[Subcategory] stack-based override rows:", int(override_mask.sum()))
    print(
        "[Subcategory] overridden category distribution:\n",
        df.loc[override_mask, "tech_category"].value_counts(dropna=False)
    )

    return df
from functools import lru_cache
import re

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from embeddings import encode_texts
from taxonomy import STACK_ALIASES, TECH_CATEGORY_DEFS, SUBCATEGORY_MIN_GAP, SUBCATEGORY_MIN_SCORE


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
            "patterns": tuple(compiled),
        }
    return patterns


def annotate_stack_taxonomy(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    stack_patterns = _get_stack_patterns()

    if df.empty:
        for column in ["stack_matches", "primary_stack", "secondary_stack", "stack_domain", "stack_match_count"]:
            df[column] = pd.Series(dtype="object" if column != "stack_match_count" else "float64")
        return df

    primary_stacks = []
    secondary_stacks = []
    stack_domains = []
    stack_match_counts = []
    stack_matches = []

    for _, row in df.iterrows():
        text = " ".join(
            [
                str(row.get("title", "")),
                str(row.get("description", "")),
                str(row.get("content", "")),
                str(row.get("text", "")),
            ]
        ).lower()

        matches = []
        for stack_name, pattern_info in stack_patterns.items():
            hit_count = sum(1 for pattern in pattern_info["patterns"] if pattern.search(text))
            if hit_count > 0:
                matches.append((stack_name, pattern_info["category"], hit_count))

        matches.sort(key=lambda item: (-item[2], item[0]))
        match_names = [name for name, _, _ in matches]
        stack_matches.append("|".join(match_names))
        stack_match_counts.append(float(sum(hit_count for _, _, hit_count in matches)))

        primary_stacks.append(match_names[0] if match_names else "Unspecified")
        secondary_stacks.append(match_names[1] if len(match_names) > 1 else "")
        stack_domains.append(matches[0][1] if matches else row.get("tech_category", "Other Tech"))

    df["stack_matches"] = stack_matches
    df["primary_stack"] = primary_stacks
    df["secondary_stack"] = secondary_stacks
    df["stack_domain"] = stack_domains
    df["stack_match_count"] = stack_match_counts
    return df


def classify_subcategory(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if df.empty:
        for column in [
            "tech_category",
            "tech_category_score",
            "tech_category_score_gap",
            "top2_category",
            "top2_score",
        ]:
            df[column] = pd.Series(dtype="object" if "category" in column else "float64")
        return annotate_stack_taxonomy(df)

    category_names, category_embeddings = _get_category_embeddings()

    print("[Subcategory] Encode article texts")
    article_embeddings = encode_texts(df["text"].tolist(), batch_size=64)

    sims = cosine_similarity(article_embeddings, category_embeddings)
    top_two_indices = np.argpartition(sims, kth=-2, axis=1)[:, -2:]
    top_two_scores = np.take_along_axis(sims, top_two_indices, axis=1)
    top_two_order = np.argsort(top_two_scores, axis=1)[:, ::-1]
    top_two_indices = np.take_along_axis(top_two_indices, top_two_order, axis=1)

    top1_idx = top_two_indices[:, 0]
    top2_idx = top_two_indices[:, 1]
    row_idx = np.arange(len(df))

    top1_scores = sims[row_idx, top1_idx].astype(float)
    top2_scores = sims[row_idx, top2_idx].astype(float)
    score_gaps = top1_scores - top2_scores

    top1_categories = np.take(category_names, top1_idx)
    top2_categories = np.take(category_names, top2_idx)
    final_categories = np.where(
        (top1_scores < SUBCATEGORY_MIN_SCORE) | (score_gaps < SUBCATEGORY_MIN_GAP),
        "Other Tech",
        top1_categories,
    )

    df["tech_category"] = final_categories
    df["tech_category_score"] = top1_scores
    df["tech_category_score_gap"] = score_gaps
    df["top2_category"] = top2_categories
    df["top2_score"] = top2_scores

    return annotate_stack_taxonomy(df)

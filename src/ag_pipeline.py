import os
import re
import json
import joblib
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.metrics.pairwise import cosine_similarity


# =========================
# 1. 경로 설정
# =========================
TRAIN_PATH = r"data\raw\train.csv"
TEST_PATH = r"data\raw\test.csv"

PROCESSED_DIR = r"data\processed"
MODELS_DIR = r"models"
OUTPUTS_DIR = r"outputs"

os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)


# =========================
# 2. 원본 라벨 정의
# =========================
LABEL_MAP = {
    1: "World",
    2: "Sports",
    3: "Business",
    4: "Sci/Tech",
}


# =========================
# 3. 세부 기술 카테고리 정의
# =========================
TECH_CATEGORY_DEFS = {
    "AI/ML": "artificial intelligence and machine learning technologies such as OpenAI, GPT, LLM, PyTorch, TensorFlow, model training, inference, NLP, and computer vision",
    "Language": "programming and query languages such as Python, Java, JavaScript, TypeScript, Go, Rust, C++, SQL, and other languages used to write software and data queries",
    "Framework": "frameworks, libraries, runtimes, SDKs, and development platforms such as React, Next.js, Spring, Django, Node.js, .NET, and development tools used to build applications and services",
    "DB/Storage": "databases, caches, search engines, vector databases, object storage, and persistence technologies such as MySQL, PostgreSQL, MongoDB, Redis, Elasticsearch, and S3",
    "Infra/Cloud": "cloud and infrastructure technologies such as AWS, Azure, Google Cloud, containers, networking, hosting, compute resources, and infrastructure services for running systems",
    "Data Engineering/Messaging": "data engineering and messaging systems such as Kafka, Spark, Hadoop, Airflow, ETL, ELT, warehousing, stream processing, and event-driven infrastructure",
    "DevOps/Automation": "DevOps and automation tools such as Docker, Kubernetes, GitHub Actions, Jenkins, Terraform, CI/CD, orchestration, observability, and workflow automation",
    "Security": "cyber security technologies such as vulnerability management, malware detection, IAM, encryption, application security, cloud security, and zero trust",
    "Collaboration/Utility": "developer productivity and collaboration tools such as GitHub, GitLab, Jira, Postman, Swagger, IDEs, package managers, testing, and documentation tools",
    "Other Tech": "general technology news about computing, software, hardware, devices, and innovation that does not fit the other categories clearly",
}

# =========================
# 3-1. 세부 분류 threshold 설정
# =========================
SUBCATEGORY_MIN_SCORE = 0.30
SUBCATEGORY_MIN_GAP = 0.03

# =========================
# 4. 데이터 로드
# =========================
def load_ag_news_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        header=None,
        names=["class_index", "title", "description"]
    )

    # 혹시 문자열 헤더가 들어있으면 제거
    df = df[df["class_index"] != "Class Index"].copy()

    df["class_index"] = df["class_index"].astype(int)
    df["title"] = df["title"].fillna("").astype(str)
    df["description"] = df["description"].fillna("").astype(str)

    return df


# =========================
# 5. 텍스트 정제
# =========================
def clean_text(text: str) -> str:
    text = str(text)

    # HTML 태그 제거
    text = re.sub(r"<[^>]+>", " ", text)

    # URL 제거
    text = re.sub(r"http\S+|www\.\S+", " ", text)

    # 이스케이프 개행 정리
    text = text.replace("\\n", " ")

    # 특수 공백 정리
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def build_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["title_clean"] = df["title"].apply(clean_text)
    df["description_clean"] = df["description"].apply(clean_text)

    df["text"] = (
        df["title_clean"].str.strip() + ". " + df["description_clean"].str.strip()
    ).str.strip()

    df["label_name"] = df["class_index"].map(LABEL_MAP)

    # AG News 원래 라벨 기준 1차 tech 여부
    df["binary_label"] = (df["class_index"] == 4).astype(int)

    return df


# =========================
# 6. 1차 필터링
# =========================
def filter_rows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # text 비어있는 것 제거
    df = df[df["text"].notna()].copy()

    # 너무 짧은 것 제거
    df = df[df["text"].str.len() >= 20].copy()

    # 중복 제거
    df = df.drop_duplicates(subset=["text"]).copy()

    return df


# =========================
# 7. 임베딩
# =========================
def encode_texts(model: SentenceTransformer, texts, batch_size=64):
    return model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


# =========================
# 8. 이진 분류기 학습
# =========================
def train_binary_classifier(model: SentenceTransformer, train_df: pd.DataFrame, test_df: pd.DataFrame):
    X_train = encode_texts(model, train_df["text"].tolist())
    X_test = encode_texts(model, test_df["text"].tolist())

    y_train = train_df["binary_label"].values
    y_test = test_df["binary_label"].values

    clf = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42,
    )
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, preds)
    f1 = f1_score(y_test, preds)

    print("\n=== [1] Tech vs Non-Tech Binary Classification ===")
    print("Accuracy:", round(acc, 4))
    print("F1 Score :", round(f1, 4))
    print(classification_report(y_test, preds, target_names=["non-tech", "tech"]))

    joblib.dump(clf, os.path.join(MODELS_DIR, "ag_binary_logreg.joblib"))

    return clf, X_test, preds, probs


# =========================
# 9. 세부 카테고리 분류
# =========================
def classify_tech_subcategories(model: SentenceTransformer, df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if df.empty:
        df["tech_category"] = []
        df["tech_category_score"] = []
        df["tech_category_score_gap"] = []
        df["top2_category"] = []
        df["top2_score"] = []
        return df

    category_names = list(TECH_CATEGORY_DEFS.keys())
    category_texts = [TECH_CATEGORY_DEFS[name] for name in category_names]

    category_embeddings = encode_texts(model, category_texts, batch_size=16)
    article_embeddings = encode_texts(model, df["text"].tolist(), batch_size=64)

    sims = cosine_similarity(article_embeddings, category_embeddings)

    assigned_categories = []
    top1_scores = []
    score_gaps = []
    top2_categories = []
    top2_scores = []

    for row in sims:
        # 점수 높은 순으로 인덱스 정렬
        sorted_idx = np.argsort(row)[::-1]

        top1_idx = sorted_idx[0]
        top2_idx = sorted_idx[1] if len(sorted_idx) > 1 else sorted_idx[0]

        top1_category = category_names[top1_idx]
        top2_category = category_names[top2_idx]

        top1_score = float(row[top1_idx])
        top2_score = float(row[top2_idx])
        score_gap = top1_score - top2_score

        # fallback 로직
        if top1_score < SUBCATEGORY_MIN_SCORE or score_gap < SUBCATEGORY_MIN_GAP:
            final_category = "Other Tech"
        else:
            final_category = top1_category

        assigned_categories.append(final_category)
        top1_scores.append(top1_score)
        score_gaps.append(score_gap)
        top2_categories.append(top2_category)
        top2_scores.append(top2_score)

    df["tech_category"] = assigned_categories
    df["tech_category_score"] = top1_scores
    df["tech_category_score_gap"] = score_gaps
    df["top2_category"] = top2_categories
    df["top2_score"] = top2_scores

    return df


# =========================
# 10. 전체 파이프라인
# =========================
def main():
    print("[Step 1] Load data")
    train_df = load_ag_news_csv(TRAIN_PATH)
    test_df = load_ag_news_csv(TEST_PATH)

    print("train raw:", train_df.shape)
    print("test raw :", test_df.shape)

    print("\n[Step 2] Build text fields")
    train_df = build_text_fields(train_df)
    test_df = build_text_fields(test_df)

    print("\n[Step 3] Filter rows")
    train_df = filter_rows(train_df)
    test_df = filter_rows(test_df)

    print("train filtered:", train_df.shape)
    print("test filtered :", test_df.shape)

    print("\n[Step 4] Save processed csv")
    train_df.to_csv(os.path.join(PROCESSED_DIR, "ag_train_processed.csv"), index=False, encoding="utf-8-sig")
    test_df.to_csv(os.path.join(PROCESSED_DIR, "ag_test_processed.csv"), index=False, encoding="utf-8-sig")

    print("\n[Step 5] Load embedding model")
    embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    print("\n[Step 6] Train binary classifier")
    clf, X_test, binary_preds, binary_probs = train_binary_classifier(embed_model, train_df, test_df)

    print("\n[Step 7] Save binary prediction results")
    binary_result = test_df[["class_index", "label_name", "title", "description", "text", "binary_label"]].copy()
    binary_result["pred_binary"] = binary_preds
    binary_result["pred_binary_label"] = binary_result["pred_binary"].map({0: "non-tech", 1: "tech"})
    binary_result["pred_binary_score"] = binary_probs
    binary_result.to_csv(os.path.join(OUTPUTS_DIR, "ag_binary_predictions.csv"), index=False, encoding="utf-8-sig")

    print("\n[Step 8] Extract only predicted tech articles")
    predicted_tech_df = binary_result[binary_result["pred_binary"] == 1].copy()

    print("predicted tech count:", len(predicted_tech_df))

    print("\n[Step 9] Subcategory classification for tech articles")
    tech_sub_df = classify_tech_subcategories(embed_model, predicted_tech_df)

    tech_sub_df.to_csv(os.path.join(OUTPUTS_DIR, "ag_tech_subcategories.csv"), index=False, encoding="utf-8-sig")

    print("\n[Step 9-1] Subcategory distribution")
    print(tech_sub_df["tech_category"].value_counts())

    print("\n[Step 10] Save metadata")
    metadata = {
        "dataset": "AG News",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "binary_classifier": "LogisticRegression",
        "original_labels": LABEL_MAP,
        "tech_subcategories": TECH_CATEGORY_DEFS,
        "subcategory_min_score": SUBCATEGORY_MIN_SCORE,
        "subcategory_min_gap": SUBCATEGORY_MIN_GAP,
        "train_rows_filtered": int(len(train_df)),
        "test_rows_filtered": int(len(test_df)),
        "predicted_tech_count": int(len(predicted_tech_df)),
    }

    with open(os.path.join(OUTPUTS_DIR, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\nDone.")


if __name__ == "__main__":
    main()
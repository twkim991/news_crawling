import os

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score

from embeddings import encode_texts
from io_utils import ensure_dir
from settings import AG_TEST_EMB_PATH, AG_TEST_PATH, AG_TRAIN_EMB_PATH, AG_TRAIN_PATH, MODELS_DIR
from text_processing import preprocess_news_df


TRAIN_PATH = AG_TRAIN_PATH
TEST_PATH = AG_TEST_PATH
TRAIN_EMB_PATH = AG_TRAIN_EMB_PATH
TEST_EMB_PATH = AG_TEST_EMB_PATH

ensure_dir(MODELS_DIR)

LABEL_MAP = {
    1: "World",
    2: "Sports",
    3: "Business",
    4: "Sci/Tech",
}

def get_or_create_embeddings(texts, save_path: str, batch_size=64):
    if os.path.exists(save_path):
        print(f"[Cache] Load embeddings from: {save_path}")
        return np.load(save_path)

    print(f"[Cache] Create embeddings: {save_path}")
    embeddings = encode_texts(texts, batch_size=batch_size)

    np.save(save_path, embeddings)
    print(f"[Cache] Saved embeddings: {save_path}")

    return embeddings

def load_ag_news(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        header=None,
        names=["class_index", "title", "description"]
    )

    df = df[df["class_index"] != "Class Index"].copy()
    df["class_index"] = df["class_index"].astype(int)

    df["content"] = ""
    df["url"] = ""
    df["published_at"] = ""
    df["source"] = "AG"
    df["label_name"] = df["class_index"].map(LABEL_MAP)
    df["binary_label"] = (df["class_index"] == 4).astype(int)

    print(df["binary_label"].value_counts())

    return df


def main():
    print("[AG] Load train/test")
    train_df = load_ag_news(TRAIN_PATH)
    test_df = load_ag_news(TEST_PATH)

    print("[AG] Preprocess")
    train_df = preprocess_news_df(train_df)
    test_df = preprocess_news_df(test_df)

    print("[AG] Encode train")
    X_train = get_or_create_embeddings(
        train_df["text"].tolist(),
        TRAIN_EMB_PATH,
        batch_size=64
    )
    y_train = train_df["binary_label"].values

    print("[AG] Encode test")
    X_test = get_or_create_embeddings(
        test_df["text"].tolist(),
        TEST_EMB_PATH,
        batch_size=64
    )
    y_test = test_df["binary_label"].values

    print("[AG] Train classifier")
    clf = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42
    )
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)

    print("\n=== AG Binary Classifier Result ===")
    print("Accuracy:", round(accuracy_score(y_test, preds), 4))
    print("F1:", round(f1_score(y_test, preds), 4))
    print(classification_report(y_test, preds, target_names=["non-tech", "tech"]))

    joblib.dump(clf, os.path.join(MODELS_DIR, "ag_binary_logreg.joblib"))
    print("\nSaved: models/ag_binary_logreg.joblib")


if __name__ == "__main__":
    main()
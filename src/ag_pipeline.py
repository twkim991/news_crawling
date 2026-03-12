import os
import joblib
import pandas as pd
import numpy as np

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, f1_score

from common import preprocess_news_df, encode_texts


import torch

print(torch.__version__)
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))



TRAIN_PATH = r"data\raw\train.csv"
TEST_PATH = r"data\raw\test.csv"
MODELS_DIR = r"models"
TRAIN_EMB_PATH = r"models\ag_train_embeddings.npy"
TEST_EMB_PATH = r"models\ag_test_embeddings.npy"

os.makedirs(MODELS_DIR, exist_ok=True)

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
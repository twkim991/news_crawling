import joblib
import numpy as np

from common import encode_texts


def load_binary_classifier(path):
    return joblib.load(path)


def predict_binary(df, model, batch_size: int = 256):
    texts = df["text"].tolist()
    total = len(texts)

    embeddings = []
    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        print(f"embedding {i} / {total}")
        batch_emb = encode_texts(batch, batch_size=batch_size)
        embeddings.append(batch_emb)

    embeddings = np.vstack(embeddings)

    print(model.predict_proba(embeddings)[:10])

    preds = model.predict(embeddings)

    df = df.copy()
    df["tech_pred"] = preds

    return df

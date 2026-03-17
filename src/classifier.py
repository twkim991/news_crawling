import joblib
import numpy as np

from common import encode_texts


def load_binary_classifier(path):
    return joblib.load(path)


def predict_binary(
    df,
    model,
    batch_size: int = 256,
    proba_threshold: float = 0.5,
    uncertainty_margin: float = 0.10,
):
    texts = df["text"].tolist()
    total = len(texts)

    embeddings = []
    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        print(f"embedding {i} / {total}")
        batch_emb = encode_texts(batch, batch_size=batch_size)
        embeddings.append(batch_emb)

    embeddings = np.vstack(embeddings)

    probas = model.predict_proba(embeddings)
    tech_probs = probas[:, 1]
    preds = (tech_probs >= proba_threshold).astype(int)

    confidence = np.abs(tech_probs - 0.5) * 2
    uncertain = np.abs(tech_probs - 0.5) < uncertainty_margin

    df = df.copy()
    df["tech_pred"] = preds
    df["tech_score"] = tech_probs
    df["prediction_confidence"] = confidence
    df["is_uncertain"] = uncertain

    return df

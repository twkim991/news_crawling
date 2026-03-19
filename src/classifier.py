import joblib
import numpy as np

from embeddings import encode_texts


def load_binary_classifier(path):
    return joblib.load(path)


def predict_binary(
    df,
    model,
    batch_size: int = 256,
    proba_threshold: float = 0.5,
    uncertainty_margin: float = 0.10,
):
    df = df.copy()
    texts = df["text"].tolist()

    if not texts:
        df["tech_pred"] = np.array([], dtype=np.int64)
        df["tech_score"] = np.array([], dtype=np.float64)
        df["prediction_confidence"] = np.array([], dtype=np.float64)
        df["is_uncertain"] = np.array([], dtype=bool)
        return df

    print(f"embedding {len(texts)} texts")
    embeddings = encode_texts(texts, batch_size=batch_size)

    tech_probs = model.predict_proba(embeddings)[:, 1]
    preds = (tech_probs >= proba_threshold).astype(np.int64)

    df["tech_pred"] = preds
    df["tech_score"] = tech_probs
    df["prediction_confidence"] = np.abs(tech_probs - 0.5) * 2
    df["is_uncertain"] = np.abs(tech_probs - 0.5) < uncertainty_margin

    return df

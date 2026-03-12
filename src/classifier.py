import joblib
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def load_binary_classifier(path):

    return joblib.load(path)


def predict_binary(df, model):

    texts = df["text"].tolist()
    embeddings = []

    batch_size = 256
    total = len(texts)

    for i in range(0, total, batch_size):

        batch = texts[i:i+batch_size]

        print(f"embedding {i} / {total}")

        batch_emb = embed_model.encode(
            batch,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        embeddings.append(batch_emb)

    embeddings = np.vstack(embeddings)

    print(model.predict_proba(embeddings)[:10])

    preds = model.predict(embeddings)

    df["tech_pred"] = preds

    return df


def classify_subcategory(df, category_defs):

    category_names = list(category_defs.keys())
    category_texts = list(category_defs.values())

    category_embeddings = embed_model.encode(
        category_texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    article_embeddings = embed_model.encode(
        df["text"].tolist(),
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    sims = cosine_similarity(article_embeddings, category_embeddings)

    idx = np.argmax(sims, axis=1)

    df["tech_category"] = [category_names[i] for i in idx]

    return df
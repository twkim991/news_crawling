from functools import lru_cache
from typing import Iterable

import torch
from sentence_transformers import SentenceTransformer

from settings import EMBEDDING_MODEL_NAME


@lru_cache(maxsize=1)
def get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    device = get_device()
    print(f"[Model] device: {device}")
    return SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)


def encode_texts(texts: Iterable[str], batch_size: int = 64):
    model = get_embedding_model()
    return model.encode(
        list(texts),
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

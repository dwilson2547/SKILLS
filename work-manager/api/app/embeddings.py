from typing import Iterable

import numpy as np
from fastembed import TextEmbedding

_model = None


def load_model():
    global _model
    if _model is None:
        _model = TextEmbedding("BAAI/bge-small-en-v1.5")
    return _model


def get_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        return []
    model = load_model()
    return [float(v) for v in next(model.embed([text.strip()]))]


def batch_embeddings(texts: Iterable[str]) -> list[list[float]]:
    clean_texts = [text.strip() if text else "" for text in texts]
    if not clean_texts:
        return []
    model = load_model()
    return [[float(v) for v in vector] for vector in model.embed(clean_texts)]


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    if not vec1 or not vec2:
        return 0.0
    a = np.array(vec1)
    b = np.array(vec2)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)

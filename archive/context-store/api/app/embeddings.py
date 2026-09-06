import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_model = None


def load_model() -> None:
    global _model
    try:
        from fastembed import TextEmbedding

        _model = TextEmbedding("BAAI/bge-small-en-v1.5")
        logger.info("Embedding model loaded")
    except Exception as exc:
        logger.warning("Embedding model unavailable — semantic search disabled: %s", exc)


def encode(text: str) -> Optional[list[float]]:
    if _model is None:
        return None
    return list(_model.embed([text]))[0].tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def is_available() -> bool:
    return _model is not None

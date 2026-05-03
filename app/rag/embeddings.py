import hashlib
import math
from functools import lru_cache

from app.core import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._model = None

    @property
    def dimension(self) -> int:
        if self.settings.embedding_provider == "hash":
            return 384
        model = self._load_model()
        vector = model.embed_query("dimension probe") if hasattr(model, "embed_query") else model.encode("dimension probe")
        return len(vector)

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        provider = self.settings.embedding_provider
        if provider == "hash":
            return [self._hash_embedding(text) for text in texts]
        model = self._load_model()
        if provider == "openai":
            return [list(vector) for vector in model.embed_documents(texts)]
        vectors = model.encode(texts, normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]

    def _load_model(self):
        if self._model is not None:
            return self._model
        if self.settings.embedding_provider == "openai":
            from langchain_openai import OpenAIEmbeddings

            self._model = OpenAIEmbeddings(model=self.settings.embedding_model, api_key=self.settings.openai_api_key)
        else:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.settings.embedding_model)
        return self._model

    @staticmethod
    def _hash_embedding(text: str, dimensions: int = 384) -> list[float]:
        vector = [0.0] * dimensions
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()

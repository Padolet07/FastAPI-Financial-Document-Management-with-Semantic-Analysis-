import json
import math
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core import get_settings
from app.models.document import DocumentChunk


@dataclass
class VectorHit:
    document_id: int
    chunk_id: int | None
    chunk_index: int
    content: str
    score: float


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return numerator / (left_norm * right_norm)


class SQLVectorStore:
    def __init__(self, db: Session):
        self.db = db

    def upsert_document_chunks(self, document_id: int, chunks: list[str], embeddings: list[list[float]]) -> int:
        self.remove_document(document_id)
        for index, (content, embedding) in enumerate(zip(chunks, embeddings)):
            self.db.add(
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=index,
                    content=content,
                    embedding_json=json.dumps(embedding),
                )
            )
        self.db.commit()
        return len(chunks)

    def remove_document(self, document_id: int) -> None:
        self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        self.db.commit()

    def search(self, query_embedding: list[float], limit: int = 20) -> list[VectorHit]:
        hits: list[VectorHit] = []
        for chunk in self.db.query(DocumentChunk).all():
            score = cosine_similarity(query_embedding, json.loads(chunk.embedding_json))
            hits.append(
                VectorHit(
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    score=score,
                )
            )
        return sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]

    def context(self, document_id: int) -> list[VectorHit]:
        chunks = (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )
        return [
            VectorHit(
                document_id=chunk.document_id,
                chunk_id=chunk.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=0.0,
            )
            for chunk in chunks
        ]


class QdrantVectorStore:
    def __init__(self, dimension: int):
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Distance, VectorParams

        settings = get_settings()
        self.collection = settings.qdrant_collection
        self.client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        collections = [item.name for item in self.client.get_collections().collections]
        if self.collection not in collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )

    def upsert_document_chunks(self, document_id: int, chunks: list[str], embeddings: list[list[float]]) -> int:
        from qdrant_client.http.models import PointStruct

        self.remove_document(document_id)
        points = [
            PointStruct(
                id=int(f"{document_id}{index:06d}"),
                vector=embedding,
                payload={"document_id": document_id, "chunk_index": index, "content": content},
            )
            for index, (content, embedding) in enumerate(zip(chunks, embeddings))
        ]
        if points:
            self.client.upsert(collection_name=self.collection, points=points)
        return len(points)

    def remove_document(self, document_id: int) -> None:
        from qdrant_client.http.models import FieldCondition, Filter, MatchValue

        self.client.delete(
            collection_name=self.collection,
            points_selector=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]),
        )

    def search(self, query_embedding: list[float], limit: int = 20) -> list[VectorHit]:
        results = self.client.search(collection_name=self.collection, query_vector=query_embedding, limit=limit)
        return [
            VectorHit(
                document_id=int(item.payload["document_id"]),
                chunk_id=None,
                chunk_index=int(item.payload["chunk_index"]),
                content=str(item.payload["content"]),
                score=float(item.score),
            )
            for item in results
        ]

    def context(self, document_id: int) -> list[VectorHit]:
        from qdrant_client.http.models import FieldCondition, Filter, MatchValue

        records, _ = self.client.scroll(
            collection_name=self.collection,
            scroll_filter=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]),
            limit=1000,
        )
        hits = [
            VectorHit(
                document_id=int(item.payload["document_id"]),
                chunk_id=None,
                chunk_index=int(item.payload["chunk_index"]),
                content=str(item.payload["content"]),
                score=0.0,
            )
            for item in records
        ]
        return sorted(hits, key=lambda hit: hit.chunk_index)


def get_vector_store(db: Session, dimension: int):
    settings = get_settings()
    if settings.vector_backend == "qdrant":
        return QdrantVectorStore(dimension=dimension)
    return SQLVectorStore(db)

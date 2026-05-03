from fastapi import HTTPException, status
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.core import get_settings
from app.models.document import Document
from app.rag.embeddings import get_embedding_service
from app.rag.vector_store import VectorHit, cosine_similarity, get_vector_store


class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.embeddings = get_embedding_service()
        self.vector_store = get_vector_store(db, self.embeddings.dimension)

    def index_document(self, document_id: int) -> dict:
        document = self.db.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_text(document.extracted_text)
        vectors = self.embeddings.embed_documents(chunks)
        count = self.vector_store.upsert_document_chunks(document_id, chunks, vectors)
        return {"document_id": document_id, "indexed_chunks": count}

    def remove_document(self, document_id: int) -> None:
        self.vector_store.remove_document(document_id)

    def search(self, query: str, limit: int) -> list[VectorHit]:
        query_embedding = self.embeddings.embed_query(query)
        candidates = self.vector_store.search(query_embedding, limit=20)
        reranked = self._rerank(query_embedding, candidates)
        return reranked[:limit]

    def context(self, document_id: int) -> list[VectorHit]:
        return self.vector_store.context(document_id)

    @staticmethod
    def _rerank(query_embedding: list[float], candidates: list[VectorHit]) -> list[VectorHit]:
        reranked = []
        local_embedder = get_embedding_service()
        candidate_embeddings = local_embedder.embed_documents([candidate.content for candidate in candidates])
        for candidate, embedding in zip(candidates, candidate_embeddings):
            rerank_score = cosine_similarity(query_embedding, embedding)
            reranked.append(
                VectorHit(
                    document_id=candidate.document_id,
                    chunk_id=candidate.chunk_id,
                    chunk_index=candidate.chunk_index,
                    content=candidate.content,
                    score=(candidate.score * 0.6) + (rerank_score * 0.4),
                )
            )
        return sorted(reranked, key=lambda hit: hit.score, reverse=True)

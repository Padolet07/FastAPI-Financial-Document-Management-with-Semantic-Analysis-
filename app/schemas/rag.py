from pydantic import BaseModel, Field


class IndexDocumentRequest(BaseModel):
    document_id: int


class RAGSearchRequest(BaseModel):
    query: str = Field(min_length=2)
    limit: int = Field(default=5, ge=1, le=20)


class ChunkResult(BaseModel):
    document_id: int
    chunk_id: int | None = None
    chunk_index: int
    content: str
    score: float


class RAGSearchResponse(BaseModel):
    query: str
    results: list[ChunkResult]


class DocumentContextResponse(BaseModel):
    document_id: int
    chunks: list[ChunkResult]

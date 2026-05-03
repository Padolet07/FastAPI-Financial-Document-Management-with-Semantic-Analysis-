from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import RAG_INDEX, RAG_SEARCH
from app.db.session import get_db
from app.models.user import User
from app.rag.service import RAGService
from app.schemas.rag import ChunkResult, DocumentContextResponse, IndexDocumentRequest, RAGSearchRequest, RAGSearchResponse

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/index-document")
def index_document(
    payload: IndexDocumentRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(RAG_INDEX)),
):
    return RAGService(db).index_document(payload.document_id)


@router.delete("/remove-document/{document_id}", status_code=204)
def remove_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(RAG_INDEX)),
):
    RAGService(db).remove_document(document_id)
    return None


@router.post("/search", response_model=RAGSearchResponse)
def semantic_search(
    payload: RAGSearchRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(RAG_SEARCH)),
):
    results = [
        ChunkResult(**hit.__dict__)
        for hit in RAGService(db).search(query=payload.query, limit=payload.limit)
    ]
    return RAGSearchResponse(query=payload.query, results=results)


@router.get("/context/{document_id}", response_model=DocumentContextResponse)
def document_context(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(RAG_SEARCH)),
):
    chunks = [ChunkResult(**hit.__dict__) for hit in RAGService(db).context(document_id)]
    return DocumentContextResponse(document_id=document_id, chunks=chunks)

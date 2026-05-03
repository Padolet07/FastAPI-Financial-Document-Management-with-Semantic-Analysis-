from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import DOCUMENT_DELETE, DOCUMENT_EDIT, DOCUMENT_UPLOAD, DOCUMENT_VIEW
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import DocumentDetail, DocumentList, DocumentRead, DocumentType, DocumentUpdate
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentRead, status_code=201)
def upload_document(
    title: str = Form(...),
    company_name: str = Form(...),
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(DOCUMENT_UPLOAD)),
):
    return DocumentService(db).upload(file, title, company_name, document_type, current_user)


@router.get("", response_model=DocumentList)
def list_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(DOCUMENT_VIEW)),
):
    items, total = DocumentService(db).list(limit=limit, offset=offset)
    return DocumentList(items=items, total=total, limit=limit, offset=offset)


@router.get("/search", response_model=DocumentList)
def search_documents(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(DOCUMENT_VIEW)),
):
    items, total = DocumentService(db).search(query=query, limit=limit, offset=offset)
    return DocumentList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(DOCUMENT_VIEW)),
):
    return DocumentService(db).get(document_id)


@router.put("/{document_id}", response_model=DocumentRead)
def update_document(
    document_id: int,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(DOCUMENT_EDIT)),
):
    return DocumentService(db).update_metadata(
        document_id=document_id,
        title=payload.title,
        company_name=payload.company_name,
        document_type=payload.document_type,
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(DOCUMENT_DELETE)),
):
    DocumentService(db).delete(document_id)
    return None

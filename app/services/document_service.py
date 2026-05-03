import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core import get_settings
from app.models.document import Document
from app.models.user import User


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def upload(
        self,
        file: UploadFile,
        title: str,
        company_name: str,
        document_type: str,
        current_user: User,
    ) -> Document:
        file_path = self._save_upload(file)
        text = self._extract_text(file_path)
        if not text.strip():
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No text could be extracted")
        document = Document(
            title=title,
            company_name=company_name,
            document_type=document_type,
            uploaded_by=current_user.id,
            file_path=str(file_path),
            extracted_text=text,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def list(self, limit: int, offset: int) -> tuple[list[Document], int]:
        query = self.db.query(Document).order_by(Document.created_at.desc())
        return query.limit(limit).offset(offset).all(), query.count()

    def get(self, document_id: int) -> Document:
        document = self.db.get(Document, document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return document

    def update_metadata(
        self,
        document_id: int,
        title: str | None,
        company_name: str | None,
        document_type: str | None,
    ) -> Document:
        document = self.get(document_id)
        if title is not None:
            document.title = title
        if company_name is not None:
            document.company_name = company_name
        if document_type is not None:
            document.document_type = document_type
        self.db.commit()
        self.db.refresh(document)
        return document

    def delete(self, document_id: int) -> None:
        document = self.get(document_id)
        path = Path(document.file_path)
        self.db.delete(document)
        self.db.commit()
        if path.exists():
            path.unlink(missing_ok=True)

    def search(self, query: str, limit: int, offset: int) -> tuple[list[Document], int]:
        pattern = f"%{query}%"
        stmt = self.db.query(Document).filter(
            or_(
                Document.title.ilike(pattern),
                Document.company_name.ilike(pattern),
                Document.document_type.ilike(pattern),
            )
        )
        return stmt.limit(limit).offset(offset).all(), stmt.count()

    def _save_upload(self, file: UploadFile) -> Path:
        suffix = Path(file.filename or "document").suffix.lower()
        if suffix not in {".pdf", ".txt", ".md"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF, TXT, and MD files are supported")
        destination = self.settings.upload_dir / f"{uuid4().hex}{suffix}"
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return destination

    @staticmethod
    def _extract_text(path: Path) -> str:
        if path.suffix.lower() == ".pdf":
            reader = PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        return path.read_text(encoding="utf-8", errors="ignore")

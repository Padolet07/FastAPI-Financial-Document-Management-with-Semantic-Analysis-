from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DocumentType = Literal["invoice", "report", "contract"]


class DocumentRead(BaseModel):
    id: int
    title: str
    company_name: str
    document_type: str
    uploaded_by: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentRead):
    extracted_text: str


class DocumentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    document_type: DocumentType | None = None


class DocumentList(BaseModel):
    items: list[DocumentRead]
    total: int
    limit: int
    offset: int


class DocumentSearchParams(BaseModel):
    query: str = Field(min_length=1)

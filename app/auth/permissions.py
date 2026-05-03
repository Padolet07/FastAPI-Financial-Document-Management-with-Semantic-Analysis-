DOCUMENT_VIEW = "documents:view"
DOCUMENT_UPLOAD = "documents:upload"
DOCUMENT_EDIT = "documents:edit"
DOCUMENT_DELETE = "documents:delete"
RAG_INDEX = "rag:index"
RAG_SEARCH = "rag:search"
ROLE_MANAGE = "roles:manage"
USER_MANAGE = "users:manage"

ALL_PERMISSIONS = [
    DOCUMENT_VIEW,
    DOCUMENT_UPLOAD,
    DOCUMENT_EDIT,
    DOCUMENT_DELETE,
    RAG_INDEX,
    RAG_SEARCH,
    ROLE_MANAGE,
    USER_MANAGE,
]

DEFAULT_ROLE_PERMISSIONS = {
    "Admin": ALL_PERMISSIONS,
    "Analyst": [DOCUMENT_VIEW, DOCUMENT_UPLOAD, DOCUMENT_EDIT, RAG_INDEX, RAG_SEARCH],
    "Auditor": [DOCUMENT_VIEW, RAG_SEARCH],
    "Client": [DOCUMENT_VIEW],
}

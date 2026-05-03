import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core import get_settings
from app.db.session import Base, SessionLocal, engine
from app.routes import auth, documents, rag, rbac
from app.services.rbac_service import RBACService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        RBACService(db).seed_defaults()
        logger.info("Database initialized")
    finally:
        db.close()
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Financial document management APIs with JWT auth, RBAC, and semantic search.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(rbac.router)
app.include_router(rag.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "environment": settings.environment}

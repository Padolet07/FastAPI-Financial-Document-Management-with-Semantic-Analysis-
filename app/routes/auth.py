from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import TokenResponse, UserLogin, UserRead, UserRegister
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    return UserService(db).register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    token = UserService(db).login(payload)
    return TokenResponse(access_token=token)

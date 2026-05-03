from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserLogin, UserRegister


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, payload: UserRegister) -> User:
        existing = self.db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        user = User(
            email=payload.email.lower(),
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, payload: UserLogin) -> str:
        user = self.db.query(User).filter(User.email == payload.email.lower()).first()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
        return create_access_token(str(user.id))

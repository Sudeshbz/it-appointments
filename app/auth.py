from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from . import models, schemas

# Şifreleme metodu (bcrypt yerine pbkdf2_sha256)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# -----------------------------
#  ŞİFRELEME FONKSİYONLARI
# -----------------------------
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# -----------------------------
#  JWT TOKEN OLUŞTURMA
# -----------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    # 🔥 sub (user_id) daima string olmalı
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# -----------------------------
#  KULLANICI DOĞRULAMA
# -----------------------------
def authenticate_user(db: Session, email: str, password: str) -> Optional[models.Employee]:
    user = db.query(models.Employee).filter(models.Employee.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# -----------------------------
#  TOKEN ÇÖZME & DOĞRULAMA
# -----------------------------
def decode_token(token: str) -> Optional[schemas.TokenData]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        user_id = payload.get("sub")
        company_id = payload.get("company_id")
        role = payload.get("role")

        if user_id is None:
            return None

        # 🔥 sub string geldiği için integer'a dönüştürüyoruz
        user_id = int(user_id)

        return schemas.TokenData(
            user_id=user_id,
            company_id=company_id,
            role=role
        )

    except JWTError:
        return None

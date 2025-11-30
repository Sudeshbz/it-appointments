from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from . import models, auth as auth_utils

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.Employee:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = auth_utils.decode_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    user = db.query(models.Employee).filter(models.Employee.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_company(user: models.Employee = Depends(get_current_user)) -> int:
    return user.company_id


def require_admin(user: models.Employee = Depends(get_current_user)) -> models.Employee:
    if user.role != models.RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Yalnızca admin erişebilir.")
    return user

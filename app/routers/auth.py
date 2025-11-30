from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import schemas, models, auth as auth_utils
from ..database import get_db
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.EmployeeOut)
def register(user_in: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    # Aynı email var mı?
    existing = db.query(models.Employee).filter(models.Employee.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı.")

    if not user_in.company_name:
        raise HTTPException(status_code=400, detail="Şirket bilgisi (company_name) gerekiyor.")

    # Şirketi bul ya da oluştur
    company = db.query(models.Company).filter(models.Company.name == user_in.company_name).first()
    if not company:
        company = models.Company(name=user_in.company_name)
        db.add(company)
        db.commit()
        db.refresh(company)

    hashed_pw = auth_utils.get_password_hash(user_in.password)

    db_user = models.Employee(
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=hashed_pw,
        role=user_in.role,
        department=user_in.department,
        company_id=company.id,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth_utils.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="E-posta veya şifre hatalı.")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={"sub": user.id, "company_id": user.company_id, "role": user.role.value},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}

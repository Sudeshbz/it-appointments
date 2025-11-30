from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(
    prefix="/services",
    tags=["services"],
)


# -------------------------------------------------
# 1) HİZMET OLUŞTUR (BUNU ZATEN KULLANIYORDUK)
# -------------------------------------------------
@router.post("/", response_model=schemas.ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(
    service_in: schemas.ServiceCreate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    # Sadece o şirketin içinde hizmet oluştur
    service = models.Service(
        name=service_in.name,
        description=service_in.description,
        company_id=current_user.company_id,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


# -------------------------------------------------
# 2) HİZMETLERİ LİSTELE
# -------------------------------------------------
@router.get("/", response_model=List[schemas.ServiceOut])
def list_services(
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Giriş yapan kullanıcının şirketine ait TÜM hizmetleri döner.
    """
    services = (
        db.query(models.Service)
        .filter(models.Service.company_id == current_user.company_id)
        .all()
    )
    return services


# -------------------------------------------------
# 3) TEK BİR HİZMETİ GETİR
# -------------------------------------------------
@router.get("/{service_id}", response_model=schemas.ServiceOut)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    """
    Parametre olarak verilen ID'li hizmeti döner.
    Sadece kullanıcının kendi şirketine aitse erişebilir.
    """
    service = (
        db.query(models.Service)
        .filter(
            models.Service.id == service_id,
            models.Service.company_id == current_user.company_id,
        )
        .first()
    )
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hizmet bulunamadı.",
        )
    return service


# -------------------------------------------------
# 4) HİZMET GÜNCELLE (PUT)
# -------------------------------------------------
@router.put("/{service_id}", response_model=schemas.ServiceOut)
def update_service(
    service_id: int,
    service_in: schemas.ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    service = (
        db.query(models.Service)
        .filter(
            models.Service.id == service_id,
            models.Service.company_id == current_user.company_id,
        )
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hizmet bulunamadı.",
        )

    # Sadece gelen alanları güncelle
    if service_in.name is not None:
        service.name = service_in.name
    if service_in.description is not None:
        service.description = service_in.description

    db.commit()
    db.refresh(service)
    return service


# -------------------------------------------------
# 5) HİZMET SİL (DELETE)
# -------------------------------------------------
@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: models.Employee = Depends(get_current_user),
):
    service = (
        db.query(models.Service)
        .filter(
            models.Service.id == service_id,
            models.Service.company_id == current_user.company_id,
        )
        .first()
    )

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hizmet bulunamadı.",
        )

    db.delete(service)
    db.commit()
    return None
